"""Unit tests for VaaniDoc IndicTrans2 CT2 language mapping module.

Tests the language code mapping, validation, and helper functions.
"""

import pytest

from backend.ai.translation.language_map import (
    is_supported_language,
    get_model_language_code,
    get_language_name,
    get_supported_vaani_codes,
    list_languages,
)


# ---- is_supported_language tests ----

class TestIsSupportedLanguage:
    def test_valid_language_gujarati(self):
        assert is_supported_language("gu") is True

    def test_valid_language_hindi(self):
        assert is_supported_language("hi") is True

    def test_valid_language_tamil(self):
        assert is_supported_language("ta") is True

    def test_valid_language_english_edge(self):
        # English is not a source language for the Indic->English stage
        assert is_supported_language("en") is False

    def test_unsupported_language(self):
        assert is_supported_language("xyz") is False

    def test_type_error_on_non_string(self):
        with pytest.raises(TypeError, match="Expected a string"):
            is_supported_language(123)  # type: ignore

    def test_type_error_on_none(self):
        with pytest.raises(TypeError, match="Expected a string"):
            is_supported_language(None)  # type: ignore


# ---- get_model_language_code tests ----

class TestGetModelLanguageCode:
    def test_gujarati(self):
        code = get_model_language_code("gu")
        assert code == "guj_Gujr"

    def test_hindi(self):
        code = get_model_language_code("hi")
        assert code == "hin_Deva"

    def test_tamil(self):
        code = get_model_language_code("ta")
        assert code == "tam_Taml"

    def test_unsupported(self):
        with pytest.raises(KeyError):
            get_model_language_code("xyz")  # type: ignore

    def test_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            get_model_language_code(123)  # type: ignore


# ---- get_language_name tests ----

class TestGetLanguageName:
    def test_gujarati(self):
        name = get_language_name("gu")
        assert name == "Gujarati"

    def test_hindi(self):
        name = get_language_name("hi")
        assert name == "Hindi"

    def test_tamil(self):
        name = get_language_name("ta")
        assert name == "Tamil"

    def test_unsupported(self):
        with pytest.raises(KeyError):
            get_language_name("xyz")  # type: ignore

    def test_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            get_language_name(123)  # type: ignore


# ---- get_supported_vaani_codes tests ----

class TestGetSupportedVaanIcodes:
    def test_returns_tuple(self):
        codes = get_supported_vaani_codes()
        assert isinstance(codes, tuple)
        assert len(codes) == 22

    def test_contains_gujarati(self):
        codes = get_supported_vaani_codes()
        assert "gu" in codes

    def test_contains_hindi(self):
        codes = get_supported_vaani_codes()
        assert "hi" in codes


# ---- list_languages tests ----

class TestListLanguages:
    def test_returns_dict(self):
        mapping = list_languages()
        assert isinstance(mapping, dict)
        assert len(mapping) == 22

    def test_gujarati_entry(self):
        mapping = list_languages()
        assert mapping["gu"] == ("guj_Gujr", "Gujarati")

    def test_hindi_entry(self):
        mapping = list_languages()
        assert mapping["hi"] == ("hin_Deva", "Hindi")

    def test_tamil_entry(self):
        mapping = list_languages()
        assert mapping["ta"] == ("tam_Taml", "Tamil")


# ---- end-of-file ----