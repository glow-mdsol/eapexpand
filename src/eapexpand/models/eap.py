from __future__ import annotations
from datetime import datetime

from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Union
from dataclasses_json import dataclass_json, LetterCase, config


"""
Wrapper dataclasses for the Objects in the EA file
"""

DATE_FORMAT = None


def decode_date(date_str: Optional[str]) -> datetime:
    """
    Decodes a date string into a datetime object
    """
    if isinstance(date_str, datetime):
        return date_str
    global DATE_FORMAT
    if DATE_FORMAT is None:
        if "/" in date_str:
            DATE_FORMAT = "%m/%d/%y %H:%M:%S"
        else:
            DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    return datetime.strptime(date_str, DATE_FORMAT) if date_str else None


def encode_date(date) -> str:
    """
    Encodes a datetime object into a string
    """
    return date.strftime(DATE_FORMAT)


def encode_flag(flag: bool) -> int:
    """
    Encodes a boolean into an integer
    """
    return 1 if flag else 0


def decode_flag(flag: int) -> bool:
    """
    Decodes an integer into a boolean
    """
    return flag == 1


class Diagram:
    def __init__(self, idee: int, name: str, diagram_type: str, version: str):
        self.id = idee
        self.name = name
        self._type = diagram_type
        self._version = version
        self._objects = {}

    def add_object(self, sequence: int, model_object: Object) -> None:
        self._objects[sequence] = model_object


