from __future__ import annotations
from pathlib import Path
import re


from typing import Dict, Optional
import os

from openpyxl import load_workbook

from .models.sqlite_loader import load_from_file

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
        elif _role == "Relationship" or _role.startswith("Relationship ("):
            entities[_name].relationships.append(row[3])
            
        elif _role in ("Attribute")  or _role.startswith("Attribute ("):
            _entity = Entity.from_row(row)
            if 'inherited from' in _role:
                pattern = re.compile(r'\(inherited from (.*)[\)]?$')
                if pattern.search(_role):
                    _inherited_from = pattern.search(_role).group(0)
                    _entity.inherited_from = _inherited_from
                else:
                    print(f"Can't match {_role} for {_name}")
            entities[_name].attributes.append(_entity)
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
        _attr = _entity.get_attribute(_attribute)
        # workaround
        if _attr is None:
            # _unqualified_name = _attribute.replace(_entity.entity_name, '')
            # _unqualified_name = _unqualified_name[0].lower() + _unqualified_name[1:]
            # _attr = _entity.get_attribute(_unqualified_name)
            # print(f"Warning: had to munge name: {_attribute} for {_entity.entity_name}")
            # if _attr is None:
            print(f"Attribute {row[2]} not found in entity {_entity.entity_name} ")
            continue
                # raise ValueError(
                #     f"Attribute {row[2]} not found in entity {_entity.entity_name} "
                # )
        if _attr.codelist_c_code is None:
            _attr.codelist_c_code = codeset.codelist_c_code
        _attr.codelist_items.append(codeset)
    return entities, codelists


def main_usdm(source_dir_or_file: str, controlled_term: str, output_dir: str, gen: Dict[str, bool]):
    if Path(source_dir_or_file).is_file():
        document = load_from_file(source_dir_or_file)
    else:
        name = (
            os.path.basename(os.path.dirname(source_dir_or_file))
            if source_dir_or_file.endswith("/")
            else os.path.basename(source_dir_or_file)
        )
        document = load_expanded_dir(source_dir)
    ct_content, codelists = load_usdm_ct(controlled_term)
    # name = os.path.basename(os.path.dirname(source_dir)) \
    #     if source_dir.endswith("/") else os.path.basename(source_dir)
    for aspect, genflag in gen.items():
        if genflag:
            if aspect == "prisma":
                from .render.prisma import generate as generate_prisma
                generate_prisma(document.name, document, ct_content, codelists, output_dir)
            elif aspect == "linkml":
                from .render.linkml import generate as generate_linkml
                generate_linkml(document.name, document,  output_dir=output_dir)
            elif aspect == "shapes":
                from .render.shapes import generate as generate_shapes
                generate_shapes(document.name, document, ct_content, codelists, output_dir)
            else:
                raise ValueError(f"Unknown aspect: {aspect}")
    else:
        # always generate the workbook
        from .render.usdm_workbook import generate as generate_workbook
        _ = generate_workbook(document.name, document, ct_content, codelists, output_dir)
    