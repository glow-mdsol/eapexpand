from eapexpand.usdm_unpkt import load_usdm_ct


def test_load_document(ct_file):
    """Load the published USDM v4.0.0 CT."""
    ct_content, codelists = load_usdm_ct(ct_file)
    assert len(codelists) == 46
    assert len(ct_content) == 84
    # the published standard has no placeholder (CNEW) codelists
    assert not [code for code in codelists if code.upper().startswith("CNEW")]
    assert all(codelist is not None for codelist in codelists.values())
    assert "Study" in ct_content
    study = ct_content["Study"]
    # 3 designated plus id
    assert len(study.attributes) == 4
    assert len(study.relationships) == 2
    sddv = ct_content["StudyDefinitionDocumentVersion"]
    assert len(sddv.attributes) == 2
    assert len(sddv.complex_datatype_relationships) == 2
    assert len(sddv.relationships) == 2
    assert len(sddv.all_attributes) == 6
    status = sddv.get_attribute("status")
    assert status.has_value_list is True
    assert status.codelist.concept_c_code == "C188723"
