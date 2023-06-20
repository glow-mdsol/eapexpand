import os
from typing import Dict, Optional
from eapexpand.models.eap import Attribute, Connector, Object

from openpyxl import load_workbook, Workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


def generate(
    name: str,
    objects: Dict[str, Object],
    ct_content: dict,
    codelists: dict,
    output_dir: Optional[str] = "output",
):
    """
    Generates the Excel Representation of the model
    :param name: The name of the model - guides what the output file is called
    """
    packages = {x.package_id: x for x in objects.values() if x.object_type == "Package"}
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
                        attribute_cardinality=_attribute.cardinality,
                        attribute_note=_attribute.notes,
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
                if attrib["attribute_note"]:
                    write_cell(sheet, row=row_num, column=5, value = attrib["attribute_note"])
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
