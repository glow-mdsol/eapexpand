"""
Check USDM exchange (API JSON) files against the API schema and the model.

For each file:

- validate against the OpenAPI ``Wrapper-Input`` schema
- check every reference attribute (``*Id``/``*Ids``, i.e. LinkML slots carrying a
  ``uml_role`` annotation): the value is a string (or a list of strings when the
  slot is multivalued), names an object in the same file, and that object's
  ``instanceType`` is the slot's range or one of its subclasses
- report ids used by more than one object

Exit codes: 0 no problems, 1 problems found, 2 inputs missing.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = REPO_ROOT / "docs" / "releases" / "USDM_v4.0.0.yaml"
DEFAULT_OPENAPI_SPEC = REPO_ROOT / "docs" / "ddf_ra" / "USDM_API.yaml"
ROOT_SCHEMA = "Wrapper-Input"


class ReferenceModel:
    """Reference slots per class (inherited included), from the generated LinkML schema."""

    def __init__(self, linkml_schema: dict[str, Any]) -> None:
        classes = linkml_schema.get("classes", {})
        self.parents = {name: cls.get("is_a") for name, cls in classes.items()}
        # class -> API name -> (allowed ranges, multivalued)
        self.references: dict[str, dict[str, tuple[set[str], bool]]] = defaultdict(dict)
        for name in classes:
            for owner in self.lineage(name):
                for slot in (classes[owner].get("attributes") or {}).values():
                    annotations = slot.get("annotations") or {}
                    if "uml_role" not in annotations:
                        continue
                    api_name = annotations["source_attribute_name"]["value"]
                    ranges = {slot["range"]} if slot.get("range") else {o["range"] for o in slot.get("any_of", [])}
                    self.references[name].setdefault(api_name, (ranges, bool(slot.get("multivalued"))))

    def lineage(self, name: str | None) -> Iterator[str]:
        while name:
            yield name
            name = self.parents.get(name)


def _objects(node: Any) -> Iterator[dict[str, Any]]:
    """Every USDM object (has id and instanceType) in the document."""
    if isinstance(node, dict):
        if "id" in node and "instanceType" in node:
            yield node
        for value in node.values():
            yield from _objects(value)
    elif isinstance(node, list):
        for value in node:
            yield from _objects(value)


def _most_specific(error: ValidationError) -> ValidationError:
    """
    For anyOf/oneOf failures, descend into the branch that got furthest: the
    deepest error is in the branch matching the object's type, not a mismatch
    on its discriminator.
    """
    while error.context:
        error = max(error.context, key=lambda e: len(e.absolute_path))
    return error


def check_file(path: Path, validator: Draft202012Validator, model: ReferenceModel) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = defaultdict(list)
    try:
        document = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        problems["invalid JSON"].append(str(exc))
        return problems

    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        error = _most_specific(error)
        location = "/".join(map(str, error.absolute_path)) or "/"
        problems["API schema"].append(f"{location}: {error.message[:200]}")

    objects = list(_objects(document))
    types_by_id: dict[str, list[str]] = defaultdict(list)
    for obj in objects:
        types_by_id[obj["id"]].append(obj["instanceType"])
    for identifier, types in types_by_id.items():
        if len(types) > 1:
            problems["duplicate id"].append(f"{identifier} used by {types}")

    for obj in objects:
        owner = f"{obj['instanceType']} {obj['id']}"
        for api_name, (ranges, multivalued) in model.references.get(obj["instanceType"], {}).items():
            value = obj.get(api_name)
            if value is None:
                continue
            if isinstance(value, list) != multivalued:
                expected = "a list" if multivalued else "a single value"
                problems["wrong shape"].append(f"{owner}.{api_name}: expected {expected}, got {value!r}")
            for target in value if isinstance(value, list) else [value]:
                if not isinstance(target, str):
                    problems["not a string"].append(f"{owner}.{api_name}: {target!r}")
                elif target not in types_by_id:
                    problems["dangling reference"].append(f"{owner}.{api_name}: {target}")
                elif not any(set(model.lineage(t)) & ranges for t in types_by_id[target]):
                    problems["wrong target type"].append(
                        f"{owner}.{api_name}: {target} is {types_by_id[target]}, expected {sorted(ranges)}"
                    )
    problems["_summary"] = [f"{len(objects)} objects"]
    return problems


def _files(paths: list[Path]) -> list[Path]:
    found = []
    for path in paths:
        found.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check USDM JSON files against the API schema and the model's reference ranges.",
        epilog="Exit codes: 0 no problems, 1 problems found, 2 inputs missing.",
    )
    parser.add_argument(
        "paths", nargs="*", type=Path, default=[REPO_ROOT / "examples"],
        help="USDM JSON files or directories of them (default: examples/)",
    )
    parser.add_argument(
        "--schema", type=Path, default=DEFAULT_SCHEMA,
        help="Generated LinkML schema providing the reference ranges (default: %(default)s)",
    )
    parser.add_argument(
        "--openapi-spec", type=Path, default=DEFAULT_OPENAPI_SPEC,
        help="OpenAPI specification (default: %(default)s)",
    )
    parser.add_argument("--limit", type=int, default=5, help="Problems listed per category (default: %(default)s)")
    opts = parser.parse_args()

    files = _files(opts.paths)
    missing = [p for p in [opts.schema, opts.openapi_spec, *files] if not p.is_file()]
    if missing or not files:
        for path in missing:
            print(f"not found: {path}", file=sys.stderr)
        if not files:
            print("no USDM JSON files to check", file=sys.stderr)
        sys.exit(2)

    with opts.openapi_spec.open() as fh:
        spec = yaml.safe_load(fh)
    validator = Draft202012Validator(
        {"$ref": f"#/components/schemas/{ROOT_SCHEMA}", "components": spec.get("components", {})}
    )
    with opts.schema.open() as fh:
        model = ReferenceModel(yaml.safe_load(fh))

    failed = 0
    for path in files:
        problems = check_file(path, validator, model)
        summary = problems.pop("_summary", [""])[0]
        total = sum(map(len, problems.values()))
        print(f"{path.name}: {'OK' if not total else f'{total} problem(s)'} ({summary})")
        for category, messages in problems.items():
            print(f"  {category} ({len(messages)})")
            for message in messages[: opts.limit]:
                print(f"    {message}")
            if len(messages) > opts.limit:
                print(f"    ... {len(messages) - opts.limit} more")
        failed += bool(total)
    print(f"\n{len(files) - failed}/{len(files)} file(s) OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
