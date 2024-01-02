from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re

from dataclasses_json import config, dataclass_json


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

# Row #	Entity Name	Role	Inherited From	Logical Data Model Name	NCI C-code	CT Item Preferred Name	Synonym(s)	Definition	Has Value List	Codelist URL

@dataclass_json
@dataclass
class Entity:
    entity_name: str = field(metadata=config(field_name="Entity Name"))
    logical_data_model_name: str = field(metadata=config(field_name="Logical Data Model Name"))
    role: Optional[str] = field(metadata=config(field_name="Role"))
    nci_c_code: Optional[str] = field(metadata=config(field_name="NCI C-code"))
    preferred_term: Optional[str] = field(metadata=config(field_name="CT Item Preferred Name"))
    synonyms: Optional[List[str]] = field(default_factory=list, metadata=config(field_name="Synonym(s)"))
    definition: Optional[str] = field(default=None, metadata=config(field_name="Definition"))
    has_value_list: Optional[str] = field(default=None, metadata=config(field_name="Has Value List"))
    codelist_url: Optional[str] = field(default=None, metadata=config(field_name="Codelist URL"))
    inherited_from: Optional[str] = field(default=None, metadata=config(field_name="Inherited From"))
    value_list_description: Optional[str] = None
    external_value_list: Optional[str] = None
    attributes: Optional[List[Entity]] = field(default_factory=list)
    relationships: Optional[List[Entity]] = field(default_factory=list)
    codelist_c_code: Optional[str] = None
    codelist_items: Optional[List[PermissibleValue]] = field(default_factory=list)
    complex_datatype_relationships: Optional[List[Entity]] = field(default_factory=list)

    @property
    def qualified_name(self):
        if not self.logical_data_model_name.lower().startswith(
            self.entity_name.lower()
        ):
            name = f"{self.entity_name.lower()}{self.logical_data_model_name[0].upper()}{self.logical_data_model_name[1:]}"
            return name
        else:
            return self.logical_data_model_name

    def get_attribute(self, attribute_name: str):
        for attr in self.attributes:
            if attr.logical_data_model_name == attribute_name:
                return attr
            elif attr.qualified_name == attribute_name:
                print(f"Warning, using a fuzzy match for {attribute_name}")
                return attr
        return None

    # @classmethod
    # def from_row(cls, row):
    #     if row[6]:
    #         synonyms = [s.strip() for s in row[6].split(";")]
    #     else:
    #         synonyms = []
    #     entity = cls(
    #         entity_name=row[1],
    #         logical_data_model_name=row[3],
    #         nci_c_code=row[4],
    #         preferred_term=row[5],
    #         synonyms=synonyms,
    #         definition=row[7],
    #     )
    #     has_value_list = row[8]
    #     if has_value_list:
    #         if has_value_list.startswith("Y"):
    #             # have a value list
    #             entity.has_value_list = True
    #             if (
    #                 "point to" in row[8].lower()
    #                 or "points to" in row[8].lower()
    #                 or "point out" in row[8].lower()
    #             ):
    #                 entity.external_value_list = True
    #                 entity.value_list_description = row[8][3:-1]
    #             else:
    #                 entity.external_value_list = False
    #                 if "CNEW" in has_value_list:
    #                     c_code = "CNEW"
    #                 else:
    #                     c_code = has_value_list.split("(")[1].split(" ")[-1][:-1]
    #                 entity.codelist_c_code = c_code
    #         elif has_value_list.startswith("N"):
    #             entity.has_value_list = False
    #     return entity


class CodeList:
    def __init__(self, entity_name: str, attribute: str, codelist_c_code: str):
        self.entity_name = entity_name
        self.attribute = attribute
        self.codelist_c_code = codelist_c_code
        self.items = []

    def add_item(self, item: PermissibleValue):
        self.items.append(item)

    @classmethod
    def from_pvalue(cls, pvalue: PermissibleValue):
        return cls(
            entity_name=pvalue.entity,
            attribute=pvalue.attribute,
            codelist_c_code=pvalue.codelist_c_code,
        )
