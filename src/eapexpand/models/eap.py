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
    """
    Some discussion about subsetting the document into diagrams
    """
    def __init__(self, idee: int, name: str, diagram_type: str, version: str):
        self.id = idee
        self.name = name
        self._type = diagram_type
        self._version = version
        self._objects = {}

    def add_object(self, sequence: int, model_object: Object) -> None:
        self._objects[sequence] = model_object


class Document:
    """
    The `Document` class represents a structured document containing various elements 
    such as packages, objects, diagrams, and metadata. It provides methods and properties 
    to access, manipulate, and query these elements.
    Attributes:
        name (str): The name of the document.
        prefix (str): The prefix associated with the document.
        packages (List[Package]): A list of package objects in the document.
        objects (List[Object]): A list of objects in the document.
        diagrams (List[Diagram]): A list of diagrams in the document.
    Properties:
        version (Optional[str]): The version of the document.
        prefixes (Dict[str, str]): A dictionary of prefixes and their associated URIs.
        description (Optional[str]): A description of the document.
        root_item (Optional[str]): The root item of the document.
        prefix (str): The prefix associated with the document.
        diagrams (List[Diagram]): A list of diagrams in the document.
        packages (List[Object]): A list of package objects in the document.
        objects (List[Object]): A sorted list of objects in the document.
        attributes (List[Attribute]): A list of attributes in the document.
        connectors (List[Connector]): A list of connectors in the document.
        classes (List[Object]): A list of class objects in the document.
        states (List[Object]): A list of state objects in the document.
        state_nodes (List[Object]): A list of state nodes in the document.
        used_types (List[str]): A list of unique types used in the document.
    Methods:
        add_prefix(prefix: str, uri: str) -> None:
            Adds a prefix and its associated URI to the document.
        get_object(object_id: int) -> Optional[Object]:
            Retrieves an object by its ID.
        get_class_by_name(name: str) -> Optional[Class]:
            Retrieves a class object by its name.
        merge_definitions(definitions: Dict[str, str]) -> None:
            Merges the provided definitions into the document, updating objects, 
            attributes, and connectors with matching names.
    """
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
    """
    DataType class represents the structure and metadata of a data type.

    Attributes:
        id (int): The unique identifier for the data type, mapped to "DatatypeID".
        datatype_type (str): The type of the data type, mapped to "Type".
        size (Optional[int]): The size of the data type, mapped to "Size". Defaults to None.
        max_prec (Optional[int]): The maximum precision of the data type, mapped to "MaxPrec". Defaults to None.
        max_scale (Optional[int]): The maximum scale of the data type, mapped to "MaxScale". Defaults to None.
        default_len (Optional[int]): The default length of the data type, mapped to "DefaultLen". Defaults to None.
        default_prec (Optional[int]): The default precision of the data type, mapped to "DefaultPrec". Defaults to None.
        default_scale (Optional[int]): The default scale of the data type, mapped to "DefaultScale". Defaults to None.
        user (Optional[int]): The user associated with the data type, mapped to "User". Defaults to None.
        generic_type (Optional[str]): The generic type of the data type, mapped to "GenericType". Defaults to an empty string.
        product_name (Optional[str]): The product name associated with the data type, mapped to "Product_Name". Defaults to an empty string.
        datatype (Optional[str]): The name of the data type, mapped to "Datatype". Defaults to an empty string.
        max_len (Optional[int]): The maximum length of the data type, mapped to "MaxLen". Defaults to None.
    """
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
    Connector class represents a model for a connector object with various attributes 
    and properties to define its characteristics and relationships.

    Attributes:
        connector_id (Optional[int]): Unique identifier for the connector.
        connector_type (Optional[str]): Type of the connector.
        start_object_id (Optional[int]): ID of the starting object.
        end_object_id (Optional[int]): ID of the ending object.
        start_edge (Optional[int]): Starting edge of the connector.
        end_edge (Optional[int]): Ending edge of the connector.
        seq_no (Optional[int]): Sequence number of the connector.
        head_style (Optional[int]): Style of the head of the connector.
        line_style (Optional[int]): Style of the line of the connector.
        route_style (Optional[int]): Routing style of the connector.
        is_bold (Optional[int]): Indicates if the connector is bold.
        line_color (Optional[int]): Color of the connector line.
        diagram_id (Optional[int]): ID of the diagram associated with the connector.
        virtual_inheritance (Optional[str]): Virtual inheritance information.
        ea_guid (Optional[str]): GUID of the connector.
        is_root (Optional[bool]): Indicates if the connector is a root.
        is_leaf (Optional[bool]): Indicates if the connector is a leaf.
        is_spec (Optional[bool]): Indicates if the connector is a specification.
        is_signal (Optional[bool]): Indicates if the connector is a signal.
        is_stimulus (Optional[bool]): Indicates if the connector is a stimulus.
        name (Optional[str]): Name of the connector.
        dest_card (Optional[str]): Destination cardinality.
        source_card (Optional[str]): Source cardinality.
        direction (Optional[str]): Direction of the connector.
        source_access (Optional[str]): Source access information.
        dest_access (Optional[str]): Destination access information.
        dest_element (Optional[str]): Destination element information.
        source_containment (Optional[str]): Source containment information.
        source_is_aggregate (Optional[int]): Indicates if the source is aggregate.
        source_is_ordered (Optional[int]): Indicates if the source is ordered.
        source_role (Optional[str]): Role of the source.
        dest_role (Optional[str]): Role of the destination.
        dest_containment (Optional[str]): Destination containment information.
        dest_is_aggregate (Optional[int]): Indicates if the destination is aggregate.
        dest_is_ordered (Optional[int]): Indicates if the destination is ordered.
        top_end_label (Optional[str]): Label for the top end of the connector.
        source_changeable (Optional[str]): Indicates if the source is changeable.
        dest_changeable (Optional[str]): Indicates if the destination is changeable.
        source_ts (Optional[str]): Timestamp for the source.
        dest_ts (Optional[str]): Timestamp for the destination.
        target2 (Optional[int]): Secondary target information.
        source_style (Optional[str]): Style of the source.
        dest_style (Optional[str]): Style of the destination.
        source_is_navigable (Optional[int]): Indicates if the source is navigable.
        dest_is_navigable (Optional[int]): Indicates if the destination is navigable.
        package_data_1 (Optional[str]): Package data field 1.
        package_data_2 (Optional[str]): Package data field 2.
        package_data_3 (Optional[str]): Package data field 3.
        package_data_4 (Optional[str]): Package data field 4.
        package_data_5 (Optional[str]): Package data field 5.
        source_object (Optional[Object]): Source object associated with the connector.
        target_object (Optional[Object]): Target object associated with the connector.
        definition (Optional[str]): Definition of the connector.
        enumeration (Optional[Enumeration]): Enumerated value associated with the connector.
        reference_url (Optional[str]): Reference URL (e.g., NCI code/URL).
        preferred_term (Optional[str]): Preferred term for the connector.
        synonyms (Optional[List[str]]): List of synonyms for the connector.
        codelist (Optional[Any]): Codelist associated with the connector.
        aliased_type (Optional[str]): Aliased type of the connector.
    Properties:
        target_object_name (str): Name of the target object, if available.
        source_object_name (str): Name of the source object, if available.
        id (Optional[int]): Returns the connector ID.
        attributes (List[Attribute]): Attributes of the target object, if available.
        optional (Optional[bool]): Indicates if the destination cardinality starts with "0".
        multivalued (Optional[bool]): Indicates if the destination cardinality ends with "*".
        description (Optional[str]): Returns the definition of the connector.
        attribute_type (Optional[str]): Returns the aliased type or the name of the target object.
        cardinality (Optional[str]): Returns the destination cardinality.
    Methods:
        optional.setter: Sets the optional property by modifying the destination cardinality.
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
    # aliased type
    aliased_type: Optional[str] = field(default=None)

    @property
    def target_object_name(self):
        return self.target_object.name if self.target_object else ""
    
    @property
    def source_object_name(self):
        return self.target_object.name if self.target_object else ""
    
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

    @optional.setter
    def optional(self, value: bool):
        if value:
            self.dest_card = "0" + self.dest_card[1:]
        else:
            self.dest_card = "1" + self.dest_card[1:]

    @property
    def multivalued(self) -> Optional[bool]:
        return self.dest_card.endswith("*")

    @property
    def description(self):
        return self.definition

    @property
    def attribute_type(self):
        return self.aliased_type if self.aliased_type else self.target_object.name

    @property
    def cardinality(self):
        return self.dest_card

    @property
    def range(self):
        if self.target_object:
            return self.target_object.name
        else:
            return None
        
