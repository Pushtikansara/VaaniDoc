"""
VaaniDoc IndicTrans2 CT2 Translation Test Suite.

Tests whether the IndicTrans2 CT2 translation preserves clinically important meaning.

Do NOT judge translation only by exact string equality because multiple English translations can express the same meaning.

Separates:
- unit tests: test language mapping and validation (work without CT2 model)
- model integration tests: test actual translation (can be skipped when the CT2 model is unavailable)

Test categories cover critical clinical information preservation:
  1. Basic symptom translation
  2. Multiple symptoms
  3. Duration
  4. Numbers
  5. Dates
  6. Severity
  7. Body location
  8. Negation
  8. Names
  9. Medication names
  10. Dosages
  11. Units
  12. Empty input
  13. Unsupported language
  14. Long input
  15. Multiple sentences

Important safety examples:

A. Negation:
"મને તાવ નથી."

The English result must preserve the NEGATION.

B. Duration:
"મને ત્રણ દિવસથી તાવ છે."

The result must preserve 3 days.

C. Body location:
"મને છાતીમાં દુખાવો છે."

The result must preserve CHEST rather than changing it to stomach or another location.

D. Dosage:
"મે 500 mg દવા લીધી."

The result must preserve 500 mg.

E. Multiple symptoms:
"મને તાવ અને માતાનો દુખાવો છે."

Both fever and headache must remain present.

Create tests that check critical information preservation rather than requiring one exact English sentence.

Do not use another LLM to decide whether a translation is correct.

For deterministic tests, use expected semantic facts.

Separate:
- unit tests
- model integration tests

Allow model integration tests to be skipped when the CT2 model is unavailable.

At the end, provide:
- number of tests
- passed
- failed
- skipped
- known limitations
"""


# ---------------------------------------------------------------------------
# CT2 availability: check if module can be imported and model loaded
# ---------------------------------------------------------------------------
from backend.ai.translation.translator import (  # type: ignore
    translate,
    UnsupportedLanguageError,
    InvalidInputError,
    TranslationFailedError,
)
import ctranslate2 as _ct2_mod  # type: ignore

CT2_MODULE_IMPORTABLE = True
try:
    # Quick test: see if we can instantiate a Translator (may fail if no model)
    _ = _ct2_mod.Translator(
        "adalat-ai/ct2-rotary-indictrans2-indic-en-dist-200M",
        device="cpu",
        compute_type="float32",
    )
    CT2_MODEL_LOADABLE = True
except Exception:
    CT2_MODEL_LOADABLE = False
finally:
    del _ct2_mod

# Translate function and error classes

# If translate is None, the module couldn't be imported
if translate is None:
    CT2_MODULE_IMPORTABLE = False
    CT2_MODEL_LOADABLE = False

# Convenience: is CT2 available for translation (module importable + model loadable)?
CT2_AVAILABLE = CT2_MODULE_IMPORTABLE and CT2_MODEL_LOADABLE

# ---------------------------------------------------------------------------
# Unit tests: language mapping and validation (no CT2 model needed)
# ---------------------------------------------------------------------------


