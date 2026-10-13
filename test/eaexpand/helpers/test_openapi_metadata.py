from eapexpand.helpers.openapi_metadata import extract_openapi_api_metadata


def test_extract_openapi_api_metadata_collects_id_properties_and_alias_code_refs():
    spec = {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "Widget-Input": {
                    "type": "object",
                    "properties": {
                        "memberIds": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "ownerId": {"type": "string"},
                        "ignoredIds": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Other-Input"},
                        },
                        "blindingSchema": {
                            "$ref": "#/components/schemas/AliasCode-Input"
                        },
                    },
                },
                "Widget-Output": {
                    "type": "object",
                    "properties": {
                        "memberIds": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "status": {"type": "string"},
                    },
                },
            }
        },
    }

    metadata = extract_openapi_api_metadata(spec)
    openapi = metadata["openapi"]

    assert set(openapi["idPropertiesByClass"]["Widget"]) == {"memberIds", "ownerId"}
    assert openapi["aliasCodePropsByClass"]["Widget"]["blindingSchema"] == "AliasCode"
