"""Tests for the VaaniDoc symptom extraction engine.

Run with:
    pytest ai/clinical/test_extraction.py -v
"""

from ai.clinical.extraction import extract_symptoms


def test_single_symptom():
    result = extract_symptoms("I have a headache.")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_synonym_match():
    result = extract_symptoms("I have head pain.")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_stomach_synonym():
    result = extract_symptoms("My stomach hurts.")
    assert len(result) == 1
    assert result[0].name == "abdominal_pain"


def test_vomiting_synonym():
    result = extract_symptoms("I am throwing up.")
    assert len(result) == 1
    assert result[0].name == "vomiting"


def test_breathing_synonym():
    result = extract_symptoms("I am breathless.")
    assert len(result) == 1
    assert result[0].name == "shortness_of_breath"


def test_multiple_symptoms():
    result = extract_symptoms("I have fever, headache and vomiting.")
    assert len(result) == 3
    names = [s.name for s in result]
    assert names == ["fever", "headache", "vomiting"]


def test_case_insensitive():
    result = extract_symptoms("I have FEVER and HeadAche.")
    assert len(result) == 2
    names = [s.name for s in result]
    assert names == ["fever", "headache"]


def test_leading_trailing_whitespace():
    result = extract_symptoms("   I have a headache.   ")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_repeated_whitespace():
    result = extract_symptoms("I   have   head   pain")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_no_symptoms():
    result = extract_symptoms("I feel okay.")
    assert result == []


def test_duplicate_synonym():
    result = extract_symptoms("I have head pain and headache.")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_symptom_order():
    result = extract_symptoms("After lunch I had nausea, then later developed headache and fever.")
    assert len(result) == 3
    names = [s.name for s in result]
    assert names == ["nausea", "headache", "fever"]


def test_multi_word_phrase():
    result = extract_symptoms("I have shortness of breath today.")
    assert len(result) == 1
    assert result[0].name == "shortness_of_breath"


def test_none_input():
    result = extract_symptoms(None)
    assert result == []


def test_empty_string():
    result = extract_symptoms("")
    assert result == []


def test_whitespace_only():
    result = extract_symptoms("    \n\t  ")
    assert result == []


def test_word_boundaries():
    # Should not match 'rash' inside 'trash'
    result = extract_symptoms("I took out the trash.")
    assert len(result) == 0


def test_multiple_occurrences_same_symptom():
    result = extract_symptoms("I have headache and later another headache.")
    assert len(result) == 1
    assert result[0].name == "headache"


def test_optional_fields_are_none():
    result = extract_symptoms("I have severe headache for two days.")
    assert len(result) == 1
    s = result[0]
    assert s.name == "headache"
    assert s.severity is None
    assert s.duration is None
    assert s.body_part is None
    assert s.confidence is None