class Document:
    def __init__(
        self,
        name: str,
        prefix: str,
        packages: List[Package],
        objects: List[Object],
        diagrams: List[Diagram],
    ) -> None:
        self.name = name
        self._prefix = prefix
        self._types = []
        self._slots = []
        self._enums = []
        self._packages = packages
        self._objects = objects
        self._diagrams = diagrams
        self._root_item = None
        self._description = None
        self._prefixes = {}
        self._version = None
        # self._attributes = attributes
        # self._connectors = connectors

    @property
    def version(self) -> Optional[str]:
        return self._version
    
    @version.setter
    def version(self, value: str) -> None:
        self._version = value
        
    @property
    def prefixes(self) -> Dict[str, str]:
        return self._prefixes
    
    def add_prefix(self, prefix: str, uri: str) -> None:
        self._prefixes[prefix] = uri

    @property
    def description(self) -> Optional[str]:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def root_item(self) -> Optional[str]:
        return self._root_item
    
    @root_item.setter
    def root_item(self, value: str) -> None:
        self._root_item = value

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def diagrams(self) -> List[Diagram]:
        return self._diagrams

    @property
    def packages(self) -> List[Object]:
        return [x for x in self._objects if isinstance(x, Package)]

    @property
    def objects(self) -> List[Object]:
        """
        Return the objects in the document, ordered by object_id
        """
        return sorted(self._objects)

    def get_object(self, object_id: int) -> Optional[Object]:
        for obj in self._objects:
            if obj.object_id == object_id:
                return obj
        return None

    def get_class_by_name(self, name: str) -> Optional[Class]:
        for obj in self._objects:
            if obj.name == name and isinstance(obj, Class):
                return obj
        return None

    @property
    def attributes(self) -> List[Attribute]:
        return [x for x in self._objects if isinstance(x, Attribute)]

    @property
    def connectors(self) -> List[Connector]:
        return [x for x in self._objects if isinstance(x, Connector)]

    @property
    def classes(self) -> List[Object]:
        return [x for x in self._objects if isinstance(x, Class)]

    @property
    def states(self) -> List[Object]:
        return [x for x in self._objects if isinstance(x, State)]

    @property
    def state_nodes(self) -> List[Object]:
        return [x for x in self._types if isinstance(x, State)]

    @property
    def used_types(self) -> List[str]:
        if not self._types:
            _types = []
            for obj in self._objects:  # type: Object
                if obj.attribute_type and obj.attribute_type not in _types:
                    _types.append(obj.attribute_type)
            self._types = _types
        return self._types

    # @classmethod
    # def from_dict(cls, datatypes: List[DataType], data: Dict[str, Any]) -> Document:
    #     """
    #     Create a document from a dictionary
    #     """
    #     _objects = [Object.from_dict(x) for x in data.get("objects", [])]
    #     _attributes = [Attribute.from_dict(x) for x in data.get("attributes", [])]
    #     _connectors = [Connector.from_dict(x) for x in data.get("connectors", [])]
    #     return cls(data.get("name"), datatypes, _objects, _attributes, _connectors)

    def merge_definitions(self, definitions: Dict[str, str]):
        """
        Merge the definitions into the document
        """
        for obj in self.objects:
            if obj.name in definitions:
                obj.definition = definitions[obj.name]
            for attr in obj.object_attributes:
                if attr.name in definitions:
                    attr.definition = definitions[attr.name]
            if obj.outgoing_connections:
                for conn in obj.outgoing_connections:
                    if conn.name in definitions:
                        conn.definition = definitions[conn.name]


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class DataType:
    id: int = field(metadata=config(field_name="DatatypeID"))
    datatype_type: str = field(metadata=config(field_name="Type"))
    size: Optional[int] = field(metadata=config(field_name="Size"), default=None)
    max_prec: Optional[int] = field(metadata=config(field_name="MaxPrec"), default=None)
    max_scale: Optional[int] = field(
        metadata=config(field_name="MaxScale"), default=None
    )
    default_len: Optional[int] = field(
        metadata=config(field_name="DefaultLen"), default=None
    )
    default_prec: Optional[int] = field(
        metadata=config(field_name="DefaultPrec"), default=None
    )
    default_scale: Optional[int] = field(
        metadata=config(field_name="DefaultScale"), default=None
    )
    user: Optional[int] = field(metadata=config(field_name="User"), default=None)
    generic_type: Optional[str] = field(
        metadata=config(field_name="GenericType"), default=""
    )
    product_name: Optional[str] = field(
        metadata=config(field_name="Product_Name"), default=""
    )
    datatype: Optional[str] = field(metadata=config(field_name="Datatype"), default="")
    max_len: Optional[int] = field(metadata=config(field_name="MaxLen"), default=None)


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Connector:
    """
    Represents a connector in the EAP model
    """

    connector_id: Optional[int] = field(metadata=config(field_name="Connector_ID"), default=None)
    connector_type: Optional[str] = field(metadata=config(field_name="Connector_Type"), default=None)
    start_object_id: Optional[int] = field(metadata=config(field_name="Start_Object_ID"), default=None)
    end_object_id: Optional[int] = field(metadata=config(field_name="End_Object_ID"), default=None)
    start_edge: Optional[int] = field(metadata=config(field_name="Start_Edge"), default=None)
    end_edge: Optional[int] = field(metadata=config(field_name="End_Edge"), default=None)
    seq_no: Optional[int] = None
    head_style: Optional[int] = None
    line_style: Optional[int] = None
    route_style: Optional[int] = None
    is_bold: Optional[int] = None
    line_color: Optional[int] = None
    diagram_id: Optional[int] = field(metadata=config(field_name="DiagramID"), default=None)
    virtual_inheritance: Optional[str] = field(
        metadata=config(field_name="VirtualInheritance"), default=""
    )
    ea_guid: Optional[str] = field(metadata=config(field_name="ea_guid"), default=None)
    is_root: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_leaf: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_spec: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_signal: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_stimulus: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    name: Optional[str] = ""
    dest_card: Optional[str] = field(metadata=config(field_name="DestCard"), default="")
    source_card: Optional[str] = field(
        metadata=config(field_name="SourceCard"), default=""
    )
    direction: Optional[str] = ""
    source_access: Optional[str] = ""
    dest_access: Optional[str] = ""
    dest_element: Optional[str] = ""
    source_containment: Optional[str] = ""
    source_is_aggregate: Optional[int] = -1
    source_is_ordered: Optional[int] = -1
    source_role: Optional[str] = ""
    dest_role: Optional[str] = ""
    dest_containment: Optional[str] = ""
    dest_is_aggregate: Optional[int] = -1
    dest_is_ordered: Optional[int] = -1
    top_end_label: Optional[str] = field(
        metadata=config(field_name="Top_End_Label"), default=""
    )
    source_changeable: Optional[str] = ""
    dest_changeable: Optional[str] = ""
    source_ts: Optional[str] = field(metadata=config(field_name="SourceTS"), default="")
    dest_ts: Optional[str] = field(metadata=config(field_name="DestTS"), default="")
    target2: Optional[int] = -1
    source_style: Optional[str] = ""
    dest_style: Optional[str] = ""
    source_is_navigable: Optional[int] = -1
    dest_is_navigable: Optional[int] = -1
    package_data_1: Optional[str] = field(
        metadata=config(field_name="PDATA1"), default=""
    )
    package_data_2: Optional[str] = field(
        metadata=config(field_name="PDATA2"), default=""
    )
    package_data_3: Optional[str] = field(
        metadata=config(field_name="PDATA3"), default=""
    )
    package_data_4: Optional[str] = field(
        metadata=config(field_name="PDATA4"), default=""
    )
    package_data_5: Optional[str] = field(
        metadata=config(field_name="PDATA5"), default=""
    )
    source_object: Optional[Object] = None
    target_object: Optional[Object] = None
    # a definition if supplied
    definition: Optional[str] = field(default="")
    # Enumerated value
    enumeration: Optional[Enumeration] = field(default=None)
    # eg NCI code/URL
    reference_url: Optional[str] = field(default=None)
    # preferred Term
    preferred_term: Optional[str] = field(default=None)
    # synonyms
    synonyms: Optional[List[str]] = field(default_factory=list)
    # codelist
    codelist: Optional[Any] = field(default=None)

    @property
    def id(self):
        return self.connector_id

    @property
    def attributes(self) -> List[Attribute]:
        """
        Getting the attributes of the object
        """
        if self.target_object:
            return self.target_object.attributes
        else:
            return []

    @property
    def optional(self) -> Optional[bool]:
        return self.dest_card.startswith("0")

    @property
    def multivalued(self) -> Optional[bool]:
        return self.dest_card.endswith("*")

    @property
    def description(self):
        return self.definition

    @property
    def attribute_type(self):
        return self.target_object.name

    @property
    def cardinality(self):
        return self.dest_card


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Attribute:
    """
    Represents an attribute of an object in the EAP model
    """

    object_id: Optional[int] = field(
        metadata=config(field_name="Object_ID"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="Name"), default="")
    scope: Optional[str] = field(metadata=config(field_name="Scope"), default="")
    containment: Optional[str] = field(
        metadata=config(field_name="Containment"), default=""
    )
    is_static: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_collection: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag),
        default=False,
    )
    is_ordered: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    allow_duplicates: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    lower_bound: Optional[str] = field(
        metadata=config(field_name="LowerBound"), default=None
    )
    upper_bound: Optional[str] = field(
        metadata=config(field_name="UpperBound"), default=None
    )
    derived: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    id: Optional[int] = field(metadata=config(field_name="ID"), default=None)
    pos: Optional[int] = field(metadata=config(field_name="Pos"), default=None)
    length: Optional[int] = field(metadata=config(field_name="Length"), default=None)
    const: Optional[bool] = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    attribute_type: Optional[str] = field(
        metadata=config(field_name="Type"), default=""
    )
    classifier_id: Optional[int] = field(
        metadata=config(field_name="Classifier"), default=-1
    )
    attribute_stereotype: Optional[str] = field(
        metadata=config(field_name="Stereotype"), default=""
    )
    ea_guid: Optional[str] = field(metadata=config(field_name="ea_guid"), default=None)
    attribute_classifier: Optional[Object] = None
    default: Optional[str] = field(metadata=config(field_name="Default"), default=None)
    connector: Optional[Connector] = None
    note: Optional[str] = field(metadata=config(field_name="Note"), default="")
    # Definition if supplied
    definition: Optional[str] = field(default="")
    # Enumerated value
    enumeration: Optional[Enumeration] = field(default=None)
    # eg NCI code/URL
    reference_url: Optional[str] = field(default=None)
    # preferred Term
    preferred_term: Optional[str] = field(default=None)
    # synonyms
    synonyms: Optional[List[str]] = field(default_factory=list)
    # codelist
    codelist: Optional[Any] = None
    # api Attributes
    api_attribute: Optional[str] = field(default=None)

    def __lt__(self, other):
        if "pos" in other.__dict__.keys():
            return self.pos < other.pos
        return True

    @property
    def cardinality(self):
        if self.connector:
            #
            return self.connector.dest_card if self.connector.dest_card else "1..1"
        return "1..1"

    @property
    def description(self) -> str:
        if self.definition:
            return self.definition.strip()
        elif self.note:
            return self.note.strip()
        else:
            return ""