@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Attribute:
    """
    The `Attribute` class represents an attribute of an object in the EAP (Enterprise Architect Project) model.

    Attributes:
        object_id (Optional[int]): The unique identifier of the object.
        name (Optional[str]): The name of the attribute.
        scope (Optional[str]): The scope of the attribute.
        containment (Optional[str]): The containment type of the attribute.
        is_static (Optional[bool]): Indicates if the attribute is static.
        is_collection (Optional[bool]): Indicates if the attribute is a collection.
        is_ordered (Optional[bool]): Indicates if the attribute is ordered.
        allow_duplicates (Optional[bool]): Indicates if duplicates are allowed.
        lower_bound (Optional[str]): The lower bound of the attribute's cardinality.
        upper_bound (Optional[str]): The upper bound of the attribute's cardinality.
        derived (Optional[bool]): Indicates if the attribute is derived.
        id (Optional[int]): The unique identifier of the attribute.
        pos (Optional[int]): The position of the attribute.
        length (Optional[int]): The length of the attribute.
        const (Optional[bool]): Indicates if the attribute is constant.
        attribute_type (Optional[str]): The type of the attribute.
        classifier_id (Optional[int]): The identifier of the classifier associated with the attribute.
        attribute_stereotype (Optional[str]): The stereotype of the attribute.
        ea_guid (Optional[str]): The globally unique identifier (GUID) of the attribute in EA.
        attribute_classifier (Optional[Object]): The classifier object associated with the attribute.
        default (Optional[str]): The default value of the attribute.
        connector (Optional[Connector]): The connector associated with the attribute.
        note (Optional[str]): Additional notes or comments about the attribute.
        definition (Optional[str]): The definition of the attribute, if supplied.
        enumeration (Optional[Enumeration]): The enumerated value associated with the attribute.
        reference_url (Optional[str]): A reference URL, e.g., NCI code/URL.
        preferred_term (Optional[str]): The preferred term for the attribute.
        synonyms (Optional[List[str]]): A list of synonyms for the attribute.
        codelist (Optional[Any]): A codelist associated with the attribute.
        api_attribute (Optional[str]): API-specific attributes.

    Methods:
        __lt__(self, other): Compares the position (`pos`) of this attribute with another attribute.
        cardinality (property): Returns the cardinality of the attribute, defaulting to "1..1" if not specified.
        description (property): Returns a description of the attribute, prioritizing `definition` over `note`.
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
        elif self.lower_bound and self.upper_bound:
            # attribute cardinality
            return f"{self.lower_bound}..{self.upper_bound}"
        return "1..1"

    @property
    def description(self) -> str:
        if self.definition:
            return self.definition.strip()
        elif self.note:
            return self.note.strip()
        else:
            return ""

    @property
    def range(self) -> str:
        """
        Getting the range of the attribute
        """
        if self.attribute_type:
            return self.attribute_type
        else:
            return ""

@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Object:
    """
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
    """
    Package class represents a data model for handling package-related information.

    Attributes:
        package_id (Optional[int]): Unique identifier for the package.
        package_name (Optional[str]): Name of the package.
        parent_id (Optional[int]): Identifier of the parent package.
        created_date (Optional[datetime]): Date when the package was created.
        modified_date (Optional[datetime]): Date when the package was last modified.
        is_controlled (Optional[bool]): Indicates if the package is controlled.
        protected (Optional[bool]): Indicates if the package is protected.
        use_dtd (Optional[bool]): Indicates if DTD is used.
        log_xml (Optional[bool]): Indicates if XML logging is enabled.
        batch_save (Optional[bool]): Indicates if batch saving is enabled.
        batch_load (Optional[bool]): Indicates if batch loading is enabled.
        version (Optional[str]): Version of the package.
        last_save_date (Optional[datetime]): Date when the package was last saved.
        last_load_date (Optional[datetime]): Date when the package was last loaded.
        package_flags (Optional[str]): Flags associated with the package.
        objects (List[Object]): List of objects associated with the package.
        parent (Optional[Package]): Parent package instance.
        diagram_id (Optional[int]): Identifier for the associated diagram.

    Methods:
        merge(data: Package):
            Merges the data from another Package instance into the current instance.

        id:
            Returns the unique identifier of the package.

        path:
            Returns the hierarchical path of the package, including its parent package if applicable.
    """
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
    Enumeration class represents extensions for the USDM (Unified Study Data Model) use case.

    Attributes:
        name (Optional[str]): The name of the enumeration.
        code (Optional[str]): The code associated with the enumeration.
        datatype (Optional[str]): The datatype of the enumeration.
        url (Optional[str]): The URL associated with the enumeration.
        submission_value (Optional[str]): The value submitted for the enumeration.
        synonyms (Optional[List[str]]): A list of synonyms for the enumeration.
        definition (Optional[str]): The definition of the enumeration.
        values (List[EnumeratedValue]): A list of enumerated values associated with the enumeration.
        labels (List[str]): A list of labels associated with the enumeration.

    Methods:
        add_value(value: EnumeratedValue):
            Adds an enumerated value to the `values` list.

        add_synonym(value: str):
            Adds a synonym to the `synonyms` list if it is not already present.

        add_definition(value: str):
            Sets the definition of the enumeration.

        prefixed_url -> str:
            Returns the URL if it exists; otherwise, returns a prefixed string using the code.

        enumerated_values -> Generator[str]:
            A generator that yields the names of object attributes.
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
    def enumerated_values(self) -> Generator[str]:
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

