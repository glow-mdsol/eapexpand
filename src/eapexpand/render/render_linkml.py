from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import yaml
from linkml.utils.schema_builder import (
    SchemaBuilder,
    ClassDefinition,
    EnumDefinition,
    SlotDefinition,
    PermissibleValue,
)

from ..models.eap import Attribute, Connector, Document
from ..models.usdm_ct import CodeList

IDENTIFIER_TYPES = ["id", "uuid"]


TYPE_MAPPING = {
    "String": "string",
    "string": "string",
    "Integer": "integer",
    "Boolean": "boolean",
    "Float": "float",
    "Date": "date",
}


def generate_schema_builder(
    name: str,
    document: Document,
    schema_id: Optional[str] = None,
    output_dir: Optional[str] = "output",
):
    """
    Use a SchemaBuilder to create the LinkML document
    """
    if schema_id:
        logger.info(f"Using schema_id: {schema_id}")
        _id = schema_id
    elif document.prefix:
        logger.info(f"Using document prefix: {document.prefix}")
        _id = document.prefix

    sb = SchemaBuilder(name, id=_id)
    sb.description = document.description
    # add default elements
    sb.add_defaults()
    for prefix, uri in document.prefixes.items():
        sb.add_prefix(prefix, uri)
    _missing_types = []
    # ADD a container
    # sb.add_class(ClassDefinition(name, tree_root=True))
    for obj in document.objects:
        if obj.object_type == "Class":
            # holder for extra attrs
            _class = ClassDefinition(
                obj.name,
            )  # type: ClassDefinition
            if obj.name == document.root_item:
                _class.tree_root = True
            
            if obj.description:
                _class.description = obj.description
            if obj.reference_url:
                # if a verbatim reference url
                if obj.reference_url.startswith("http"):
                    _class.definition_uri = obj.reference_url
                elif obj.reference_url.startswith("C") and obj.reference_url != "CNEW":
                    # if a NCI C-code
                    _class.definition_uri = "ncit:" + obj.reference_url
                else:
                    _class.definition_uri = obj.reference_url
            if obj.generalizations:
                _class.is_a = obj.generalizations[0].target_object.name
                # _class.is_a = super_class.target_object.name
            if obj.specializations:
                # make super classes abstract
                _class.abstract = True
            if obj.preferred_term:
                _class.title = obj.preferred_term
            if obj.synonyms:
                _class.aliases = obj.synonyms
            # add the classes as datatypes
            TYPE_MAPPING[obj.name] = obj.name
            _attributes: List[SlotDefinition] = []
            for attr in obj.all_attributes:  # type: Attribute
                # if attr.name == "name":
                #     print(f"Adding attribute {obj.name}.{attr.name}")
                if attr.name == "name":
                    # attribute name where "name" gets blitzed
                    _name = obj.name.lower() + attr.name.capitalize()
                    _attr = SlotDefinition(
                        name=_name, aliases=["name"]
                    )  # eg protocolVersion
                else:
                    _attr = SlotDefinition(name=attr.name)
                if attr.reference_url:
                    if attr.reference_url.startswith("http"):
                        _attr.definition_uri = attr.reference_url
                    elif (
                        attr.reference_url.startswith("C")
                        and attr.reference_url != "CNEW"
                    ):
                        _attr.definition_uri = "ncit:" + attr.reference_url
                    else:
                        _attr.definition_uri = attr.reference_url
                if attr.description:
                    _attr.description = attr.description
                _attr.multivalued = False
                if attr.name in IDENTIFIER_TYPES:
                    _attr.identifier = True
                if attr.attribute_type:
                    # Multivalued attributes are represented as lists
                    if "List" in attr.attribute_type:
                        _attr.multivalued = True
                        _attr_type = attr.attribute_type.split("<")[1].split(">")[0]
                        if _attr_type not in TYPE_MAPPING:
                            _missing_types.append(_attr_type)
                        _attr.range = TYPE_MAPPING.get(_attr_type, _attr_type)
                    else:
                        if attr.attribute_type not in TYPE_MAPPING:
                            _missing_types.append(attr.attribute_type)
                        _attr.range = TYPE_MAPPING.get(
                            attr.attribute_type, attr.attribute_type
                        )
                if isinstance(attr, (Connector,)):
                    if attr.multivalued:
                        _attr.multivalued = True
                    else:
                        _attr.multivalued = False
                    if attr.optional:
                        _attr.required = False
                    else:
                        _attr.required = True
                else:
                    if attr.lower_bound == 1:
                        _attr.required = True
                    if attr.upper_bound == 1:
                        _attr.multivalued = False
                if attr.preferred_term:
                    _attr.title = attr.preferred_term
                if attr.synonyms:
                    _attr.aliases = attr.synonyms
                if attr.codelist:
                    _codelist = attr.codelist  # type: CodeList
                    if _codelist.preferred_term:
                        _codelist_name = "".join(_codelist.preferred_term.split())
                    else:
                        _codelist_name = f"{_codelist.entity_name}{_codelist.attribute_name.capitalize()}"
                    # if the item is enumerated
                    if _codelist_name not in sb.schema.enums:
                        _enum = EnumDefinition(
                            name=_codelist_name
                        )
                        _enum.name = _codelist_name
                        if _codelist.preferred_term:
                            _enum.title = _codelist.preferred_term
                        else:
                            _enum.title = _codelist.attribute_name
                        if _codelist.synonyms:
                            _enum.aliases = _codelist.synonyms
                        # TODO: imported_from
                        _enum.description = _codelist.definition
                        _enum.definition_uri = "ncit:" + _codelist.concept_c_code
                        _enum.enum_uri = "ncit:" + _codelist.concept_c_code
                        _enum.code_set = _codelist.concept_c_code
                        if _codelist.alternate_name:
                            # TODO: add a mapping to the alternate name 
                            pass
                        for pv in _codelist.items:
                            _pv = PermissibleValue(pv.concept_c_code)
                            _pv.meaning = "ncit:" + pv.concept_c_code
                            if pv.preferred_term:
                                _pv.title = pv.preferred_term
                                _pv.text = pv.preferred_term
                            if pv.synonyms:
                                _pv.aliases = pv.synonyms
                            if pv.definition:
                                _pv.description = pv.definition
                            _enum.permissible_values[_pv.text] = _pv
                        sb.add_enum(_enum)
                    _attr.range = _codelist_name
                _attributes.append(_attr)
                # if _attr.name == "name":
                #     print("Adding name attribute")
                #     _attr.aliases = ["name"]
                #     _class.attributes[
                #         "".join([obj.name.lower(), _attr.name.capitalize()])
                #     ] = _attr
                # else:
                # _class.attributes[_attr.name] = _attr
            # _class.attributes = _attributes
            sb.add_class(_class, slots=_attributes, use_attributes=True)
    if "Map" in set(_missing_types) - set(TYPE_MAPPING.keys()):
        print("Adding Map type")
        # add a map class
        _map = ClassDefinition("Map")
        _map.description = "A map of key-value pairs"
        _map.attributes["key"] = SlotDefinition("key")
        _map.attributes["key"].range = "string"
        _map.attributes["value"] = SlotDefinition("value")
        _map.attributes["value"].range = "string"
        sb.add_class(_map)
    for absent_type in set(_missing_types) - set(TYPE_MAPPING.keys()):
        print("Missing type:", absent_type)
    print("Writing model to", output_dir)
    _schema = sb.as_dict()
    # add the description, not available for builder
    _schema["description"] = document.description
    if document.version:
        _schema["version"] = document.version
    with open(f"{output_dir}/{name}.yaml", "w") as fh:
        fh.write(yaml.dump(_schema, sort_keys=False))