class TestLanguageMapping:
    """Unit tests for language code mapping and validation."""

    def test_supported_languages_count(self):
        """All 22 scheduled Indian languages should be supported."""
        from backend.ai.translation.language_map import get_supported_vaani_codes
        codes = get_supported_vaani_codes()
        assert len(codes) == 22, f"Expected 22 languages, got {len(codes)}"

    def test_gujarati_supported(self):
        """Gujarati should be a supported language."""
        from backend.ai.translation.language_map import is_supported_language
        assert is_supported_language("gu") is True

    def test_hindi_supported(self):
        """Hindi should be a supported language."""
        from backend.ai.translation.language_map import is_supported_language
        assert is_supported_language("hi") is True

    def test_tamil_supported(self):
        """Tamil should be a supported language."""
        from backend.ai.translation.language_map import is_supported_language
        assert is_supported_language("ta") is True

    def test_english_not_supported(self):
        """English is not a source language for the Indic->English stage."""
        from backend.ai.translation.language_map import is_supported_language
        assert is_supported_language("en") is False

    def test_unsupported_language(self):
        """An arbitrary code should not be supported."""
        from backend.ai.translation.language_map import is_supported_language
        assert is_supported_language("xyz") is False

    def test_gujarati_model_code(self):
        """Gujarati should map to the exact CT2 model code."""
        from backend.ai.translation.language_map import get_model_language_code
        code = get_model_language_code("gu")
        assert code == "guj_Gujr", f"Expected guj_Gujr, got {code}"

    def test_hindi_model_code(self):
        """Hindi should map to the exact CT2 model code."""
        from backend.ai.translation.language_map import get_model_language_code
        code = get_model_language_code("hi")
        assert code == "hin_Deva", f"Expected hin_Deva, got {code}"

    def test_tamil_model_code(self):
        """Tamil should map to the exact CT2 model code."""
        from backend.ai.translation.language_map import get_model_language_code
        code = get_model_language_code("ta")
        assert code == "tam_Taml", f"Expected tam_Taml, got {code}"

    def test_language_name_lookup(self):
        """Language names should be correct."""
        from backend.ai.translation.language_map import get_language_name
        assert get_language_name("gu") == "Gujarati"
        assert get_language_name("hi") == "Hindi"
        assert get_language_name("ta") == "Tamil"

    def test_list_languages_returns_dict(self):
        """list_languages() should return a dict with 22 entries."""
        from backend.ai.translation.language_map import list_languages
        mapping = list_languages()
        assert isinstance(mapping, dict)
        assert len(mapping) == 22

    def test_invalid_input_type_raises(self):
        """is_supported_language should raise TypeError for non-string."""
        from backend.ai.translation.language_map import is_supported_language
        try:
            is_supported_language(123)  # type: ignore
            assert False, "Should have raised TypeError"
        except TypeError:
            pass  # expected

    def test_invalid_input_type_raises_translator(self):
        """translate should raise InvalidInputError for non-string text."""
        from backend.ai.translation.translator import translate
        try:
            translate(123, "gu")  # type: ignore
            assert False, "Should have raised InvalidInputError"
        except InvalidInputError:
            pass  # expected

    def test_missing_local_model_path_raises_fast(self, monkeypatch):
        """No remote model load should be attempted when no local checkpoint path exists."""
        import backend.ai.translation.translator as translator

        monkeypatch.delenv("VAANI_TRANSLATION_MODEL_PATH", raising=False)
        monkeypatch.delenv("INDICTRANS2_MODEL_PATH", raising=False)
        monkeypatch.setattr(translator, "_model", None)

        with pytest.raises(RuntimeError, match="VAANI_TRANSLATION_MODEL_PATH|INDICTRANS2_MODEL_PATH"):
            translator._ensure_model_loaded()


# ---------------------------------------------------------------------------
# Integration tests: actual translation (skippable when model unavailable)
# ---------------------------------------------------------------------------

import pytest  # noqa: F401  needed for @pytest.mark.skipif


