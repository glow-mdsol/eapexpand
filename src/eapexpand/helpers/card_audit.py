"""
Audit the cardinality of generated USDM artefacts against the UML model.

For every class attribute and association in the UML (QEA) file, the UML
multiplicity is compared with:

- the generated LinkML schema: ``required``, ``multivalued``,
  ``minimum_cardinality`` and ``maximum_cardinality``
- the generated workbook (``USDM`` sheet): the Cardinality column
- the OpenAPI specification: required/nullable, array, ``minItems``/``maxItems``

Associations sharing a name (union relationships, e.g. ``Condition.appliesTo``)
are compared using their widest combined multiplicity, as the generators merge
them into a single slot.

Mismatches between the UML and the LinkML or workbook are errors. Differences
from the OpenAPI specification, and classes the workbook omits (no CT entry),
are reported as warnings.

Exit codes: 0 no errors, 1 errors found, 2 inputs missing.
"""

import argparse
import contextlib
import io
import logging
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Optional

import openpyxl
import yaml

from ..models.eap import ModelObject
from ..models.sqlite_loader import load_from_file
from ..render.render_linkml import _to_snake_case
from .openapi_metadata import extract_openapi_api_metadata

DEFAULT_OPENAPI_SPEC = Path(__file__).resolve().parents[3] / "docs" / "ddf_ra" / "USDM_API.yaml"

Bounds = tuple[int, Optional[int]]  # (lower, upper); upper None == unbounded


def _parse(cardinality: Optional[str]) -> Optional[Bounds]:
    text = (cardinality or "").strip()
    if not text:
        return None
    lower_raw, _, upper_raw = text.partition("..")
    if not upper_raw:
        upper_raw = "*" if lower_raw == "*" else lower_raw
        lower_raw = "0" if lower_raw == "*" else lower_raw
    if not lower_raw.isdigit() or not (upper_raw == "*" or upper_raw.isdigit()):
        return None
    return int(lower_raw), None if upper_raw == "*" else int(upper_raw)


def _widen(a: Bounds, b: Bounds) -> Bounds:
    upper = None if a[1] is None or b[1] is None else max(a[1], b[1])
    return min(a[0], b[0]), upper


def _fmt(bounds: Bounds) -> str:
    return f"{bounds[0]}..{'*' if bounds[1] is None else bounds[1]}"


class Findings:
    def __init__(self) -> None:
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.warnings: dict[str, list[str]] = defaultdict(list)

    def error(self, category: str, message: str) -> None:
        self.errors[category].append(message)

    def warn(self, category: str, message: str) -> None:
        self.warnings[category].append(message)

    def report(self) -> None:
        for label, groups in (("ERROR", self.errors), ("WARNING", self.warnings)):
            for category, messages in groups.items():
                print(f"\n{label}: {category} ({len(messages)})")
                for message in sorted(messages):
                    print(f"  {message}")
        print(
            f"\n{sum(map(len, self.errors.values()))} error(s), "
            f"{sum(map(len, self.warnings.values()))} warning(s)"
        )


def _uml_items(obj: ModelObject) -> list[tuple[str, str, Bounds, str]]:
    """(exchange name, UML name, bounds, raw multiplicity) for each attribute/association."""
    items = []
    for attr in obj.object_attributes or []:
        raw = f"{attr.lower_bound}..{attr.upper_bound}"
        items.append((attr.name, attr.name, _parse(raw), raw))
    merged: dict[str, list] = {}
    for conn in obj.outgoing_connections or []:
        if conn.connector_type != "Association":
            continue
        bounds = _parse(conn.dest_card)
        exchange = conn.api_name if conn.is_reference else conn.name
        if conn.name in merged and bounds and merged[conn.name][2]:
            merged[conn.name][2] = _widen(merged[conn.name][2], bounds)
            merged[conn.name][3] += f", {conn.dest_card}"
        else:
            merged[conn.name] = [exchange, conn.name, bounds, conn.dest_card]
    return items + [tuple(v) for v in merged.values()]


def _check_linkml(findings: Findings, key: str, bounds: Bounds, slot: Optional[dict]) -> None:
    if slot is None:
        findings.error("missing from LinkML", key)
        return
    lower, upper = bounds
    multivalued = upper is None or upper > 1
    if bool(slot.get("required")) != (lower > 0):
        findings.error("LinkML required != UML", f"{key}: UML {_fmt(bounds)}, required={slot.get('required')}")
    if bool(slot.get("multivalued")) != multivalued:
        findings.error("LinkML multivalued != UML", f"{key}: UML {_fmt(bounds)}, multivalued={slot.get('multivalued')}")
    if multivalued:
        if slot.get("minimum_cardinality") != (lower or None):
            findings.error(
                "LinkML minimum_cardinality != UML",
                f"{key}: UML {_fmt(bounds)}, minimum_cardinality={slot.get('minimum_cardinality')}",
            )
        if slot.get("maximum_cardinality") != upper:
            findings.error(
                "LinkML maximum_cardinality != UML",
                f"{key}: UML {_fmt(bounds)}, maximum_cardinality={slot.get('maximum_cardinality')}",
            )


