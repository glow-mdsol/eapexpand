from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict

from openpyxl import load_workbook

from .loader import load_expanded_dir
from .models.sqlite_loader import load_from_file
from .models.usdm_ct import CodeList, Entity, PermissibleValue


def load_usdm_ct(filename: str):
    print("Loading USDM CT")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    wbk = load_workbook(filename, read_only=True)
    _ent_attr = wbk["DDF Entities&Attributes"]
    entities = {}
    headers = []
    for idx, row in enumerate(_ent_attr.iter_rows(min_row=1, values_only=True)):
        if idx == 0:
            for cell in row:
                headers.append(cell)
            continue
        # map the row to a dictionary
        _row = dict(zip(headers, row))
        _name = _row["Entity Name"]
        _role = _row["Role"]
        _entity = Entity.from_dict(_row)
        if _entity.role in ("Entity"):
            if not _name in entities:
                # add an id attribute
                _id = Entity.from_dict({"Entity Name": f"{_name}", 
                                        "Role": "Attribute", 
                                        "Logical Data Model Name": "id", 
                                        "Definition": "Unique identifier for the entity", 
                                        "CT Item Preferred Name": "id", 
                                        "Has Value List": "N", 
                                        "NCI C-code": "",
                                        "Inherited From": ""})
                _entity.attributes.append(_id)
                entities[_name] = _entity

        elif _entity.role in ("Relationship"):
            entities[_name].relationships.append(_entity)
        elif _entity.role in ("Complex Datatype Relationship"):
            entities[_name].complex_datatype_relationships.append(
                _entity
            )
        elif _entity.role in ("Attribute"):
            entities[_name].attributes.append(_entity)
        else:
            raise ValueError(f"Unknown entity type: {_role}")
    print("Loading USDM CT Value Sets")
    _value_sets = wbk["DDF valid value sets"]
    codelists = {}
    missing_codelists = {}
    for row in _value_sets.iter_rows(min_row=7, values_only=True):
        # get the entity
        codeset = PermissibleValue.from_row(row)
        if codeset.codelist_c_code not in codelists:
            codelists[codeset.codelist_c_code] = CodeList.from_pvalue(codeset)
        codelists[codeset.codelist_c_code].add_item(codeset)
        # get the entity name
        _entity = entities[row[1]]
        # get the attribute name
        _attribute = row[2]
        _attr = _entity.get_attribute(_attribute)
        # workaround
        if _attr is None:
            missing_codelists[_attribute] = _entity.entity_name
            continue
        _attr.codelist_items.append(codeset)
    if missing_codelists:
        print("Missing Attributes")
        for attr, entity in missing_codelists.items():
            print(f"Attribute {attr} not found in entity {entity} ")
    return entities, codelists


def main_usdm(
    source_dir_or_file: str, controlled_term: str, output_dir: str, gen: Dict[str, bool]
):
    if Path(source_dir_or_file).is_file():
        document = load_from_file(source_dir_or_file)
    else:
        name = (
            os.path.basename(os.path.dirname(source_dir_or_file))
            if source_dir_or_file.endswith("/")
            else os.path.basename(source_dir_or_file)
        )
        document = load_expanded_dir(source_dir_or_file)
    ct_content, codelists = load_usdm_ct(controlled_term)
    definitions = {}
    for concept in ct_content.values():
        if concept.definition:
            definitions[concept.entity_name] = concept.definition
        for attr in concept.attributes:
            if attr.definition:
                definitions[attr.logical_data_model_name] = attr.definition
    document.merge_definitions(definitions)
    for aspect, genflag in gen.items():
        print("Checking generation of ", aspect, "as", genflag)
        if genflag:
            if aspect == "prisma":
                from .render.prisma import generate as generate_prisma

                generate_prisma(
                    document.name, document, ct_content, codelists, output_dir
                )
            elif aspect == "linkml":
                from .render.linkml import generate as generate_linkml

                generate_linkml(
                    document.name,
                    document,
                    prefix="https://cdisc.org/usdm",
                    output_dir=output_dir,
                )
            elif aspect == "shapes":
                from .render.shapes import generate as generate_shapes

                generate_shapes(
                    document.name, document, ct_content, codelists, output_dir
                )
            else:
                raise ValueError(f"Unknown aspect: {aspect}")
    # always generate the workbook
    from .render.usdm_workbook import generate as generate_workbook

    _ = generate_workbook(document.name, document, ct_content, codelists, output_dir)
