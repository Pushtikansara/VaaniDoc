"""Tests for the VaaniDoc symptom knowledge base.

Run with:
    pytest ai/clinical/test_symptoms.py -v
"""

from ai.clinical.symptoms import (
    SYMPTOM_DB,
    build_synonym_index,
    get_all_symptoms,
    get_category,
    get_symptom,
    get_synonyms,
    lookup_synonym,
)


def test_kb_not_empty():
    assert len(SYMPTOM_DB) > 0


def test_at_least_50_symptoms():
    assert len(SYMPTOM_DB) >= 50


def test_symptom_structure():
    for canonical, entry in SYMPTOM_DB.items():
        assert isinstance(canonical, str)
        assert canonical.islower()
        assert " " not in canonical
        assert "synonyms" in entry
        assert "category" in entry
        assert len(entry["synonyms"]) > 0
        assert entry["category"] in {
            "Neurological",
            "Respiratory",
            "Cardiovascular",
            "Gastrointestinal",
            "General",
            "Musculoskeletal",
            "Dermatological",
            "Urinary",
            "ENT",
        }


def test_get_symptom():
    entry = get_symptom("headache")
    assert entry is not None
    assert entry["category"] == "Neurological"


def test_get_unknown_symptom():
    assert get_symptom("unknown_symptom") is None


def test_get_category():
    assert get_category("headache") == "Neurological"
    assert get_category("cough") == "Respiratory"
    assert get_category("fever") == "General"


def test_get_synonyms():
    syns = get_synonyms("headache")
    assert syns is not None
    assert "headache" in syns


def test_reverse_lookup():
    assert lookup_synonym("head pain") == "headache"
    assert lookup_synonym("stomach pain") == "abdominal_pain"
    assert lookup_synonym("throwing up") == "vomiting"


def test_reverse_lookup_case_insensitive():
    assert lookup_synonym("HEAD PAIN") == "headache"
    assert lookup_synonym("  Stomach PAIN  ") == "abdominal_pain"


def test_reverse_lookup_whitespace():
    assert lookup_synonym("  throwing    up  ") == "vomiting"


def test_unknown_phrase():
    assert lookup_synonym("completely unknown phrase") is None


def test_no_diagnoses_as_keys():
    diagnoses = {"diabetes", "pneumonia", "migraine", "heart_attack", "stroke"}
    for d in diagnoses:
        assert d not in SYMPTOM_DB


def test_no_duplicate_canonical_names():
    # In a dictionary, keys are inherently unique, but we can verify the keys match get_all_symptoms
    assert len(set(SYMPTOM_DB.keys())) == len(SYMPTOM_DB.keys())
    assert len(get_all_symptoms()) == len(SYMPTOM_DB)


def test_build_synonym_index():
    index = build_synonym_index()
    assert isinstance(index, dict)
    assert len(index) >= len(SYMPTOM_DB)