# def generate(
#     name: str,
#     document: Document,
#     prefix: Optional[str] = "",
#     output_dir: Optional[str] = "output",
# ):
#     """
#     Create a LinkML representation from the EAP model
#     """
#
#     if not prefix:
#         prefix = f"https://example.org/{name}"
#     model = {
#         "id": name,
#         "name": name,
#         "prefixes": {
#             "linkml": dict(prefix_reference="https://w3id.org/linkml/"),
#             "ncit": dict(
#                 prefix_reference="https://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl"
#             ),
#             name: dict(prefix_reference=prefix),
#         },
#         "imports": ["linkml:types"],
#         "default_range": "string",
#         "default_prefix": name,
#         "default_curi_maps": ["semweb_context"],
#         "classes": {},
#         "slots": {},
#     }
#     _enums = {}
#     _types = {}
#     _slots = {}
#     # create a back reference for the slots to the classes
#     for obj in document.objects:  # type: Object
#         # we should probably use the class attribute of the document here
#         if obj.object_type == "Class":
#             _attributes = sorted(obj.object_attributes)
#             # across all the attributes
#             for attr in _attributes:  # type: Attribute
#                 # _slot = _slots.setdefault(attr.name, {"refs": []})
#                 _slot = _slots.setdefault(attr.name, {})
#                 if attr.name in IDENTIFIER_TYPES:
#                     _slot["identifier"] = True
#                 if attr.attribute_type:
#                     # Multivalued attributes are represented as lists
#                     if "List" in attr.attribute_type:
#                         _slot["multivalued"] = True
#                         _slot["range"] = attr.attribute_type.split("<")[1].split(">")[0]
#                     else:
#                         _slot["range"] = TYPE_MAPPING.get(
#                             attr.attribute_type, attr.attribute_type
#                         )
#                     # _slot["refs"].append(obj.name)
#                     _types.setdefault(attr.attribute_type, []).append(obj)
#                 if attr.description:
#                     _slot["description"] = attr.description
#                 if attr.lower_bound == 1:
#                     _slot["required"] = True
#                 # if attr.cardinality:
#                 #     print("Cardinality:", attr.cardinality)
#             for attr in obj.outgoing_connections:  # type: Connector
#                 _slot = _slots.setdefault(attr.name, {})
#                 _slot["range"] = attr.target_object.name
#                 # _slot["multivalued"] = True
#                 # _slot["required"] = True
#                 # _slot["refs"].append(obj.name)
#                 # if attr.description:
#                 #     _slot["description"] = attr.description
#                 # if attr.lower_bound == 1:
#                 #     _slot["required"] = True
#                 # if attr.cardinality:
#                 #     print("Cardinality:", attr.cardinality)
#     # create a back reference for the types to the classes
#     for obj in document.objects:  # type: Object
#         if obj.object_type == "Class":
#             _class = {
#                 "name": obj.name,
#                 "description": obj.description,
#             }
#             if obj.generalizations:
#                 super_class = obj.generalizations[0]  # type: Connector
#                 _class["is_a"] = super_class.target_object.name
#
#             _object_id = obj.object_id
#             _all_attributes = sorted(obj.object_attributes)
#             _object_slots = []
#             _attributes = {}
#             for attr in _all_attributes:  # type: Attribute
#                 # if attr.attribute_type in ("Map"):
#                 #     _attributes[attr.name] = dict(type="map", slot_usage="required")
#                 # else:
#                 if "List" in attr.attribute_type:
#                     attr.attribute_type = attr.attribute_type.replace("List", "list")
#                     range_name = attr.attribute_type.split("<")[1].split(">")[0]
#                 _object_slots.append(attr.name)
#             for conn in obj.outgoing_connections:
#                 if conn.connector_type == "Association":
#                     _object_slots.append(conn.name)
#
#                 # model.setdefault("slots", {}).setdefault(
#                 #     attr.name,
#                 #     {
#                 #         "name": attr.name,
#                 #         "type": attr.attribute_type,
#                 #         "cardinality": attr.cardinality,
#                 #         "description": attr.notes,
#                 #     },
#                 # )
#                 # _class["slots"].append(attr.name)
#             # add the attributes
#             if _attributes:
#                 _class["attributes"] = _attributes
#             if _object_slots:
#                 _class["slots"] = _object_slots
#             model["classes"][obj.name] = _class
#     if _slots:
#         model["slots"] = _slots
#     # add a Map class
#     model["classes"]["Map"] = {
#         "name": "Map",
#         "description": "A map of key-value pairs",
#         "slots": [
#             "key",
#             "value",
#         ],
#     }
#     model["slots"]["key"] = {"range": "string"}
#     model["slots"]["value"] = {"range": "string"}
#     print("Writing model to", output_dir)
#     with open(f"{output_dir}/{name}.yaml", "w") as fh:
#         fh.write(yaml.dump(model, sort_keys=False))
