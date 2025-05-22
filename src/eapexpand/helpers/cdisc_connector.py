from __future__ import annotations

import re
from typing import Optional

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from eapexpand.models.usdm_ct import CodeList, PermissibleValue


class CDISCCTConnector:
    """
    A connector class for interacting with the CDISC Library API to retrieve controlled terminology (CT) packages 
    and codelists.

    Attributes:
        api_key (str): The API key used for authenticating with the CDISC Library API.
        client (requests.Session): A session object for making HTTP requests with the API key pre-configured.
        _base_url (str): The base URL for the CDISC Library API.
        _packages (dict): A cache for storing the newest package URLs for different vocabularies.
        _cache (dict): A cache for storing retrieved codelists.

    Methods:
        get_newest_package(vocabulary="sdtmct"):
            Retrieves the newest package URL for a given vocabulary from the CDISC Library API.

        retrieve_valueset(codelist_code: str) -> Optional[CodeList]:
            Retrieves a codelist from the CDISC Library API and converts it into a `CodeList` object.
            If the codelist is already cached, it retrieves it from the cache.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = requests.Session()
        self.client.headers.update({"api-key": self.api_key})
        self._base_url = "https://api.library.cdisc.org/api"
        self._packages = {}
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
            if not _packages:
                raise ValueError(f"No packages found for vocabulary {vocabulary}")
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
            for package in ("ddfct", "sdtmct", "protocolct", "glossaryct", "ddfct"):
                if package not in self._packages:
                    self._packages[package] = self.get_newest_package(package)
                # get the package_id
                package_id = self._packages[package]
                _url = f"{self._base_url}{package_id}/codelists/{codelist_code}"
                results = self.client.get(_url)

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
                    break
            else:
                logger.error(f"Failed to retrieve codelist {codelist_code}")
                return None
                #raise ValueError(f"Failed to retrieve codelist {codelist_code}")
        return self._cache[codelist_code]
