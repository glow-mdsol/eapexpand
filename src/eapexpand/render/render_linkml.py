from typing import Optional, List, Union
import logging
import re
import yaml
from linkml_runtime.utils.schema_builder import (
    SchemaBuilder,
    ClassDefinition,
    SlotDefinition,
)
from ..models.eap import Attribute, Connector, Document
from ..report import get_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IDENTIFIER_TYPES = ["id", "uuid"]


TYPE_MAPPING = {
    "String": "string",
    "string": "string",
    "Integer": "integer",
    "Boolean": "boolean",
    "Float": "float",
    "Date": "date",
}


def _to_snake_case(name: str) -> str:
    """
    Convert mixed/camel/Pascal-case names into LinkML-friendly snake_case.
    """
    if not name:
        return name
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", name)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.lower()


def _uml_bounds(cardinality: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """
    Parse a UML multiplicity ("0..1", "1..*", "1", "0..2") into (lower, upper);
    upper is None when unbounded or unknown.
    """
    text = (cardinality or "").strip()
    lower_raw, _, upper_raw = text.partition("..")
    if not upper_raw:
        upper_raw = lower_raw
    lower = int(lower_raw) if lower_raw.isdigit() else None
    upper = int(upper_raw) if upper_raw.isdigit() else None
    return lower, upper


def _merge_slot_definitions(existing: SlotDefinition, incoming: SlotDefinition) -> SlotDefinition:
    """
    Merge two same-name slots, preserving a single slot and widening it for unions.
    """
    existing_ranges = set()
    if existing.range:
        existing_ranges.add(str(existing.range))
    for option in existing.any_of or []:
        if isinstance(option, dict) and option.get("range"):
            existing_ranges.add(str(option["range"]))

    incoming_ranges = set()
    if incoming.range:
        incoming_ranges.add(str(incoming.range))
    for option in incoming.any_of or []:
        if isinstance(option, dict) and option.get("range"):
            incoming_ranges.add(str(option["range"]))

    all_ranges = sorted(existing_ranges | incoming_ranges)
    if len(all_ranges) == 1:
        existing.range = all_ranges[0]
        existing.any_of = None
    elif len(all_ranges) > 1:
        existing.range = None
        existing.any_of = [{"range": range_name} for range_name in all_ranges]

    existing_required = bool(existing.required)
    incoming_required = bool(incoming.required)
    existing.required = existing_required and incoming_required

    # a union is as permissive as its widest member
    if existing.minimum_cardinality is not None and incoming.minimum_cardinality is not None:
        existing.minimum_cardinality = min(existing.minimum_cardinality, incoming.minimum_cardinality)
    else:
        existing.minimum_cardinality = None
    if existing.multivalued != incoming.multivalued:
        # one member is single-valued (implicit max 1): only a bounded list keeps its max
        bounded = [s.maximum_cardinality for s in (existing, incoming) if s.multivalued]
        existing.maximum_cardinality = bounded[0] if bounded and bounded[0] is not None else None
    elif existing.maximum_cardinality is not None and incoming.maximum_cardinality is not None:
        existing.maximum_cardinality = max(existing.maximum_cardinality, incoming.maximum_cardinality)
    else:
        existing.maximum_cardinality = None

    existing.multivalued = bool(existing.multivalued) or bool(incoming.multivalued)
    is_reference = existing.inlined is False and not existing.inlined_as_list
    if is_reference:
        # references by id (union connectors sharing an API name) stay un-inlined
        pass
    elif existing.multivalued:
        existing.inlined_as_list = True
        existing.inlined = False
    elif incoming.inlined:
        existing.inlined = True

    if not existing.description and incoming.description:
        existing.description = incoming.description
    if not existing.definition_uri and incoming.definition_uri:
        existing.definition_uri = incoming.definition_uri
    if not existing.title and incoming.title:
        existing.title = incoming.title

    existing_aliases = list(existing.aliases or [])
    for alias in incoming.aliases or []:
        if alias not in existing_aliases:
            existing_aliases.append(alias)
    if existing_aliases:
        existing.aliases = existing_aliases

    if incoming.annotations:
        if existing.annotations is None:
            existing.annotations = incoming.annotations
        else:
            for annotation_name in incoming.annotations:
                existing.annotations[annotation_name] = incoming.annotations[annotation_name]

    return existing


def generate_schema_builder(
    name: str,
    document: Document,
    schema_id: Optional[str] = None,
    output_dir: Optional[str] = "output",
    use_internal_enums: bool = True,
):
    """
    Generate a schema builder for creating a LinkML document.

    This function utilizes a `SchemaBuilder` to construct a LinkML schema based on the provided
    document and its attributes. It supports adding classes, slots, prefixes, and enumerations
    to the schema, and handles various configurations for attributes, including multivalued,
    required, and optional attributes. The resulting schema is written to a YAML file.

    Args:
        name (str): The name of the schema.
        document (Document): The document object containing metadata and definitions for the schema.
        schema_id (Optional[str], optional): An optional schema ID. If not provided, the document's
            prefix will be used. Defaults to None.
        output_dir (Optional[str], optional): The directory where the generated schema YAML file
            will be saved. Defaults to "output".
        use_internal_enums (bool, optional): Retained for compatibility. Codelist enums are not generated.
    Raises:
        ValueError: If required attributes or configurations are missing in the document.

    Notes:
        - The function supports adding default elements, prefixes, and enumerations to the schema.
        - It handles special cases for attributes with specific types, such as `AliasCode` and
          multivalued attributes.
        - Missing types are logged, and a "Map" type is added if required.
        - The schema's description and version are derived from the document metadata.

    Example:
        generate_schema_builder(
            name="example_schema",
            document=my_document,
            schema_id="http://example.org/schema",
            output_dir="schemas")
    """
    if schema_id:
        logger.info(f"Using schema_id: {schema_id}")
        _id = schema_id
    elif document.prefix:
        logger.info(f"Using document prefix: {document.prefix}")
        _id = document.prefix
    else:
        logger.warning("No schema_id or document prefix provided, using default.")
        _id = f"https://example.org/{name}"
    sb = SchemaBuilder(name, id=_id)
    # sb.description = document.description
    # add default elements
    sb.add_defaults()
    for prefix, uri in document.prefixes.items():
        sb.add_prefix(prefix, uri)
    _missing_types = []
    # ADD a container
    # sb.add_class(ClassDefinition(name, tree_root=True))
    message = ClassDefinition(
        "Message",
        description="A USDM message",
    )
    sb.add_class(
        message,
        slots=[
            SlotDefinition(
                name="study",
                range="Study",
                required=True,
                inlined=True,
                description="USDM Study Definition",
            ),
            SlotDefinition(
                name="usdm_version",
                range="string",
                required=True,
                aliases=["usdmVersion"],
                description="Version of the USDM message",
            ),
            SlotDefinition(
                name="system_version",
                range="string",
                required=True,
                aliases=["systemVersion"],
                description="Version of the System that generated the USDM message",
            ),
            SlotDefinition(
                name="system_name",
                range="string",
                required=True,
                aliases=["systemName"],
                description="Name of the System that generated the USDM message",
            ),
        ],
        use_attributes=True,
    )
    # add the default types
    base = ClassDefinition(
        "Base", description="A base class for all USDM classes", mixin=True
    )
    sb.add_class(
        base,
        slots=[
            SlotDefinition(
                name="instance_type",
                range="string",
                description="API attribute to identify the class type",
                multivalued=False,
                inlined=True,
                aliases=["instanceType"],
            ),
            SlotDefinition(
                name="extension_attributes",
                range="ExtensionAttribute",
                description="Extension attributes for this instance",
                multivalued=True,
                inlined_as_list=True,
                required=False,
                aliases=["extensionAttributes"],
            ),
        ],
        use_attributes=True,
    )
    _id = SlotDefinition(name="id",
        definition_uri="ncit:C25364",
        description="One or more characters used to identify, name, or characterize"
          " the nature, properties, or contents of a thing.",
        title="id",
        aliases=["Identifier", "Unique Identifier"],
        identifier=True,
        range="string",
        multivalued=False,
        inlined=True)
    sb.add_slot(_id)
    for obj in document.objects:
        if obj.object_type == "Class":
            # holder for extra attrs
            _class_name = obj.name
            _class = ClassDefinition(_class_name, mixins=["Base"])  # type: ClassDefinition
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
            if _class_name == "AliasCode":
                _class.abstract = True
            if obj.preferred_term:
                _class.title = obj.preferred_term
            if obj.synonyms:
                _class.aliases = obj.synonyms
            # add the classes as datatypes
            TYPE_MAPPING[_class_name] = _class_name
            _attributes: List[SlotDefinition] = []
            _attribute_index = {}
            for attr in obj.all_attributes:
                if attr.name in IDENTIFIER_TYPES:
                    logger.info(f"Adding identifier for {attr.name}")
                    _class.slots = ["id"]
                    continue
                if attr.range not in TYPE_MAPPING:
                    # can we work out the --Id attributes
                    pass
                if attr.name in ["dictionaries"]:
                    print("Adding dictionaries")
                attr: Union[Attribute, Connector]
                # if attr.name == "name":
                #     print(f"Adding attribute {obj.name}.{attr.name}")
                # name is protected in schemabuilder
                # relationships exchanged by id are named for the exchange format
                # (e.g. nextId) but keep the UML target class as their range
                is_reference = isinstance(attr, Connector) and attr.is_reference
                source_attribute_name = attr.api_name if is_reference else attr.name
                if is_reference:
                    source_slot_name = str(attr.api_name)
                elif attr.name == "name":
                    # attribute name where "name" gets blitzed
                    source_slot_name = f"{obj.name}{attr.name.capitalize()}"
                else:
                    source_slot_name = str(attr.name)

                canonical_slot_name = _to_snake_case(source_slot_name)
                _attr = SlotDefinition(name=canonical_slot_name)
                if source_attribute_name and source_attribute_name != canonical_slot_name:
                    aliases = list(_attr.aliases or [])
                    if source_attribute_name not in aliases:
                        aliases.append(source_attribute_name)
                    _attr.aliases = aliases
                _attr.annotations = {
                    "source_attribute_name": {
                        "tag": "source_attribute_name",
                        "value": str(source_attribute_name),
                    },
                    "source_slot_name": {
                        "tag": "source_slot_name",
                        "value": str(source_slot_name),
                    },
                }
                if is_reference:
                    _attr.annotations["uml_role"] = {"tag": "uml_role", "value": str(attr.name)}
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
                # if attr.name in IDENTIFIER_TYPES:
                #     _attr.identifier = True
                if attr.attribute_type:
                    # Multivalued attributes are represented as lists
                    if "List" in attr.attribute_type:
                        _attr.multivalued = True
                        _attr.inlined_as_list = True
                        _attr_type = attr.attribute_type.split("<")[1].split(">")[0]
                        if _attr_type not in TYPE_MAPPING:
                            _missing_types.append(_attr_type)
                        _attr.range = TYPE_MAPPING.get(_attr_type, _attr_type)
                    else:
                        if attr.attribute_type not in TYPE_MAPPING:
                            _missing_types.append(attr.attribute_type)
                        # NOTE: this is a hack to handle the different types of superclass
                        # (not needed for references by id: the UML range already
                        # admits its subclasses)
                        if not is_reference and attr.attribute_type in [
                            "ScheduledInstance",
                            "ScheduledDecisionInstance",
                            "ScheduledActivityInstance",
                        ]:
                            _attr.any_of = [
                                {"range": x}
                                for x in [
                                    "ScheduledInstance",
                                    "ScheduledDecisionInstance",
                                    "ScheduledActivityInstance",
                                ]
                            ]
                        # NOTE: this is a hack to handle the different types of superclass - this has been made concrete in 4.0
                        elif attr.attribute_type in ["StudySite" "StudyCohort"]:
                            _attr.any_of = [
                                {"range": x}
                                for x in ["StudySite", "StudyCohort", "GeographicScope"]
                            ]
                        else:
                            _attr.range = TYPE_MAPPING.get(
                                attr.attribute_type, attr.attribute_type
                            )
                #    _attr.multivalued = False
                #     _attr.required = False
                if isinstance(attr, (Connector,)):
                    # Connector uses cardinality
                    _attr.multivalued = bool(attr.multivalued)
                    if is_reference:
                        # serialised as the target's identifier, not a nested object
                        _attr.inlined = False
                    elif attr.multivalued:
                        _attr.inlined_as_list = True
                    else:
                        _attr.inlined = True
                    if attr.optional:
                        _attr.required = False
                    else:
                        _attr.required = True

                else:
                    # Attribute uses the lower_bound and upper_bound
                    if attr.lower_bound == "1":
                        _attr.required = True
                    if attr.upper_bound == "1":
                        _attr.multivalued = False
                        _attr.inlined = True
                    else:
                        _attr.multivalued = True
                        _attr.inlined_as_list = True
                if _attr.multivalued:
                    # `required` alone only demands the key, so carry the UML
                    # bounds of a list (1..*, 0..2) as explicit cardinalities
                    _lower, _upper = _uml_bounds(attr.cardinality)
                    if _lower and _lower > 0:
                        _attr.minimum_cardinality = _lower
                    if _upper is not None:
                        _attr.maximum_cardinality = _upper
                if attr.preferred_term:
                    _attr.title = attr.preferred_term
                if attr.synonyms:
                    _attr.aliases = attr.synonyms
                # TODO: add the description, pydantic exporter doesn't expose all the attributes; just title, description, and values
                if attr.codelist:
                    _codelist = attr.codelist  # type: CodeList
                    if _attr.annotations is None:
                        _attr.annotations = {}
                    annotations = _attr.annotations
                    if _codelist.concept_c_code:
                        annotations["codelist_code"] = {
                            "tag": "codelist_code",
                            "value": _codelist.concept_c_code,
                        }
                    annotations["codelist_extensible"] = {
                        "tag": "codelist_extensible",
                        "value": bool(_codelist.extensible),
                    }
                    _attr.annotations = annotations
                _slot_name = str(_attr.name)
                if _slot_name in _attribute_index:
                    _merge_slot_definitions(_attribute_index[_slot_name], _attr)
                else:
                    _attributes.append(_attr)
                    _attribute_index[_slot_name] = _attr
                # if _attr.name == "name":
                #     print("Adding name attribute")
                #     _attr.aliases = ["name"]
                #     _class.attributes[
                #         "".join([obj.name.lower(), _attr.name.capitalize()])
                #     ] = _attr
                # else:
                # _class.attributes[_attr.name] = _attr
            _class.attributes = _attribute_index
            if _class_name in sb.schema.classes:
                existing_class = sb.schema.classes[_class_name]
                existing_attributes = existing_class.attributes or {}
                for slot_name, slot_def in _attribute_index.items():
                    if slot_name in existing_attributes:
                        _merge_slot_definitions(existing_attributes[slot_name], slot_def)
                    else:
                        existing_attributes[slot_name] = slot_def
                existing_class.attributes = existing_attributes
                if _class.slots:
                    existing_slots = list(existing_class.slots or [])
                    existing_class.slots = list(dict.fromkeys(existing_slots + list(_class.slots)))
            else:
                sb.add_class(_class)
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
        get_report().warning("LinkML: types with no class or mapping", absent_type)
    print("Writing model to", output_dir)
    _schema = sb.as_dict()

    # add the description, not available for builder
    _schema["description"] = document.description
    if document.version:
        # remove the v prefix
        _schema["version"] = document.version.replace("v", "")
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
