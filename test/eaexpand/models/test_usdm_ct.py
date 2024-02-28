from eapexpand.usdm_unpkt import load_usdm_ct


def test_load_document(ct_file):
    ct_content, codelists = load_usdm_ct(ct_file)
    assert len(ct_content) > 0
    assert len(codelists) == 32
    assert len(ct_content) == 58
    assert "Study" in ct_content
    study = ct_content["Study"]
    # 3 desigated plus id
    assert len(study.attributes) == 4
    assert len(study.relationships) == 2
    spdv = ct_content["StudyProtocolDocumentVersion"]
    assert len(spdv.attributes) == 2
    assert len(spdv.complex_datatype_relationships) == 1
    assert len(spdv.relationships) == 3
    assert len(spdv.all_attributes) == 6
    protocol_status = spdv.get_attribute("protocolStatus")
    assert protocol_status.has_value_list is True
