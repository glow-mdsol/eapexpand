from __future__ import annotations
import re

from openpyxl import load_workbook, Workbook
from openpyxl.cell.cell import Cell
from dataclasses import dataclass, field
from typing import List, Optional
import os
from .unpkt import load_expanded_dir


def _f(cell: Cell):
    """
    Coerce empty cells to empty strings
    """
    if cell.value is None:
        return ""
    return str(cell.value)


@dataclass
class PermissibleValue:
    project: str
    entity: str
    attribute: str
    codelist_c_code: str
    concept_c_code: str
    preferred_term: str
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row[6]:
            synonyms = [s.strip() for s in row[6].split(";")]
        else:
            synonyms = []
        return cls(
            project=row[0],
            entity=row[1],
            attribute=row[2],
            codelist_c_code=row[3],
            concept_c_code=row[4],
            preferred_term=row[5],
            synonyms=synonyms,
            definition=row[7],
        )


@dataclass
class Entity:
    entity_name: str
    logical_data_model_name: str
    nci_c_code: Optional[str] = None
    preferred_term: Optional[str] = None
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = None
    has_value_list: Optional[bool] = False
    value_list_description: Optional[str] = None
    external_value_list: Optional[str] = None
    attributes: Optional[List[Entity]] = field(default_factory=list)
    relationships: Optional[List[str]] = field(default_factory=list)
    codelist_c_code: Optional[str] = None
    codelist_items: Optional[List[PermissibleValue]] = field(default_factory=list)
    role: Optional[str] = None

    def get_attribute(self, attribute_name: str):
        for attr in self.attributes:
            if attr.logical_data_model_name == attribute_name:
                return attr
        return None
    
    @classmethod
    def from_row(cls, row):
        if row[6]:
            synonyms = [s.strip() for s in row[6].split(";")]
        else:
            synonyms = []
        entity = cls(
            entity_name=row[1],
            logical_data_model_name=row[3],
            nci_c_code=row[4],
            preferred_term=row[5],
            synonyms=synonyms,
            definition=row[7],
        )
        has_value_list = row[8]
        if has_value_list:
            if has_value_list.startswith("Y"):
                entity.has_value_list = True
                source = re.compile(r'Y \((.*)\)$')
                m = source.match(row[8])
                if m:
                    entity.value_list_description = m.group(1)
                    if entity.value_list_description.lower().startswith("point out"):
                        entity.external_value_list = True
                    else:
                        entity.external_value_list = False
                        entity.codelist_c_code = entity.value_list_description
                else:
                    raise ValueError(f"Unable to parse value list description: {row[8]}")
            elif has_value_list.startswith("N"):
                entity.has_value_list = False
        return entity


def load_usdm_ct(filename: str):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    wbk = load_workbook(filename, read_only=True)
    _ent_attr = wbk["DDF Entities&Attributes"]
    entities = {}
    for row in _ent_attr.iter_rows(min_row=2, values_only=True):
        _name = row[1]
        _role = row[2]
        if _role == "Entity":
            if not _name in entities:
                entities[_name] = Entity.from_row(row)
        elif _role == "Relationship":
            entities[_name].relationships.append(row[3])
        elif _role == "Attribute":
            entities[_name].attributes.append(Entity.from_row(row))
        else:
            raise ValueError(f"Unknown entity type: {row[2]}")
    _value_sets = wbk["DDF valid value sets"]
    for row in _value_sets.iter_rows(min_row=7, values_only=True):
        # get the entity
        codeset = PermissibleValue.from_row(row)
        _entity = entities[row[1]]
        _attribute = row[2]
        if _attribute == "encounterContactMode":
            print("WARNING Remap encounterContactMode to encounterContactModes")
            _attribute = "encounterContactModes"
        _attr = _entity.get_attribute(_attribute)
        if _attr is None:
            raise ValueError(f"Attribute {row[2]} not found in entity {_entity.entity_name} ")
        if _attr.codelist_c_code is None:
            _attr.codelist_c_code = codeset.codelist_c_code
        _attr.codelist_items.append(codeset)
    return entities


