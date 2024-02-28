from typing import Optional

import yaml
from linkml.utils.schema_builder import (
    SchemaBuilder,
    SchemaDefinition,
    ClassDefinition,
    EnumDefinition,
    SlotDefinition,
    PermissibleValue,
)

from linkml.utils.helpers import convert_to_snake_case

from ..models.eap import Object, Attribute, Connector, Package, Document
from ..models.usdm_ct import CodeList

IDENTIFIER_TYPES = ["id", "uuid"]

TYPE_MAPPING = {
    "String": "string",
    "Integer": "integer",
    "Boolean": "boolean",
    "Float": "float",
}


def generate_schema_builder(
    name: str,
    document: Document,
    prefix: Optional[str] = None,
    output_dir: Optional[str] = "output",
):
    """
    Use a SchemaBuilder to create the LinkML document
    """
    sb = SchemaBuilder(name)
    # add default elements
    sb.add_defaults()
    sb.add_prefix(name, prefix)
    sb.add_prefix("ncit", "https://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl")
    for obj in document.objects:
        if obj.object_type == "Class":
            # holder for extra attrs
            _class = ClassDefinition(obj.name)
            if obj.description:
                _class.description = obj.description
            if obj.reference_url:
                # if a verbatim reference url
                if obj.reference_url.startswith("http"):
                    _class.definition_uri = obj.reference_url
                elif obj.reference_url.startswith("C"):
                    # if a NCI C-code
                    _class.definition_uri = "ncit:" + obj.reference_url
                else:
                    _class.reference = obj.reference_url
            if obj.generalizations:
                _class.is_a = obj.generalizations[0].target_object.name
                # _class.is_a = super_class.target_object.name
            if obj.preferred_term:
                _class.title = obj.preferred_term
            if obj.synonyms:
                _class.aliases = obj.synonyms
            for attr in obj.object_attributes:  # type: Attribute
                _attr = SlotDefinition(attr.name)  # eg protocolVersion
                if attr.reference_url:
                    if attr.reference_url.startswith("http"):
                        _attr.definition_uri = attr.reference_url
                    elif attr.reference_url.startswith("C"):
                        _attr.definition_uri = "ncit:" + attr.reference_url
                    else:
                        _attr.reference = attr.reference_url
                if attr.description:
                    _attr.description = attr.description
                if attr.attribute_type:
                    # Multivalued attributes are represented as lists
                    if "List" in attr.attribute_type:
                        _attr.multivalued = True
                        _attr.range = attr.attribute_type.split("<")[1].split(">")[0]
                    else:
                        _attr.range = TYPE_MAPPING.get(
                            attr.attribute_type, attr.attribute_type
                        )
                if attr.lower_bound == 1:
                    _attr.required = True
                if attr.preferred_term:
                    _attr.title = attr.preferred_term
                if attr.synonyms:
                    _attr.aliases = attr.synonyms
                if attr.codelist:
                    _codelist = attr.codelist  # type: CodeList
                    # if the item is enumerated
                    if attr.codelist.concept_c_code not in sb.schema.enums:
                        _enum = EnumDefinition(_codelist.concept_c_code)
                        _enum.description = _codelist.definition
                        _enum.enum_uri = "ncit:" + _codelist.concept_c_code
                        _enum.code_set = _codelist.concept_c_code
                        for pv in _codelist.items:
                            _pv = PermissibleValue(pv.concept_c_code)
                            _pv.meaning = "ncit:" + pv.concept_c_code
                            if pv.preferred_term:
                                _pv.title = pv.preferred_term
                            if pv.synonyms:
                                _pv.aliases = pv.synonyms
                            if pv.definition:
                                _pv.description = pv.definition

                            _enum.permissible_values[_pv.text] = _pv
                        sb.add_enum(_enum)
                    _attr.range = _codelist.concept_c_code
                _class.attributes[_attr.name] = _attr
            sb.add_class(_class)
    print("Writing model to", output_dir)
    with open(f"{output_dir}/{name}.yaml", "w") as fh:
        fh.write(yaml.dump(sb.as_dict(), sort_keys=False))


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
            "ncit": dict(
                prefix_reference="https://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl"
            ),
            name: dict(prefix_reference=prefix),
        },
        "imports": ["linkml:types"],
        "default_range": "string",
        "default_prefix": name,
        "default_curi_maps": ["semweb_context"],
        "classes": {},
        "slots": {},
    }
    _enums = {}
    _types = {}
    _slots = {}
    # create a back reference for the slots to the classes
    for obj in document.objects:  # type: Object
        # we should probably use the class attribute of the document here
        if obj.object_type == "Class":
            _attributes = sorted(obj.object_attributes)
            # across all the attributes
            for attr in _attributes:  # type: Attribute
                # _slot = _slots.setdefault(attr.name, {"refs": []})
                _slot = _slots.setdefault(attr.name, {})
                if attr.name in IDENTIFIER_TYPES:
                    _slot["identifier"] = True
                if attr.attribute_type:
                    # Multivalued attributes are represented as lists
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
                if attr.lower_bound == 1:
                    _slot["required"] = True
                # if attr.cardinality:
                #     print("Cardinality:", attr.cardinality)
            for attr in obj.outgoing_connections:  # type: Connector
                _slot = _slots.setdefault(attr.name, {})
                _slot["range"] = attr.target_object.name
                # _slot["multivalued"] = True
                # _slot["required"] = True
                # _slot["refs"].append(obj.name)
                # if attr.description:
                #     _slot["description"] = attr.description
                # if attr.lower_bound == 1:
                #     _slot["required"] = True
                # if attr.cardinality:
                #     print("Cardinality:", attr.cardinality)
    # create a back reference for the types to the classes
    for obj in document.objects:  # type: Object
        if obj.object_type == "Class":
            _class = {
                "name": obj.name,
                "description": obj.description,
            }
            if obj.generalizations:
                super_class = obj.generalizations[0]  # type: Connector
                _class["is_a"] = super_class.target_object.name

            _object_id = obj.object_id
            _all_attributes = sorted(obj.object_attributes)
            _object_slots = []
            _attributes = {}
            for attr in _all_attributes:  # type: Attribute
                # if attr.attribute_type in ("Map"):
                #     _attributes[attr.name] = dict(type="map", slot_usage="required")
                # else:
                if "List" in attr.attribute_type:
                    attr.attribute_type = attr.attribute_type.replace("List", "list")
                    range_name = attr.attribute_type.split("<")[1].split(">")[0]
                _object_slots.append(attr.name)
            for conn in obj.outgoing_connections:
                if conn.connector_type == "Association":
                    _object_slots.append(conn.name)

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
            # add the attributes
            if _attributes:
                _class["attributes"] = _attributes
            if _object_slots:
                _class["slots"] = _object_slots
            model["classes"][obj.name] = _class
    if _slots:
        model["slots"] = _slots
    # add a Map class
    model["classes"]["Map"] = {
        "name": "Map",
        "description": "A map of key-value pairs",
        "slots": [
            "key",
            "value",
        ],
    }
    model["slots"]["key"] = {"range": "string"}
    model["slots"]["value"] = {"range": "string"}
    print("Writing model to", output_dir)
    with open(f"{output_dir}/{name}.yaml", "w") as fh:
        fh.write(yaml.dump(model, sort_keys=False))
