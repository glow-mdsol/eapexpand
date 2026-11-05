from pathlib import Path
from typing import Any

import yaml

SCALAR_TYPES = {"string", "integer", "number"}


def _base_schema_name(schema_name: str) -> str:
    if schema_name.endswith("-Input"):
        return schema_name[: -len("-Input")]
    if schema_name.endswith("-Output"):
        return schema_name[: -len("-Output")]
    return schema_name


def _ref_name(ref: str | None) -> str | None:
    if not ref:
        return None
    return ref.split("/")[-1]


def _unwrap_nullable(prop_schema: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """
    Collapse an OpenAPI 3.1 optional property (``anyOf: [X, {type: null}]``)
    to ``X``; returns the schema and whether it was nullable.
    """
    any_of = prop_schema.get("anyOf")
    if not isinstance(any_of, list):
        return prop_schema, False
    non_null = [s for s in any_of if isinstance(s, dict) and s.get("type") != "null"]
    if len(non_null) != 1:
        return prop_schema, False
    return {**non_null[0], **{k: v for k, v in prop_schema.items() if k != "anyOf"}}, True


def extract_openapi_api_metadata(openapi_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Distil the parts of an OpenAPI spec the UML loader needs:

    - ``idPropertiesByClass``: scalar ``*Id``/``*Ids`` properties (API reference attributes)
    - ``aliasCodePropsByClass``: properties typed as AliasCode
    - ``refPropsByClass``: properties referencing another schema, with target class and
      multiplicity (used to add API-only containment relationships)
    """
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    id_props_by_class: dict[str, set[str]] = {}
    alias_code_props_by_class: dict[str, dict[str, str]] = {}
    ref_props_by_class: dict[str, dict[str, dict[str, Any]]] = {}

    for schema_name, schema in schemas.items():
        class_name = _base_schema_name(schema_name)
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            continue

        for prop_name, raw_prop_schema in properties.items():
            if not isinstance(raw_prop_schema, dict):
                continue
            prop_schema, nullable = _unwrap_nullable(raw_prop_schema)
            raw_items = prop_schema.get("items")
            items: dict[str, Any] = raw_items if isinstance(raw_items, dict) else {}
            prop_type = prop_schema.get("type")

            if prop_name.endswith("Id") or prop_name.endswith("Ids"):
                is_scalar = prop_type in SCALAR_TYPES
                is_scalar_array = prop_type == "array" and items.get("type") in SCALAR_TYPES
                if is_scalar or is_scalar_array:
                    id_props_by_class.setdefault(class_name, set()).add(prop_name)

            prop_ref = _ref_name(prop_schema.get("$ref"))
            items_ref = _ref_name(items.get("$ref"))
            ref_name = items_ref or prop_ref
            if ref_name:
                ref_base = _base_schema_name(ref_name)
                if ref_base == "AliasCode":
                    alias_code_props_by_class.setdefault(class_name, {})[prop_name] = "AliasCode"
                ref_props_by_class.setdefault(class_name, {})[prop_name] = {
                    "type": ref_base,
                    "multivalued": items_ref is not None,
                    "optional": nullable or items_ref is not None,
                }

    return {
        "openapi": {
            "idPropertiesByClass": {
                class_name: sorted(props)
                for class_name, props in id_props_by_class.items()
            },
            "aliasCodePropsByClass": alias_code_props_by_class,
            "refPropsByClass": ref_props_by_class,
        }
    }


def load_openapi_api_metadata(openapi_path: str | Path) -> dict[str, Any]:
    """Load an OpenAPI spec (YAML or JSON) and extract the API metadata."""
    path = Path(openapi_path)
    with path.open("r") as fh:
        openapi_spec = yaml.safe_load(fh)
    return extract_openapi_api_metadata(openapi_spec)
