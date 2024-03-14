from __future__ import annotations

"""
Handles the loading of the USDM CT
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class DDFEntity:
    """
    Represents a single entity in the USDM CT (linked to DDF)
    """

    entity_name: str = field(metadata=config(field_name="Entity Name"))
    logical_data_model_name: str = field(
        metadata=config(field_name="Logical Data Model Name")
    )
    role: Optional[str] = field(metadata=config(field_name="Role"))
    nci_c_code: Optional[str] = field(metadata=config(field_name="NCI C-code"))
    preferred_term: Optional[str] = field(
        metadata=config(field_name="CT Item Preferred Name")
    )
    raw_synonyms: Optional[str] = field(metadata=config(field_name="Synonym(s)"))
    definition: Optional[str] = field(
        default=None, metadata=config(field_name="Definition")
    )
    value_list: Optional[str] = field(
        default=None, metadata=config(field_name="Has Value List")
    )
    codelist_url: Optional[str] = field(
        default=None, metadata=config(field_name="Codelist URL")
    )
    inherited_from: Optional[str] = field(
        default=None, metadata=config(field_name="Inherited From")
    )
    attributes: Optional[List[DDFEntity]] = field(default_factory=list)
    relationships: Optional[List[DDFEntity]] = field(default_factory=list)
    complex_datatype_relationships: Optional[List[DDFEntity]] = field(
        default_factory=list
    )
    # assigned codelist
    codelist: Optional[CodeList] = None

    @property
    def synonyms(self):
        return (
            [s.strip() for s in self.raw_synonyms.split(";")]
            if self.raw_synonyms
            else []
        )

    @property
    def qualified_name(self):
        if not self.logical_data_model_name.lower().startswith(
            self.entity_name.lower()
        ):
            name = f"{self.entity_name.lower()}{self.logical_data_model_name[0].upper()}{self.logical_data_model_name[1:]}"
            return name
        else:
            return self.logical_data_model_name

    @property
    def all_attributes(self):
        return {
            x.logical_data_model_name: x
            for x in self.attributes
            + self.relationships
            + self.complex_datatype_relationships
        }

    def get_attribute(self, attribute_name: str) -> Optional[DDFEntity]:
        for attr in self.attributes:
            if attr.logical_data_model_name == attribute_name:
                return attr
            elif attr.qualified_name == attribute_name:
                print(f"Warning, using a fuzzy match for {attribute_name}")
                return attr
        for attr in self.complex_datatype_relationships:
            if attr.logical_data_model_name == attribute_name:
                return attr
            elif attr.qualified_name == attribute_name:
                print(f"Warning, using a fuzzy match for {attribute_name}")
                return attr
        for attr in self.relationships:
            if attr.logical_data_model_name == attribute_name:
                return attr
            elif attr.qualified_name == attribute_name:
                print(f"Warning, using a fuzzy match for {attribute_name}")
                return attr
        return None

    @property
    def has_value_list(self) -> bool:
        if self.value_list:
            if self.value_list.startswith("Y"):
                return True
            else:
                return False
        else:
            return False

    @property
    def external_code_list(self):
        if self.has_value_list:
            _value = None
            if "Point" in self.value_list:
                if "Point to" in self.value_list:
                    # Point to
                    _value = self.value_list[12:-1]
                elif "Points to" in self.value_list:
                    # Points to
                    _value = self.value_list[13:-1]
                else:
                    # Point out to
                    _value = self.value_list[16:-1]
            elif "CNEW" in self.value_list:
                _value = "CNEW"
            else:
                _value = self.value_list.split("(")[1].split(" ")[-1][:-1]
            return _value

    @property
    def codelist_code(self) -> Optional[str]:
        if self.has_value_list:
            c_code = None
            # have a value list
            if "point" in self.value_list.lower():
                return None
            else:
                if "CNEW" in self.value_list:
                    c_code = "CNEW"
                else:
                    c_code = self.value_list.split("(")[1].split(" ")[-1][:-1]
                return c_code
        else:
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


@dataclass
class CodeList:
    """
    Mainly a container for permissible values
    In the CT sheet the values are a list associated with an entity->attribute, in the CDISC Library
     the binding is missing, so the codelist is the parent rather than something inferred from the record
    """

    entity_name: Optional[str] = ""
    attribute_name: Optional[str] = ""
    concept_c_code: Optional[str] = ""
    preferred_term: Optional[str] = ""
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = None
    submission_value: Optional[str] = None
    extensible: Optional[bool] = False
    items: List[PermissibleValue] = field(default_factory=list)

    def add_item(self, item: PermissibleValue):
        self.items.append(item)

    @classmethod
    def from_pvalue(cls, pvalue: PermissibleValue):
        return cls(
            entity_name=pvalue.entity_name,
            attribute_name=pvalue.attribute_name,
            concept_c_code=pvalue.codelist_c_code,
            preferred_term=pvalue.preferred_term,
            synonyms=pvalue.synonyms,
            submission_value=pvalue.submission_value,
        )


@dataclass
class PermissibleValue:
    project: str
    entity_name: str
    attribute_name: str
    codelist_c_code: str
    concept_c_code: str
    preferred_term: str
    synonyms: Optional[List[str]] = field(default_factory=list)
    definition: Optional[str] = None
    submission_value: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row[6]:
            synonyms = [s.strip() for s in row[6].split(";")]
        else:
            synonyms = []
        return cls(
            project=row[0],
            entity_name=row[1],
            attribute_name=row[2],
            codelist_c_code=row[3],
            concept_c_code=row[4],
            preferred_term=row[5],
            synonyms=synonyms,
            definition=row[7],
        )
