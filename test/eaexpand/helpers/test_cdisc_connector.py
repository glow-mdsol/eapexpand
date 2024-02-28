import os
from dotenv import load_dotenv
from eapexpand.helpers.cdisc_connector import CDISCCTConnector

load_dotenv()


def test_get_packages():
    client = CDISCCTConnector(os.environ["CDISC_LIBRARY_API_TOKEN"])
    packages = client.get_newest_package()
    assert packages is not None
    assert "sdtmct" in packages


def test_get_term():
    client = CDISCCTConnector(os.environ["CDISC_LIBRARY_API_TOKEN"])
    CL = "C66736"
    codelist = client.retrieve_valueset(CL)
    assert codelist is not None
