from __future__ import annotations

import re
from typing import Optional

import requests

from eapexpand.models.usdm_ct import CodeList, PermissibleValue


class CDISCCTConnector:
    """
    Handle the connection to the CDISC CT API
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = requests.Session()
        self.client.headers.update({"api-key": self.api_key})
        self._base_url = "https://api.library.cdisc.org/api"
        self._package_name = None
        self._package_id = None
        self._cache = {}

    def get_newest_package(self, vocabulary="sdtmct"):
        """
        Get the newest package for a vocabulary
        """
        _package_re = re.compile(r"/mdr/ct/packages/([a-z\-]+)-(\d{4}-\d{2}-\d{2})")
        packages = self.client.get(f"{self._base_url}/mdr/ct/packages")
        if packages.status_code == 200:
            _packages = []
            packages = packages.json()["_links"]["packages"]
            for package in packages:
                vocab, date = _package_re.match(package["href"]).groups()
                if vocab == vocabulary:
                    _packages.append((date, package, package["href"]))
            return sorted(_packages)[-1][-1]
        else:
            raise ValueError(f"Failed to retrieve packages: {packages.status_code}")

    def retrieve_valueset(self, codelist_code: str) -> Optional[CodeList]:
        """
        Retrieve the remote valuesset and munge into a CodeList
        """
        if codelist_code in self._cache:
            return self._cache[codelist_code]

        if codelist_code == "CNEW":
            self._cache[codelist_code] = CodeList(
                concept_c_code="CNEW",
                submission_value="CNEW",
                preferred_term="New Code",
                extensible=True,
            )
        else:
            if self._package_id is None:
                self._package_id = self.get_newest_package()
            results = self.client.get(
                f"{self._base_url}{self._package_id}/codelists/{codelist_code}"
            )

            codelist = None
            if results.status_code == 200:
                dataset = results.json()
                codelist = CodeList(concept_c_code=dataset["conceptId"])
                codelist.submission_value = dataset["submissionValue"]
                codelist.preferred_term = dataset["preferredTerm"]
                codelist.definition = dataset.get("definition")
                codelist.extensible = dataset.get("extensible") == "true"
                codelist.synonyms = dataset.get("synonyms", [])
                for term in dataset["terms"]:
                    pv = PermissibleValue(
                        project="DDF",
                        entity_name="",
                        codelist_c_code=dataset["conceptId"],
                        preferred_term=term["preferredTerm"],
                        synonyms=term.get("synonyms", []),
                        definition=term.get("definition"),
                        attribute_name="",
                        concept_c_code=term["conceptId"],
                    )
                    codelist.add_item(pv)
            self._cache[codelist_code] = codelist
        return self._cache[codelist_code]
