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


# ── Negation tests ──────────────────────────────────────────────────

def test_negation_dont():
    result = extract_symptoms("I don't have fever.")
    assert result == []

def test_negation_do_not():
    result = extract_symptoms("I do not have fever.")
    assert result == []

def test_negation_no():
    result = extract_symptoms("No fever.")
    assert result == []

def test_negation_denies():
    result = extract_symptoms("The patient denies fever.")
    assert result == []

def test_negation_denied():
    result = extract_symptoms("The patient denied fever.")
    assert result == []

def test_negation_negative_for():
    result = extract_symptoms("Negative for fever.")
    assert result == []

def test_negation_without():
    result = extract_symptoms("I am without fever.")
    assert result == []

def test_negation_local_scope_but():
    result = extract_symptoms("I have fever but no headache.")
    assert len(result) == 1
    assert result[0].name == "fever"

def test_negation_local_scope_dont():
    result = extract_symptoms("I don't have fever but I have headache.")
    assert len(result) == 1
    assert result[0].name == "headache"

def test_negation_local_scope_and():
    result = extract_symptoms("I have headache and no vomiting.")
    assert len(result) == 1
    assert result[0].name == "headache"

def test_negation_local_scope_dont_second():
    result = extract_symptoms("I don't have headache but I have fever.")
    assert len(result) == 1
    assert result[0].name == "fever"

def test_negation_local_scope_punctuation():
    result = extract_symptoms("I don't have fever. I have headache.")
    assert len(result) == 1
    assert result[0].name == "headache"

def test_negation_sentence_boundaries():
    result = extract_symptoms("No fever. No headache. I have cough.")
    assert len(result) == 1
    assert result[0].name == "cough"

def test_synonym_negation_1():
    result = extract_symptoms("I don't have head pain.")
    assert result == []

def test_synonym_negation_2():
    result = extract_symptoms("No stomach pain.")
    assert result == []

def test_synonym_negation_3():
    result = extract_symptoms("I do not feel breathless.")
    assert result == []

def test_mixed_negation_and_active():
    result = extract_symptoms("I have fever, headache and no vomiting.")
    assert len(result) == 2
    names = [s.name for s in result]
    assert names == ["fever", "headache"]

def test_repeated_symptom_active_wins():
    result = extract_symptoms("I don't have headache. I have headache now.")
    assert len(result) == 1
    assert result[0].name == "headache"

def test_negation_case_insensitive():
    result = extract_symptoms("I DON'T HAVE FEVER.")
    assert result == []

def test_negation_punctuation_comma():
    result = extract_symptoms("I don't have fever, but I have headache.")
    assert len(result) == 1
    assert result[0].name == "headache"

def test_no_false_global_negation():
    result = extract_symptoms("I don't have fever but I have headache and cough.")
    assert len(result) == 2
    names = [s.name for s in result]
    assert names == ["headache", "cough"]