# @dataclass
# class ConnectorAttribute(Attribute):
#     dest_card: Optional[str] = None
#     @classmethod
#     def from_connector(cls, connector: Connector):
#         _attr = cls()
#         _attr.name = connector.name
#         _attr.attribute_type = connector.target_object.name
#         # this provides the cardinality
#         _attr.connector = connector
#         _attr.pos = connector.start_object_id + connector.end_object_id
#         _attr.preferred_term = connector
#         return _attr


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Object:
    """
    Represents an object in the EAP model
    """

    object_id: int = field(metadata=config(field_name="Object_ID"), default=None)
    object_type: str = field(metadata=config(field_name="Object_Type"), default="")
    diagram_id: int = field(metadata=config(field_name="Diagram_ID"), default=None)
    package_id: int = field(metadata=config(field_name="Package_ID"), default=None)
    package: Optional[Package] = None
    ntype: int = field(metadata=config(field_name="NType"), default=0)
    complexity: Optional[str] = field(
        metadata=config(field_name="Complexity"), default=""
    )
    effort: Optional[int] = field(metadata=config(field_name="Effort"), default=0)
    created_date: Optional[datetime] = field(
        metadata=config(encoder=encode_date, decoder=decode_date), default=None
    )
    modified_date: Optional[datetime] = field(
        metadata=config(encoder=encode_date, decoder=decode_date),
        default=None,
    )
    parent_id: int = field(metadata=config(field_name="ParentID"), default=-1)
    is_root: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_leaf: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_spec: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    is_active: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag), default=False
    )
    classifier: Optional[int] = 0
    phase: Optional[str] = ""
    name: Optional[str] = ""
    author: Optional[str] = ""
    version: Optional[str] = ""
    note: Optional[str] = ""
    ea_guid: Optional[str] = field(metadata=config(field_name="ea_guid"), default=None)
    outgoing_connections: Optional[List[Connector]] = field(default_factory=list)
    incoming_connections: Optional[List[Connector]] = field(default_factory=list)
    generalizations: Optional[List[Connector]] = field(default_factory=list)
    specializations: Optional[List[Connector]] = field(default_factory=list)
    object_attributes: Optional[List[Attribute]] = field(default_factory=list)
    properties: Optional[List[ObjectProperty]] = field(default_factory=list)
    classifies: Optional[List[Object]] = field(default_factory=list)
    edges: Optional[List[Connector]] = field(default_factory=list)
    # a definition if supplied
    definition: Optional[str] = field(default="")
    # Enumerated value
    enumeration: Optional[Enumeration] = field(default=None)
    # eg NCI code/URL
    reference_url: Optional[str] = field(default=None)
    # preferred Term
    preferred_term: Optional[str] = field(default=None)
    # synonyms
    synonyms: Optional[List[str]] = field(default_factory=list)

    @property
    def all_attributes(self) -> List[Attribute | Connector]:
        """
        Getting the attributes of the object
        """
        attributes = [(x.pos, x) for x in self.object_attributes]
        start = max([x[0] for x in attributes]) if attributes else 1
        for idx, conn in enumerate(self.outgoing_connections, start=start):
            if conn.connector_type == "Association":
                attributes.append((idx, conn))
        return [x[1] for x in sorted(attributes, key=lambda x: x[0])]

    @property
    def attributes(self) -> List[Attribute]:
        """
        Getting the attributes of the object
        """
        if len(self.generalizations) == 0:
            return self.all_attributes
        else:
            return self.all_attributes + self.generalizations[0].attributes

    def __lt__(self, other):
        return self.object_id < other.object_id

    def __str__(self):
        return self.name + " " + str(self.object_id)

    @property
    def property_names(self) -> Generator[str]:
        for attr in sorted(self.object_attributes):
            yield attr.name

    @property
    def description(self) -> str:
        if self.definition:
            return self.definition.strip()
        elif self.note:
            return self.note.strip()
        else:
            return ""


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Package(Object):
    package_id: Optional[int] = field(
        metadata=config(field_name="Package_ID"), default=None
    )
    package_name: Optional[str] = field(default="")
    parent_id: Optional[int] = field(
        metadata=config(field_name="Parent_ID"), default=None
    )
    created_date: Optional[datetime] = field(
        metadata=config(
            field_name="CreatedDate", encoder=encode_date, decoder=decode_date
        ),
        default=None,
    )
    modified_date: Optional[datetime] = field(
        metadata=config(
            field_name="ModifiedDate", encoder=encode_date, decoder=decode_date
        ),
        default=None,
    )
    is_controlled: Optional[bool] = field(
        metadata=config(
            field_name="IsControlled", encoder=encode_flag, decoder=decode_flag
        ),
        default=False,
    )
    protected: Optional[bool] = field(
        metadata=config(
            field_name="Protected", encoder=encode_flag, decoder=decode_flag
        ),
        default=False,
    )
    use_dtd: Optional[bool] = field(
        metadata=config(field_name="UseDTD", encoder=encode_flag, decoder=decode_flag),
        default=False,
    )
    log_xml: Optional[bool] = field(
        metadata=config(field_name="LogXML", encoder=encode_flag, decoder=decode_flag),
        default=False,
    )
    batch_save: Optional[bool] = field(
        metadata=config(
            field_name="BatchSave", encoder=encode_flag, decoder=decode_flag
        ),
        default=False,
    )
    batch_load: Optional[bool] = field(
        metadata=config(
            field_name="BatchLoad", encoder=encode_flag, decoder=decode_flag
        ),
        default=False,
    )
    version: Optional[str] = field(metadata=config(field_name="Version"), default="")
    last_save_date: Optional[datetime] = field(
        metadata=config(
            field_name="LastSaveDate", encoder=encode_date, decoder=decode_date
        ),
        default=None,
    )
    last_load_date: Optional[datetime] = field(
        metadata=config(
            field_name="LastLoadDate", encoder=encode_date, decoder=decode_date
        ),
        default=None,
    )
    package_flags: Optional[str] = field(default_factory=list)
    objects: List[Object] = field(default_factory=list)
    parent: Optional[Package] = field(default=None, init=False)
    diagram_id: Optional[int] = field(
        metadata=config(field_name="Diagram_ID"), default=None
    )

    def merge(self, data: Package):
        """
        Merge the data into the package
        """
        self.package_id = data.package_id
        self.package_name = data.name
        self.parent_id = data.parent_id
        self.created_date = decode_date(data.created_date)
        self.modified_date = decode_date(data.modified_date)
        self.is_controlled = decode_flag(data.is_controlled)
        self.last_load_date = decode_date(data.last_load_date)
        self.last_save_date = decode_date(data.last_save_date)
        self.protected = decode_flag(data.protected)
        self.use_dtd = decode_flag(data.use_dtd)
        self.log_xml = decode_flag(data.log_xml)
        self.batch_save = decode_flag(data.batch_save)
        self.batch_load = decode_flag(data.batch_load)
        self.package_flags = data.package_flags.split(";") if data.package_flags else []

    @property
    def id(self):
        return self.package_id

    @property
    def path(self) -> str:
        return (
            self.parent_package.path + "." + self.name
            if self.parent_package
            else self.name
        )


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Class(Object):
    pass

    def get_attribute(self, attribute_name: str) -> Optional[Attribute | Connector]:
        for attr in self.all_attributes:
            if attr.name == attribute_name:
                return attr
        return None


