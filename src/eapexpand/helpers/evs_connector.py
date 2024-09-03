from __future__ import annotations

import re
from typing import Optional

import requests


class NCIEVSConnector:
    def __init__(self):
        # self.api_key = api_key
        self.client = requests.Session()
        # self.client.headers.update({"api_token": self.api_key})
        self._base_url = "https://api-evsrest.nci.nih.gov/api/v1"
        self._package_name = None
        self._package_id = None
        self._cache = {}

    def get_concept(self, concept_code: str, terminology: Optional[str] = "ncit"):
        """
        Get the concept from the EVS API
        """
        if concept_code in self._cache:
            return self._cache[concept_code]
        url = f"{self._base_url}/concepts/{terminology}/{concept_code}"
        response = self.client.get(url)
        response.raise_for_status()
        self._cache[concept_code] = response.json()
        return response.json()
