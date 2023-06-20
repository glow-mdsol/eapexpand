from typing import Optional

from ..models.eap import Object, Attribute, Connector, Package

def generate(self, name: str,
             packages: dict, 
             objects: dict, 
             attributes: dict, 
             connectors: dict, 
             output_dir: Optional[str] = "output"):
    """
    Create a LinkML representation from the EAP model
    """
    model = {}
    slots = {}
    for obj in objects.values():  # type: Object
        if obj.object_type == "Class":
            _class = {"slots": []}
            _object_id = obj.object_id
            _attributes = sorted(
                [
                    attributes[attr_id]
                    for attr_id in attributes
                    if attributes[attr_id].object_id == _object_id
                ]
            )

            _attributes.sort()
            for attr in _attributes:  # type: Attribute
                if attr not in slots:
                    slots[attr.name] = {
                        "name": attr.name,
                        "type": attr.attribute_type,
                        "cardinality": attr.cardinality,
                        "description": attr.notes,
                    }
                _class["slots"].append(attr.name)

            model[obj.name] = {
                "name": obj.name,
                "attributes": [
                    {
                        "name": attr.name,
                        "type": attr.attribute_type,
                        "cardinality": attr.cardinality,
                        "description": attr.notes,
                    }
                    for attr in _attributes
                ],
            }
        _attributes = sorted(
                    [
                        attributes[attr_id]
                        for attr_id in attributes
                        if attributes[attr_id].object_id == _object_id
                    ]
                )
