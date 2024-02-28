import pytest
from pathlib import Path


@pytest.fixture
def ct_file():
    return Path(__file__).parent / "fixtures" / "USDM_CT.xlsx"
