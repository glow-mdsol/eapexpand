

from dataclasses import dataclass, field
import os

from openpyxl import Workbook
from dataclasses_json import dataclass_json, LetterCase, config
from datetime import datetime
from typing import Optional, List

DATE_FORMAT = "%m/%d/%y %H:%M:%S"


def decode_date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)


def encode_date(date):
    return date.strftime(DATE_FORMAT)


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
    is_root: int
    is_leaf: int
    is_spec: int
    is_signal: int
    is_stimulus: int
    name: Optional[str] = ""
    dest_card: Optional[str] = field(metadata=config(field_name="DestCard"), default="")
    source_card: Optional[str] = field(metadata=config(field_name="SourceCard"), default="")
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
    top_end_label: Optional[str] = field(metadata=config(field_name="Top_End_Label"), default="")
    source_changeable: Optional[str] = ""
    dest_changeable: Optional[str] = ""
    source_ts: Optional[str] = field(metadata=config(field_name="SourceTS"), default="")
    dest_ts: Optional[str] = field(metadata=config(field_name="DestTS"), default="")
    target2: Optional[int] = -1
    source_style: Optional[str] = ""
    dest_style: Optional[str] = ""
    source_is_navigable: Optional[int] = -1
    dest_is_navigable: Optional[int] = -1


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
    is_static: bool
    is_collection: bool
    is_ordered: bool
    allow_duplicates: bool
    lower_bound: str
    upper_bound: str
    derived: bool
    id: int = field(metadata=config(field_name="ID"))
    pos: int
    length: int
    const: bool
    attribute_type: str = field(metadata=config(field_name="Type"))
    classifier: Optional[int] = 0

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
        metadata=config(
            encoder= encode_date,
            decoder= decode_date
        ))
    modified_date: datetime = field(
        metadata=config(
            encoder= encode_date,
            decoder= decode_date
        ))
    scope: str
    ea_guid: str
    parent_id: int = field(metadata=config(field_name="ParentID"))
    is_root: bool
    is_leaf: bool
    is_spec: bool
    is_active: bool
    classifier: Optional[int] = 0
    phase: Optional[str] = ""
    name: Optional[str] = ""
    author: Optional[str] = ""
    version: Optional[str] = ""
    note: Optional[str] = ""
    attributes: Optional[List[Attribute]] = field(default_factory=list)

    def __str__(self):
        return self.name + " " + str(self.object_id)

def load_objects(filename):
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _object = Object.from_json(line)
            data[_object.object_id] = _object
    return data

def load_attributes(filename):
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _attr = Attribute.from_json(line)
            data[_attr.id] = _attr
    return data


def load_connectors(filename):
    data = {}
    with open(filename, "r") as f:
        for line in f:
            _connector = Connector.from_json(line)
            data[_connector.connector_id] = _connector
    return data

def load(source_dir: str):
    # load the key entities
    objects = load_objects(os.path.join(source_dir, "t_object.json"))
    attributes = load_attributes(os.path.join(source_dir, "t_attribute.json"))
    connectors = load_connectors(os.path.join(source_dir, "t_connector.json"))

    # Coalesce the attributes into the objects
    for object_id, _object in objects.items():
        _object.attributes = [attributes[attr_id] for attr_id in attributes if attributes[attr_id].object_id == object_id]
        _object.attributes.sort()

    for connector_id, connector in connectors.items():
        source = objects[connector.start_object_id]
        dest = objects[connector.end_object_id]
        if connector.source_role == "source":
            source.attributes.append(Attribute(
                object_id=source.object_id,
                name=connector.top_end_label,
                scope="Private",
                containment="Not Specified",
                is_static=False,
                is_collection=False,
                is_ordered=False,
                allow_duplicates=False,
                lower_bound="1",
                upper_bound="1",
                derived=False,
                id=connector_id,
                pos=0,
                length=0,
                const=False,
                classifier=0,
                attribute_type=dest.name
            ))
        else:
            dest.attributes.append(Attribute(
                object_id=dest.object_id,
                name=connector.top_end_label,
                scope="Private",
                containment="Not Specified",
                is_static=False,
                is_collection=False,
                is_ordered=False,
                allow_duplicates=False,
                lower_bound="1",
                upper_bound="1",
                derived=False,
                id=connector_id,
                pos=0,
                length=0,
                const=False,
                classifier=0,
                attribute_type=source.name
            ))

    for object_id, _object in objects.items():
        _object.attributes.sort()
    return objects, attributes, connectors


