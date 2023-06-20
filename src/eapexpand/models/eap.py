from __future__ import annotations
from datetime import datetime

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from dataclasses_json import dataclass_json, LetterCase, config


"""
Wrapper dataclasses for the Objects in the EA file
"""


DATE_FORMAT = "%m/%d/%y %H:%M:%S"


def decode_date(date_str: Optional[str]) -> datetime:
    """
    Decodes a date string into a datetime object
    """
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


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Connector:
    """
    Represents a connector in the EAP model
    """

    connector_id: int = field(metadata=config(field_name="Connector_ID"))
    connector_type: str = field(metadata=config(field_name="Connector_Type"))
    start_object_id: int = field(metadata=config(field_name="Start_Object_ID"))
    end_object_id: int = field(metadata=config(field_name="End_Object_ID"))
    start_edge: int = field(metadata=config(field_name="Start_Edge"))
    end_edge: int = field(metadata=config(field_name="End_Edge"))
    seq_no: int
    head_style: int
    line_style: int
    route_style: int
    is_bold: int
    line_color: int
    virtual_inheritance: str
    diagram_id: int = field(metadata=config(field_name="DiagramID"))
    ea_guid: Optional[str] = field(metadata=config(field_name="ea_guid"), default=None)
    is_root: Optional[bool] = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_leaf: Optional[bool] = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_spec: Optional[bool] = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_signal: Optional[bool] = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_stimulus: Optional[bool] = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
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

    @property
    def id(self):
        return self.connector_id


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
    connector: Optional[Connector] = None
    notes: Optional[str] = field(metadata=config(field_name="Notes"), default="")

    def __lt__(self, other):
        return self.pos < other.pos
    
    @property
    def cardinality(self):
        if self.connector:
            return self.connector.dest_card if self.connector.dest_card else "1..1"
        return "1..1"

    def __lt__(self, other):
        return self.pos < other.pos

    def __gt__(self, other):
        return self.pos < other.pos


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
    complexity: Optional[str] = field(metadata=config(field_name="Complexity"), default="")
    effort: Optional[int] = field(metadata=config(field_name="Effort"), default=0)
    created_date: Optional[datetime] = field(
        metadata=config(encoder=encode_date, decoder=decode_date),
        default=None
    )
    modified_date: Optional[datetime] = field(
        metadata=config(encoder=encode_date, decoder=decode_date),
        default=None,
    )
    parent_id: int = field(metadata=config(field_name="ParentID"), default=-1)
    is_root: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_leaf: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_spec: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    is_active: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag), default=False)
    classifier: Optional[int] = 0
    phase: Optional[str] = ""
    name: Optional[str] = ""
    author: Optional[str] = ""
    version: Optional[str] = ""
    note: Optional[str] = ""
    ea_guid: Optional[str] = field(metadata=config(field_name="ea_guid"), default=None)
    outgoing_connections: Optional[List[Connector]] = field(default_factory=list)
    incoming_connections: Optional[List[Connector]] = field(default_factory=list)
    generalizations: Optional[List[Object]] = field(default_factory=list)
    specializations: Optional[List[Object]] = field(default_factory=list)
    attributes: Optional[List[Attribute]] = field(default_factory=list)
    properties: Optional[List[ObjectProperty]] = field(default_factory=list)
    connectors: Optional[List[Connector]] = field(default_factory=list)

    def __str__(self):
        return self.name + " " + str(self.object_id)

    @property
    def property_names(self) -> List[str]:
        for attr in sorted(self.attributes):
            yield attr.name

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
        default=False
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
    parent_package: Optional[Package] = field(default=None, init=False)

    def merge(self, data: Dict[str, Any]):
        """
        Merge the data into the package
        """
        self.package_id = data.get("Package_ID")
        self.package_name = data.get("Name")
        self.parent_id = data.get("Parent_ID")
        self.created_date = decode_date(data.get("CreatedDate"))
        self.modified_date = decode_date(data.get("ModifiedDate"))
        self.is_controlled = decode_flag(data.get("IsControlled"))
        self.last_load_date = decode_date(data.get("LastLoadDate"))
        self.last_save_date = decode_date(data.get("LastSaveDate"))
        self.protected = decode_flag(data.get("Protected"))
        self.use_dtd = decode_flag(data.get("UseDTD"))
        self.log_xml = decode_flag(data.get("LogXML"))
        self.batch_save = decode_flag(data.get("BatchSave"))
        self.batch_load = decode_flag(data.get("BatchLoad"))
        self.package_flags = data.get("PackageFlags", "").split(";") if data.get("PackageFlags") else []

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


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Enumeration(Object):
    pass

    @property
    def enumerated_values(self) -> List[str]:
        for attr in self.attributes:
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


