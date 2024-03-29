from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re

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
    inherited_from: Optional[str] = None

    @property
    def qualified_name(self):
        if not self.logical_data_model_name.lower().startswith(self.entity_name.lower()):
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
                source = re.compile(r"Y \((.*)\)$")
                m = source.match(row[8])
                if m:
                    entity.value_list_description = m.group(1)
                    if entity.value_list_description.lower().startswith("point out"):
                        entity.external_value_list = True
                    else:
                        entity.external_value_list = False
                        entity.codelist_c_code = entity.value_list_description
                else:
                    raise ValueError(
                        f"Unable to parse value list description: {row[8]}"
                    )
            elif has_value_list.startswith("N"):
                entity.has_value_list = False
        return entity


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



