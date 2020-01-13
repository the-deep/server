from lead.tasks import _preprocess


def test_lead_text_extract_transform_tab_and_nbsp():
    """Test fitler and tansform extracted word"""
    extracted_text = 'Hello, this is extracted\t text that contains &nbsp;.'
    expected_text = 'Hello, this is extracted txt that contains .'
    assert _preprocess(expected_text) == expected_text