def generate(
    name: str,
    objects: dict,
    attributes: dict,
    connectors: dict,
    ct_content: dict,
    output_dir: Optional[str] = "output",
):
    """
    Generates the Excel Representation of the model
    :param name: The name of the model - guides what the output file is called
    """
    doc = Workbook()
    sheet = doc.active
    sheet.title = "Objects"
    for idx, column in enumerate(
        ("Class", "Attribute", "Type", "Cardinality", "Class Note", "NCI C-code", "Preferred term", "Definition", "Codelist", "External Codelist")
    ):
        sheet.cell(row=1, column=idx + 1).value = column
    row_num = 2
    for obj in objects.values():
        _output = {}
        if obj.object_type == "Class":
            _object_id = obj.object_id
            _ref = ct_content.get(obj.name) # type: Entity
            if _ref is None:
                print("WARNING: Reference not found for " + obj.name)             
            _attributes = sorted(
                [
                    attributes[attr_id]
                    for attr_id in attributes
                    if attributes[attr_id].object_id == _object_id
                ]
            )
            # write the entity
            sheet.cell(row=row_num, column=1).value = obj.name
            if _ref:
                if _ref.definition:
                    sheet.cell(row=row_num, column=8).value = _ref.definition
                if _ref.nci_c_code:
                    sheet.cell(row=row_num, column=6).value = _ref.nci_c_code
                if _ref.preferred_term:
                    sheet.cell(row=row_num, column=7).value = _ref.preferred_term
            else:
                print(f"Reference not found for {obj.name}")
            if obj.note:
                sheet.cell(row=row_num, column=5).value = str(obj.note)
            row_num += 1

            for _attribute in _attributes:
                attrib = _output.setdefault(_attribute.name, {})
                if not attrib:
                    attrib = dict(
                        attribute_name=_attribute.name,
                        attribute_type=_attribute.attribute_type,
                        attribute_cardinality=_attribute.lower_bound
                        + ".."
                        + _attribute.upper_bound,
                    )
                    if _ref:
                        _attr_ref = _ref.get_attribute(_attribute.name)
                        if _attr_ref:
                            attrib["definition"] = _attr_ref.definition
                            attrib["c_code"] = _attr_ref.nci_c_code
                            attrib["pref_term"] = _attr_ref.preferred_term
                            if _attr_ref.has_value_list:
                                if _attr_ref.external_value_list:
                                    attrib["external_value_list"] = _attr_ref.value_list_description
                                else:
                                    attrib["codelist"] = _attr_ref.value_list_description or ""
                _output[_attribute.name] = attrib
            connections = [
                connectors[cid]
                for cid in connectors
                if connectors[cid].start_object_id == _object_id
            ]
            for connection in connections:
                if connection.connector_type not in ("Association", "Generalization"):
                    continue
                attrib = _output.setdefault(connection.name, {})
                if not attrib:
                    attrib = dict(
                        attribute_name=connection.name,
                        attribute_type=objects[connection.end_object_id].name,
                        attribute_cardinality=connection.source_card,
                        note=None,
                    )
                _output[connection.name] = attrib
            for offset, attrib in enumerate(_output.values()):
                sheet.cell(row=row_num, column=1).value = obj.name
                sheet.cell(row=row_num, column=2).value = attrib["attribute_name"]
                sheet.cell(row=row_num, column=3).value = attrib["attribute_type"]
                sheet.cell(row=row_num, column=4).value = attrib[
                    "attribute_cardinality"
                ]
                sheet.cell(row=row_num, column=6).value = attrib.get("c_code", "")
                sheet.cell(row=row_num, column=7).value = attrib.get("pref_term", "")
                sheet.cell(row=row_num, column=8).value = attrib.get("definition", "")
                sheet.cell(row=row_num, column=9).value = attrib.get("codelist", "")
                sheet.cell(row=row_num, column=10).value = attrib.get("external_value_list", "")
                row_num += 1
    # create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    fname = os.path.join(output_dir, f"{name}.xlsx")
    doc.save(fname)
    print(f"Generated USDM Excel file: {fname}")


def main_usdm(source_dir: str, controlled_term: str, output_dir: str):
    objects, attributes, connectors = load_expanded_dir(source_dir=source_dir)
    ct_content = load_usdm_ct(controlled_term)
    name = os.path.basename(os.path.dirname(source_dir)) if source_dir.endswith("/") else os.path.basename(source_dir)
    generate(name, objects, attributes, connectors, ct_content, output_dir)