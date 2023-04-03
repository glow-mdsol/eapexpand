from __future__ import annotations
import re

from openpyxl import load_workbook, Workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


from typing import Optional
import os

from .models.usdm_ct import CodeList, Entity, PermissibleValue
from .loader import load_expanded_dir


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
    codelists = {}
    for row in _value_sets.iter_rows(min_row=7, values_only=True):
        # get the entity
        codeset = PermissibleValue.from_row(row)
        if codeset.codelist_c_code not in codelists:
            codelists[codeset.codelist_c_code] = CodeList.from_pvalue(codeset)
        codelists[codeset.codelist_c_code].add_item(codeset)
        # get the entity
        _entity = entities[row[1]]
        # get the attribute
        _attribute = row[2]
        if _attribute == "encounterContactMode":
            print("WARNING Remap encounterContactMode to encounterContactModes")
            _attribute = "encounterContactModes"
        _attr = _entity.get_attribute(_attribute)
        if _attr is None:
            raise ValueError(
                f"Attribute {row[2]} not found in entity {_entity.entity_name} "
            )
        if _attr.codelist_c_code is None:
            _attr.codelist_c_code = codeset.codelist_c_code
        _attr.codelist_items.append(codeset)
    return entities, codelists


def generate(
    name: str,
    objects: dict,
    attributes: dict,
    connectors: dict,
    ct_content: dict,
    codelists: dict,
    output_dir: Optional[str] = "output",
):
    """
    Generates the Excel Representation of the model
    :param name: The name of the model - guides what the output file is called
    """
    # remap the code attribute model to the code list model
    doc = Workbook()
    sheet = doc.active
    sheet.title = "Core Model"
    cols = {}
    def write_cell(worksheet, row, column, value, header = False):
        columns = cols.setdefault(worksheet.title, {})
        columns[column] = max([len(value), columns.get(column, 10)])
        cols[worksheet.title] = columns
        worksheet.cell(row, column).value = value
        worksheet.cell(row, column).alignment = Alignment(wrap_text=True, vertical='top')
        if header:
            worksheet.cell(row, column).font = Font(bold=True)

    for idx, column in enumerate(
        (
            "Class",
            "Attribute",
            "Type",
            "Cardinality",
            "Class Note",
            "NCI C-code",
            "Preferred term",
            "Definition",
            "Codelist",
            "External Codelist",
        )
    ):
        write_cell(sheet, 1, idx + 1, column, True)
    row_num = 2
    for obj in objects.values():
        _output = {}
        if obj.object_type == "Class":
            _object_id = obj.object_id
            _ref = ct_content.get(obj.name)  # type: Entity
            if obj.generalizations:
                _generalization = obj.generalizations[0]
                _ref = ct_content.get(_generalization.name)
            else:
                _generalization = None
            if _ref is None:
                print("WARNING: Reference not found for " + obj.name)
            # _attributes = sorted(
            #     [
            #         attributes[attr_id]
            #         for attr_id in attributes
            #         if attributes[attr_id].object_id == _object_id
            #     ]
            # )
            # write the entity
            write_cell(sheet, row=row_num, column=1, value = obj.name)
            if _ref:
                if _ref.definition:
                    write_cell(sheet, row=row_num, column=8, value = _ref.definition)
                if _ref.nci_c_code:
                    write_cell(sheet, row=row_num, column=6, value = _ref.nci_c_code)
                if _ref.preferred_term:
                    write_cell(sheet, row=row_num, column=7, value = _ref.preferred_term)
            else:
                print(f"Reference not found for {obj.name}")
            if obj.note:
                write_cell(sheet, row=row_num, column=5, value = str(obj.note))
            row_num += 1

            for _attribute in obj.attributes:
                attrib = _output.setdefault(_attribute.name, {})
                if not attrib:
                    if _generalization and _attribute in _generalization.attributes:
                        _name = "* " + _attribute.name
                    else:
                        _name = _attribute.name
                    attrib = dict(
                        attribute_name=_name,
                        attribute_type=_attribute.attribute_type,
                        attribute_cardinality=_attribute.cardinality
                    )
                    if _ref:
                        _attr_ref = _ref.get_attribute(_attribute.name)
                        if _attr_ref:
                            attrib["definition"] = _attr_ref.definition
                            attrib["c_code"] = _attr_ref.nci_c_code
                            attrib["pref_term"] = _attr_ref.preferred_term
                            if _attr_ref.has_value_list:
                                if _attr_ref.external_value_list:
                                    attrib[
                                        "external_value_list"
                                    ] = _attr_ref.value_list_description
                                else:
                                    attrib["codelist"] = (
                                        _attr_ref.value_list_description or ""
                                    )
                _output[_attribute.name] = attrib
            # connections = [
            #     connectors[cid]
            #     for cid in connectors
            #     if connectors[cid].start_object_id == _object_id
            # ]
            # for connection in connections:
            #     if connection.connector_type not in ("Association", "Generalization"):
            #         continue
            #     attrib = _output.setdefault(connection.name, {})
            #     if not attrib:
            #         attrib = dict(
            #             attribute_name=connection.name,
            #             attribute_type=objects[connection.end_object_id].name,
            #             attribute_cardinality=connection.source_card,
            #             note=None,
            #         )
            #     _output[connection.name] = attrib
            for offset, attrib in enumerate(_output.values()):
                _codelist = attrib.get("codelist")
                if _codelist:
                    _cl = ct_content.get(_codelist)
                    if _codelist != "CNEW":
                        _codelist_value = '=HYPERLINK("#{}!A2","{}")'.format(_codelist, _codelist)
                    else:
                        _codelist_value = "CNEW"            
                else:
                    _codelist_value = ""
                write_cell(sheet, row=row_num, column=1, value = obj.name)
                write_cell(sheet, row=row_num, column=2, value = attrib["attribute_name"])
                write_cell(sheet, row=row_num, column=3, value = attrib["attribute_type"])
                write_cell(sheet, row=row_num, column=4, value = attrib[
                    "attribute_cardinality"
                ])
                write_cell(sheet, row=row_num, column=6, value = attrib.get("c_code", ""))
                write_cell(sheet, row=row_num, column=7, value = attrib.get("pref_term", ""))
                write_cell(sheet, row=row_num, column=8, value = attrib.get("definition", ""))
                write_cell(sheet, row=row_num, column=9, value = _codelist_value)
                write_cell(sheet, row=row_num, column=10, value = attrib.get(
                    "external_value_list", ""
                ))
                row_num += 1
    for c_code, _codelist in codelists.items():
        if c_code.strip().upper() == 'CNEW':
            continue
        _sheet = doc.create_sheet(c_code)
        for idx, colheader in enumerate(["Code", "Preferred Term", "Synonyms", "Definition"], start=1):
            write_cell(_sheet, row=1, column=idx, value=colheader, header=True)
        for idx, item in enumerate(_codelist.items, start=2):
            # type item: PermissibleValue
            write_cell(_sheet, row=idx, column=1, value = item.concept_c_code)
            write_cell(_sheet, row=idx, column=2, value = item.preferred_term)
            write_cell(_sheet, row=idx, column=3, value = ";".join(item.synonyms) if item.synonyms else "")
            write_cell(_sheet, row=idx, column=4, value = item.definition)
    for wks in doc.worksheets:
        _columns = cols.get(wks.title, {})
        for colnum, length in _columns.items():
            column_width = min([length, 50])
            wks.column_dimensions[get_column_letter(colnum)].width = column_width
        

    # create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    fname = os.path.join(output_dir, f"{name}.xlsx")
    doc.save(fname)
    print(f"Generated USDM Excel file: {fname}")


def main_usdm(source_dir: str, controlled_term: str, output_dir: str):
    objects, attributes, connectors = load_expanded_dir(source_dir=source_dir)
    ct_content, codelists = load_usdm_ct(controlled_term)
    name = (
        os.path.basename(os.path.dirname(source_dir))
        if source_dir.endswith("/")
        else os.path.basename(source_dir)
    )
    generate(name, objects, attributes, connectors, ct_content, codelists, output_dir)
