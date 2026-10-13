import json
from pathlib import Path
from typing import Any


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


def extract_openapi_api_metadata(openapi_spec: dict[str, Any]) -> dict[str, Any]:
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    id_props_by_class: dict[str, set[str]] = {}
    alias_code_props_by_class: dict[str, dict[str, str]] = {}

    for schema_name, schema in schemas.items():
        class_name = _base_schema_name(schema_name)
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            continue

        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue

            if prop_name.endswith("Id") or prop_name.endswith("Ids"):
                prop_type = prop_schema.get("type")
                item_type = prop_schema.get("items", {}).get("type") if isinstance(prop_schema.get("items"), dict) else None
                is_scalar = prop_type in {"string", "integer", "number"}
                is_scalar_array = prop_type == "array" and item_type in {"string", "integer", "number"}
                if is_scalar or is_scalar_array:
                    id_props_by_class.setdefault(class_name, set()).add(prop_name)

            prop_ref = _ref_name(prop_schema.get("$ref"))
            items_ref = _ref_name(prop_schema.get("items", {}).get("$ref")) if isinstance(prop_schema.get("items"), dict) else None
            ref_name = items_ref or prop_ref
            if ref_name:
                ref_base = _base_schema_name(ref_name)
                if ref_base == "AliasCode":
                    alias_code_props_by_class.setdefault(class_name, {})[prop_name] = "AliasCode"

    return {
        "openapi": {
            "idPropertiesByClass": {
                class_name: sorted(props)
                for class_name, props in id_props_by_class.items()
            },
            "aliasCodePropsByClass": alias_code_props_by_class,
        }
    }


def load_openapi_api_metadata(openapi_path: str | Path) -> dict[str, Any]:
    path = Path(openapi_path)
    with path.open("r") as fh:
        openapi_spec = json.load(fh)
    return extract_openapi_api_metadata(openapi_spec)
