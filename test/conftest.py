import pytest
from pathlib import Path


@pytest.fixture
def ct_file():
    return Path(__file__).parent / "fixtures" / "v4.0.0_USDM_CT.xlsx"
