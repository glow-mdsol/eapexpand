from __future__ import annotations
from datetime import datetime

from dataclasses import dataclass, field
from typing import List, Optional
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
class Package:
    package_id: int = field(metadata=config(field_name="Package_ID"))
    name: str = field(metadata=config(field_name="Name"))
    parent_id: int = field(metadata=config(field_name="Parent_ID"))
    created_date: datetime = field(
        metadata=config(
            field_name="CreatedDate", encoder=encode_date, decoder=decode_date
        )
    )
    modified_date: datetime = field(
        metadata=config(
            field_name="ModifiedDate", encoder=encode_date, decoder=decode_date
        )
    )
    ea_guid: str = field(metadata=config(field_name="ea_guid"))
    is_controlled: bool = field(metadata=config(field_name="IsControlled"))
    protected: bool = field(
        metadata=config(
            field_name="Protected", encoder=encode_flag, decoder=decode_flag
        )
    )
    use_dtd: bool = field(
        metadata=config(field_name="UseDTD", encoder=encode_flag, decoder=decode_flag)
    )
    log_xml: bool = field(
        metadata=config(field_name="LogXML", encoder=encode_flag, decoder=decode_flag)
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
    objects: List[Object] = field(default_factory=list)

    @property
    def id(self):
        return self.package_id


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
    ea_guid: str
    is_root: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_leaf: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_spec: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_signal: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_stimulus: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
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

    object_id: int = field(metadata=config(field_name="Object_ID"))
    name: str = field(metadata=config(field_name="Name"))
    scope: str
    containment: str
    is_static: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_collection: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag)
    )
    is_ordered: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    allow_duplicates: bool = field(
        metadata=config(encoder=encode_flag, decoder=decode_flag)
    )
    lower_bound: str
    upper_bound: str
    derived: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    id: int = field(metadata=config(field_name="ID"))
    pos: int
    length: int
    const: bool
    attribute_type: Optional[str] = field(
        metadata=config(field_name="Type"), default=""
    )
    classifier_id: Optional[int] = field(
        metadata=config(field_name="Classifier"), default=-1
    )
    attribute_stereotype: Optional[str] = field(
        metadata=config(field_name="Stereotype"), default=""
    )
    attribute_classifier: Optional[Object] = None

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

    object_id: int = field(metadata=config(field_name="Object_ID"))
    object_type: str = field(metadata=config(field_name="Object_Type"))
    diagram_id: int = field(metadata=config(field_name="Diagram_ID"))
    package_id: int = field(metadata=config(field_name="Package_ID"))
    ntype: int = field(metadata=config(field_name="NType"))
    complexity: str
    effort: int
    created_date: datetime = field(
        metadata=config(encoder=encode_date, decoder=decode_date)
    )
    modified_date: datetime = field(
        metadata=config(encoder=encode_date, decoder=decode_date)
    )
    scope: str
    ea_guid: str
    parent_id: int = field(metadata=config(field_name="ParentID"))
    is_root: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_leaf: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_spec: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    is_active: bool = field(metadata=config(encoder=encode_flag, decoder=decode_flag))
    classifier: Optional[int] = 0
    phase: Optional[str] = ""
    name: Optional[str] = ""
    author: Optional[str] = ""
    version: Optional[str] = ""
    note: Optional[str] = ""
    outgoing_connections: Optional[List[Connector]] = field(default_factory=list)
    incoming_connections: Optional[List[Connector]] = field(default_factory=list)
    package: Optional[Package] = None

    def __str__(self):
        return self.name + " " + str(self.object_id)


def load_packages(filename):
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _package = Package.from_json(line)
            data[_package.package_id] = _package
    return data


def load_objects(filename: str) -> Dict[int, Object]:
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _object = Object.from_json(line)
            data[_object.object_id] = _object
    return data


def load_attributes(filename: str) -> Dict[int, Attribute]:
    data = {}
    with open(filename, "r") as f:
        for line in f:
            # object id -> classifier
            try:
                _attr = Attribute.from_json(line)
                if _attr.id in data:
                    print(f"Warning - duplicated object id: {_attr.id}")
                data[_attr.id] = _attr
            except AttributeError as exc:
                print(f"Error: {exc}", line)
            except KeyError as exc:
                print(f"Error: {exc}", line)
            except TypeError as exc:
                print(f"Error: {exc}", line)    
    return data


def load_connectors(filename) -> Dict[int, Connector]:
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _connector = Connector.from_json(line)
            data[_connector.connector_id] = _connector
    return data