def _check_openapi(findings: Findings, key: str, bounds: Bounds, schema: dict, name: str) -> None:
    prop = schema.get("properties", {}).get(name)
    if prop is None:
        return
    lower, upper = bounds
    multivalued = upper is None or upper > 1
    branches = prop.get("anyOf", [])
    nullable = any(isinstance(b, dict) and b.get("type") == "null" for b in branches)
    base = next((b for b in branches if isinstance(b, dict) and b.get("type") != "null"), prop)
    is_array = base.get("type") == "array"
    required = name in schema.get("required", [])
    if is_array != multivalued:
        findings.warn("OpenAPI array != UML multivalued", f"{key}: UML {_fmt(bounds)}, array={is_array}")
    elif not is_array and required != (lower > 0):
        findings.warn(
            "OpenAPI required != UML",
            f"{key}: UML {_fmt(bounds)}, required={required}, nullable={nullable}",
        )
    elif is_array:
        if lower > 0 and (base.get("minItems") or 0) < lower:
            findings.warn("OpenAPI minItems missing for UML lower bound", f"{key}: UML {_fmt(bounds)}")
        if upper is not None and base.get("maxItems") != upper:
            findings.warn("OpenAPI maxItems != UML", f"{key}: UML {_fmt(bounds)}, maxItems={base.get('maxItems')}")


def audit(qea: Path, schema_file: Path, workbook_file: Path, openapi_spec: Path) -> Findings:
    with openapi_spec.open() as fh:
        spec = yaml.safe_load(fh)
    api_metadata = extract_openapi_api_metadata(spec)
    schemas = spec.get("components", {}).get("schemas", {})
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        document = load_from_file(str(qea), api_metadata=api_metadata)
    with schema_file.open() as fh:
        classes = yaml.safe_load(fh).get("classes", {})
    rows = list(openpyxl.load_workbook(workbook_file)["USDM"].iter_rows(values_only=True))[1:]
    workbook = {(str(r[0]), str(r[1])): str(r[3]) for r in rows if r[1]}
    workbook_classes = {str(r[0]) for r in rows if r[1]}

    findings = Findings()
    for obj in document.objects:
        if obj.object_type != "Class":
            continue
        slots = (classes.get(obj.name) or {}).get("attributes") or {}
        schema = schemas.get(f"{obj.name}-Input") or schemas.get(obj.name) or {}
        for exchange, uml_name, bounds, raw in _uml_items(obj):
            if uml_name == "id":
                continue
            key = f"{obj.name}.{exchange}" + (f" (UML {uml_name})" if exchange != uml_name else "")
            if bounds is None:
                findings.error("unparseable UML multiplicity", f"{key}: {raw!r}")
                continue
            slot_name = _to_snake_case(f"{obj.name}Name" if exchange == "name" else exchange)
            _check_linkml(findings, key, bounds, slots.get(slot_name))
            if obj.name not in workbook_classes:
                findings.warn("class not in workbook (no CT entry)", str(obj.name))
            elif (obj.name, exchange) not in workbook:
                findings.error("missing from workbook", key)
            elif _parse(workbook[(obj.name, exchange)]) != bounds:
                findings.error(
                    "workbook cardinality != UML",
                    f"{key}: UML {_fmt(bounds)}, workbook {workbook[(obj.name, exchange)]}",
                )
            _check_openapi(findings, key, bounds, schema, exchange)
    # one warning per omitted class
    for category in list(findings.warnings):
        findings.warnings[category] = sorted(set(findings.warnings[category]))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that generated USDM LinkML/workbook cardinalities match the UML model.",
        epilog="Exit codes: 0 no errors, 1 errors found, 2 inputs missing.",
    )
    parser.add_argument("output_dir", type=Path, help="Generation output directory (as passed to load_usdm --output)")
    parser.add_argument(
        "--qea", type=Path, default=Path("input/v4.0.0/v4.0.0_USDM_UML.qea"),
        help="UML model (QEA) the output was generated from (default: %(default)s)",
    )
    parser.add_argument(
        "--name",
        help="Base name of the generated files (default: USDM_<version> from the QEA name, e.g. USDM_v4.0.0)",
    )
    parser.add_argument(
        "--openapi-spec", type=Path, default=DEFAULT_OPENAPI_SPEC,
        help="OpenAPI specification (default: %(default)s)",
    )
    opts = parser.parse_args()
    logging.disable(logging.CRITICAL)

    name = opts.name or "USDM_" + opts.qea.stem.removesuffix("_USDM_UML")
    inputs = {
        "QEA": opts.qea,
        "LinkML schema": opts.output_dir / f"{name}.yaml",
        "workbook": opts.output_dir / f"{name}.xlsx",
        "OpenAPI specification": opts.openapi_spec,
    }
    missing = [f"{label} not found: {path}" for label, path in inputs.items() if not path.is_file()]
    if missing:
        print("\n".join(missing), file=sys.stderr)
        sys.exit(2)

    findings = audit(opts.qea, inputs["LinkML schema"], inputs["workbook"], opts.openapi_spec)
    findings.report()
    sys.exit(1 if findings.errors else 0)


if __name__ == "__main__":
    main()
