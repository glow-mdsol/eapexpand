from typing import Optional

import yaml

from ..models.eap import Object, Attribute, Connector, Package

def generate(self, 
             name: str,
             objects: dict, 
             output_dir: Optional[str] = "output"):
    """
    Create a LinkML representation from the EAP model
    """
    model = {"id": name, "name": name, "classes": [], "slots": []}
    slots = {}
    for obj in objects.values():  # type: Object
        if obj.object_type == "Class":
            _class = {"slots": []}
            _object_id = obj.object_id
            _attributes = sorted(obj.attributes)
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
    with open(f"{output_dir}/{name}.yaml", "w") as fh:
        fh.write(yaml.dump(model, sort_keys=False))
        