def generate(name: str, objects: dict, attributes: dict, connectors: dict, output_dir: Optional[str] = "output"):
    """
    Generates the Excel Representation of the model
    :param name: The name of the model - guides what the output file is called
    """
    doc = Workbook()
    sheet = doc.active
    sheet.title = "Objects"
    for idx, column in enumerate(("Class", "Attribute", "Type", "Cardinality", "Class Note")):
        sheet.cell(row=1, column=idx + 1).value = column
    row_num = 2
    for obj in objects.values():
        _output = {}
        if obj.object_type == "Class":
            _object_id = obj.object_id
            _attributes = sorted([attributes[attr_id] for attr_id in attributes if attributes[attr_id].object_id == _object_id])
            for _attribute in _attributes:
                attrib = _output.setdefault(_attribute.name, {})
                if not attrib:
                    attrib = dict(attribute_name=_attribute.name, 
                    attribute_type=_attribute.attribute_type, 
                    attribute_cardinality=_attribute.lower_bound + ".." + _attribute.upper_bound
                    )
                # TODO - upsert
                _output[_attribute.name] = attrib     
                # _output[_attribute.name] = dict(name)
                #     sheet.cell(row=row_num, column=1).value = obj.name
                #     sheet.cell(row=row_num, column=2).value = _attribute.name
                #     sheet.cell(row=row_num, column=3).value = _attribute.attribute_type
                #     sheet.cell(row=row_num, column=4).value = "*" if "List" in _attribute.attribute_type else ""
                #     if _init:
                #        sheet.cell(row=row_num, column=5).value = obj.note if obj.note else ""
                #        _init = False
                #     row_num += 1
            connections = [connectors[cid] for cid in connectors if connectors[cid].start_object_id == _object_id]
            for connection in connections:
                if connection.connector_type not in  ("Association", "Generalization"):
                    continue
                attrib = _output.setdefault(connection.name, {})
                if not attrib:
                    attrib = dict(attribute_name=connection.name, 
                    attribute_type=objects[connection.end_object_id].name, 
                    attribute_cardinality=connection.source_card, 
                    note=None)
                _output[connection.name] = attrib
                # _attributes = sorted([attributes[aid] for aid in attributes if attributes[aid].object_id == _connector.end_object_id])
                # for _attribute in _attributes:
                #     attrib = _output.setdefault(_attribute.name, {})
                #     sheet.cell(row=row_num, column=1).value = obj.name
                #     sheet.cell(row=row_num, column=2).value = _attribute.name
                #     sheet.cell(row=row_num, column=3).value = _attribute.attribute_type
                #     sheet.cell(row=row_num, column=4).value = _connector.dest_card if _connector.dest_card else ""
                    # sheet.cell(row=row_num, column=5).value = _attribute.note if _attribute.note else ""
            for offset, attrib in enumerate(_output.values()):
                sheet.cell(row=row_num, column=1).value = obj.name
                sheet.cell(row=row_num, column=2).value = attrib["attribute_name"]
                sheet.cell(row=row_num, column=3).value = attrib["attribute_type"]
                sheet.cell(row=row_num, column=4).value = attrib["attribute_cardinality"]
                if offset == 0:
                    sheet.cell(row=row_num, column=5).value = obj.note if obj.note else ""
                row_num += 1
    # create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    doc.save(os.path.join(output_dir, f"{name}.xlsx"))
        