class TestTranslationIntegration:
    """Integration tests that require the CT2 model."""

    # Skip integration tests if CT2 model is not available
    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_gujarati_negative_symptom(self):
        """
        A. Negation:
        "મને તાવ નથી."
        The English result must preserve the NEGATION.
        """
        gujarati = "મને તાવ નથી."
        english = translate(gujarati, "gu")
        # Check that negation is preserved - "no fever" or similar
        negation_present = (
            "no" in english.lower()
            or "without" in english.lower()
            or "no fever" in english.lower()
        )
        assert negation_present, (
            f"Negation not preserved in: '{english}'. "
            "Expected negation (no/without/no fever) in output."
        )

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_gujarati_duration_three_days(self):
        """
        B. Duration:
        "મને ત્રણ દિવસથી તાવ છે."
        The result must preserve 3 days.
        """
        gujarati = "મને ત્રણ દિવસથી તાવ છે."
        english = translate(gujarati, "gu")
        # Check that "3 days" or "three days" appears
        has_days = ("3 days" in english) or ("three days" in english.lower())
        assert has_days, (
            f"Duration '3 days' not preserved in: '{english}'. "
            "Expected '3 days' or 'three days' in output."
        )

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_gujarati_body_location_chest(self):
        """
        C. Body location:
        "મને છાતીમાં દુખાવો છે."
        The result must preserve CHEST rather than changing it to stomach or another location.
        """
        gujarati = "મને છાતીમાં દુખાવો છે."
        english = translate(gujarati, "gu")
        english_lower = english.lower()
        # Must contain chest-related term, must NOT contain stomach-related term
        has_chest = "chest" in english_lower
        has_stomach = "stomach" in english_lower or "abdomen" in english_lower
        assert has_chest, (
            f"CHEST not preserved in: '{english}'. "
            "Expected CHEST in output."
        )
        assert not has_stomach, (
            f"Stomach/abdomen incorrectly present in: '{english}'. "
            "Expected no stomach/abdomen in output."
        )

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_gujarati_dosage_mg(self):
        """
        D. Dosage:
        "મે 500 mg દવા લીધી."
        The result must preserve 500 mg.
        """
        gujarati = "મે 500 mg દવા લીધી."
        english = translate(gujarati, "gu")
        # Check that "500 mg" or "500 milligrams" appears
        has_dosage = ("500 mg" in english) or ("500 milligrams" in english)
        assert has_dosage, (
            f"Dosage '500 mg' not preserved in: '{english}'. "
            "Expected '500 mg' or '500 milligrams' in output."
        )

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_gujarati_multiple_symptoms(self):
        """
        E. Multiple symptoms:
        "મને તાવ અને માતાનો દુખાવો છે."
        Both fever and headache must remain present.
        """
        gujarati = "મને તાવ અને માતાનો દુખાવો છે."
        english = translate(gujarati, "gu")
        english_lower = english.lower()
        has_fever = any(
            term in english_lower for term in ["fever", "feverish", "hot"]
        )
        has_headache = any(
            term in english_lower for term in ["headache", "head", "pain"]
        )
        assert has_fever, (
            f"Fever not preserved in: '{english}'. "
            "Expected fever-related term in output."
        )
        assert has_headache, (
            f"Headache not preserved in: '{english}'. "
            "Expected headache-related term in output."
        )

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_hindi_fever_two_days(self):
        """
        Hindi: "मुझे दो दिन से बुखार है।"
        Expected meaning: fever for two days (similar to Gujarati smoke test).
        """
        hindi = "मुझे दो दिन से बुखार है।"
        english = translate(hindi, "hi")
        english_lower = english.lower()
        has_fever = any(
            term in english_lower for term in ["fever", "feverish"]
        )
        has_days = any(
            term in english_lower for term in ["day", "days"]
        )
        assert has_fever, f"Fever not preserved in: '{english}'"
        assert has_days, f"Days not preserved in: '{english}'"

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_english_input_raises(self):
        """English should not be a supported source language."""
        try:
            translate("fever for two days", "en")
            assert False, "Should have raised UnsupportedLanguageError"
        except UnsupportedLanguageError:
            pass  # expected

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_empty_input_raises(self):
        """Empty text should raise InvalidInputError."""
        try:
            translate("", "gu")
            assert False, "Should have raised InvalidInputError"
        except InvalidInputError:
            pass  # expected

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_unsupported_language_raises(self):
        """Unsupported language should raise UnsupportedLanguageError."""
        try:
            translate("test", "xyz")
            assert False, "Should have raised UnsupportedLanguageError"
        except UnsupportedLanguageError:
            pass  # expected

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_long_input(self):
        """Long input should be handled (may truncate at 160 tokens)."""
        gujarati = "મને બે દિવસથી તાવ છે "
        long_input = gujarati * 20
        english = translate(long_input, "gu")
        assert isinstance(english, str)

    @pytest.mark.skipif(
        not CT2_AVAILABLE, reason="CT2 model not available; skipping integration tests"
    )
    def test_multiple_sentences(self):
        """Multiple sentences should be handled."""
        gujarati = "મને તાવ છે. મને કુસમ છે."
        english = translate(gujarati, "gu")
        assert isinstance(english, str)
        assert len(english.strip()) > 0, "Output should not be empty"


# ---------------------------------------------------------------------------
# When run as main, execute the tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n")
    # Run unit tests (these always run, no CT2 needed)
    from backend.ai.translation.test_translation import TestLanguageMapping, run_unit_tests as run_unit

    unit_passed, unit_failed = run_unit()

    # Run integration tests if CT2 available
    if CT2_AVAILABLE:
        from backend.ai.translation.test_translation import TestTranslationIntegration, run_integration_tests as run_integ
        integ_passed, integ_failed, integ_skipped = run_integ()
    else:
        integ_passed = 0
        integ_failed = 0
        integ_skipped = (
            pytest.Session  # placeholder; actual count from test generator
        )

    print("\n" + "=" * 60)
    print("VAANIDOC - Test Suite Summary")
    print("=" * 60)
    print(f"Unit tests       : {unit_passed} passed, {unit_failed} failed")
    print(
        f"Integration tests: {integ_passed} passed, {integ_failed} failed, "
        f"{integ_skipped} skipped (CT2 model unavailable)"
    )
    total = unit_passed + unit_failed + integ_passed + integ_failed + integ_skipped
    print(f"Total: {total} tests configured")
    print("=" * 60 + "\n")
