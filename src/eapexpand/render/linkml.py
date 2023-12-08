from typing import Optional

import yaml

from ..models.eap import Object, Attribute, Connector, Package, Document

IDENTIFIER_TYPES = ["id", "uuid"]

TYPE_MAPPING = {
    "String": "string",
    "Integer": "integer",
    "Boolean": "boolean",
    "Float": "float",
}


def generate(
    name: str,
    document: Document,
    prefix: Optional[str] = "",
    output_dir: Optional[str] = "output",
):
    """
    Create a LinkML representation from the EAP model
    """

    if not prefix:
        prefix = f"https://example.org/{name}"
    model = {
        "id": name,
        "name": name,
        "prefixes": {
            "linkml": dict(prefix_reference="https://w3id.org/linkml/"),
            name: dict(prefix_reference=prefix),
        },
        "imports": ["linkml:types"],
        "default_range": "string",
        "default_prefix": name,
        "default_curi_maps": ["semweb_context"],
        "classes": {},
        "slots": {},
        "types": {},
        "enums": {},
    }
    _types = {}
    _slots = {}
    # create a back reference for the slots to the classes
    for obj in document.objects:  # type: Object
        # we should probably use the class attribute of the document here
        if obj.object_type == "Class":
            _attributes = sorted(obj.attributes)
            for attr in _attributes:  # type: Attribute
                # _slot = _slots.setdefault(attr.name, {"refs": []})
                _slot = _slots.setdefault(attr.name, {})
                if attr.name in IDENTIFIER_TYPES:
                    _slot["identifier"] = True
                if attr.attribute_type:
                    # Multi-valued attributes are represented as lists
                    if "List" in attr.attribute_type:
                        _slot["multivalued"] = True
                        _slot["range"] = attr.attribute_type.split("<")[1].split(">")[0]
                    else:
                        _slot["range"] = TYPE_MAPPING.get(
                            attr.attribute_type, attr.attribute_type
                        )
                    # _slot["refs"].append(obj.name)
                    _types.setdefault(attr.attribute_type, []).append(obj)
                if attr.description:
                    _slot["description"] = attr.description
                # if attr.cardinality:
                #     print("Cardinality:", attr.cardinality)

    # create a back reference for the types to the classes
    for obj in document.objects:  # type: Object
        if obj.object_type == "Class":
            _class = {"slots": []}
            _object_id = obj.object_id
            _attributes = sorted(obj.attributes)
            for attr in _attributes:  # type: Attribute
                if "List" in attr.attribute_type:
                    attr.attribute_type = attr.attribute_type.replace("List", "list")
                    range_name = attr.attribute_type.split("<")[1].split(">")[0]

                # model.setdefault("slots", {}).setdefault(
                #     attr.name,
                #     {
                #         "name": attr.name,
                #         "type": attr.attribute_type,
                #         "cardinality": attr.cardinality,
                #         "description": attr.notes,
                #     },
                # )
                # _class["slots"].append(attr.name)

            model["classes"][obj.name] = {
                "name": obj.name,
                "description": obj.description,
                "slots": [attr.name for attr in _attributes],
            }
    model["slots"] = _slots
    print("Writing model to", output_dir)
    with open(f"{output_dir}/{name}.yaml", "w") as fh:
        fh.write(yaml.dump(model, sort_keys=False))