@dataclass
class EnumeratedValue:
    """
    Represents an element in the EnumeratedValue Set
    """

    label: str
    "Concept Code"
    code: str
    url: Optional[str] = None
    submission_value: Optional[str] = None
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = field(default=None)
    labels: List[str] = field(default_factory=list)


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Enumeration(Object):
    """
    These represent extensions for the USDM Use case
    """

    name: Optional[str] = None
    code: Optional[str] = None
    datatype: Optional[str] = None
    url: Optional[str] = None
    submission_value: Optional[str] = None
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = field(default=None)
    values: List[EnumeratedValue] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    def add_value(self, value: EnumeratedValue):
        self.values.append(value)

    def add_synonym(self, value: str):
        self.synonyms.append(value) if value not in self.synonyms else None

    def add_definition(self, value: str):
        self.definition = value

    @property
    def prefixed_url(self) -> str:
        if self.url:
            return self.url
        else:
            return f"ncit:{self.code}"

    @property
    def enumerated_values(self) -> List[str]:
        for attr in self.object_attributes:
            yield attr.name


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Note(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Boundary(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Text(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Artifact(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class State(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class StateNode(Object):
    pass


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class ObjectProperty:
    property_id: int = field(metadata=config(field_name="PropertyID"))
    object_id: int = field(metadata=config(field_name="Object_ID"))
    property_name: str = field(metadata=config(field_name="Property"))
    ea_guid: str = field(metadata=config(field_name="ea_guid"))
    property_value: str = field(metadata=config(field_name="Value"), default="")
