"""Clinical symptom knowledge base for VaaniDoc.

A curated dictionary of common primary-care symptoms, each with:
  - canonical snake_case name
  - list of English synonym phrases a patient might use
  - broad clinical category

This module is a **static knowledge base** only.  It does NOT perform
text extraction, NLP, or fuzzy matching.
"""

from __future__ import annotations

import re
from typing import Optional


# ── type alias ───────────────────────────────────────────────────────

SymptomEntry = dict  # {"synonyms": list[str], "category": str}


# ── whitespace normaliser ────────────────────────────────────────────

_MULTI_WS = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Lowercase, strip, and collapse repeated whitespace."""
    return _MULTI_WS.sub(" ", text.strip().lower())


# =====================================================================
#  SYMPTOM KNOWLEDGE BASE
# =====================================================================
# Rules:
#   • Every key is a canonical snake_case symptom name.
#   • "synonyms" — realistic English phrases a patient might say.
#   • "category" — exactly one of the nine broad categories.
#   • NO diagnoses (no diabetes, pneumonia, migraine, etc.).
#   • NO duplicate canonical names.
# =====================================================================

SYMPTOM_DB: dict[str, SymptomEntry] = {

    # ── NEUROLOGICAL ─────────────────────────────────────────────────

    "headache": {
        "synonyms": [
            "headache",
            "head pain",
            "pain in my head",
            "my head hurts",
            "head is pounding",
            "throbbing head",
        ],
        "category": "Neurological",
    },
    "dizziness": {
        "synonyms": [
            "dizziness",
            "dizzy",
            "feeling dizzy",
            "lightheaded",
            "light headed",
            "feeling lightheaded",
            "room is spinning",
        ],
        "category": "Neurological",
    },
    "fainting": {
        "synonyms": [
            "fainting",
            "fainted",
            "passed out",
            "lost consciousness",
            "blacked out",
            "nearly fainted",
        ],
        "category": "Neurological",
    },
    "seizure": {
        "synonyms": [
            "seizure",
            "seizures",
            "fits",
            "convulsion",
            "convulsions",
        ],
        "category": "Neurological",
    },
    "confusion": {
        "synonyms": [
            "confusion",
            "confused",
            "feeling confused",
            "disoriented",
            "disorientation",
            "cannot think clearly",
        ],
        "category": "Neurological",
    },
    "numbness": {
        "synonyms": [
            "numbness",
            "numb",
            "feeling numb",
            "loss of sensation",
            "no feeling",
            "cannot feel",
        ],
        "category": "Neurological",
    },
    "tingling": {
        "synonyms": [
            "tingling",
            "pins and needles",
            "prickling",
            "tingling sensation",
        ],
        "category": "Neurological",
    },
    "tremor": {
        "synonyms": [
            "tremor",
            "tremors",
            "shaking",
            "shaking hands",
            "hands are shaking",
            "trembling",
        ],
        "category": "Neurological",
    },
    "memory_loss": {
        "synonyms": [
            "memory loss",
            "forgetfulness",
            "forgetting things",
            "cannot remember",
            "memory problems",
        ],
        "category": "Neurological",
    },

    # ── RESPIRATORY ──────────────────────────────────────────────────

    "cough": {
        "synonyms": [
            "cough",
            "coughing",
            "dry cough",
            "wet cough",
            "persistent cough",
            "keeps coughing",
        ],
        "category": "Respiratory",
    },
    "shortness_of_breath": {
        "synonyms": [
            "shortness of breath",
            "breathlessness",
            "breathless",
            "difficulty breathing",
            "breathing difficulty",
            "trouble breathing",
            "cannot breathe properly",
            "hard to breathe",
            "out of breath",
            "gasping for air",
        ],
        "category": "Respiratory",
    },
    "wheezing": {
        "synonyms": [
            "wheezing",
            "wheeze",
            "whistling sound when breathing",
            "noisy breathing",
        ],
        "category": "Respiratory",
    },
    "sore_throat": {
        "synonyms": [
            "sore throat",
            "throat pain",
            "pain in my throat",
            "my throat hurts",
            "scratchy throat",
            "throat irritation",
        ],
        "category": "Respiratory",
    },
    "runny_nose": {
        "synonyms": [
            "runny nose",
            "nose is running",
            "running nose",
            "nasal discharge",
            "watery nose",
        ],
        "category": "Respiratory",
    },
    "nasal_congestion": {
        "synonyms": [
            "nasal congestion",
            "stuffy nose",
            "blocked nose",
            "nose is blocked",
            "congested nose",
            "cannot breathe through nose",
        ],
        "category": "Respiratory",
    },
    "sneezing": {
        "synonyms": [
            "sneezing",
            "sneezes",
            "keeps sneezing",
            "frequent sneezing",
        ],
        "category": "Respiratory",
    },
    "chest_congestion": {
        "synonyms": [
            "chest congestion",
            "congested chest",
            "phlegm in chest",
            "mucus in chest",
        ],
        "category": "Respiratory",
    },

    # ── CARDIOVASCULAR ───────────────────────────────────────────────

    "chest_pain": {
        "synonyms": [
            "chest pain",
            "pain in my chest",
            "my chest hurts",
            "chest tightness",
            "tight chest",
            "pressure in chest",
            "chest discomfort",
        ],
        "category": "Cardiovascular",
    },
    "palpitations": {
        "synonyms": [
            "palpitations",
            "heart palpitations",
            "heart is racing",
            "heart pounding",
            "can feel my heartbeat",
            "irregular heartbeat",
            "heart skipping beats",
        ],
        "category": "Cardiovascular",
    },
    "rapid_heartbeat": {
        "synonyms": [
            "rapid heartbeat",
            "fast heartbeat",
            "fast heart rate",
            "heart beating fast",
            "tachycardia",
        ],
        "category": "Cardiovascular",
    },
    "slow_heartbeat": {
        "synonyms": [
            "slow heartbeat",
            "slow heart rate",
            "heart beating slowly",
        ],
        "category": "Cardiovascular",
    },
    "leg_swelling": {
        "synonyms": [
            "leg swelling",
            "swollen legs",
            "swollen leg",
            "legs are swollen",
            "ankle swelling",
            "swollen ankles",
            "feet swelling",
            "swollen feet",
        ],
        "category": "Cardiovascular",
    },

    # ── GASTROINTESTINAL ─────────────────────────────────────────────

    "abdominal_pain": {
        "synonyms": [
            "abdominal pain",
            "stomach pain",
            "belly pain",
            "pain in my stomach",
            "pain in my abdomen",
            "tummy pain",
            "stomach ache",
            "stomachache",
            "my stomach hurts",
        ],
        "category": "Gastrointestinal",
    },
    "nausea": {
        "synonyms": [
            "nausea",
            "nauseous",
            "feeling nauseous",
            "feeling sick",
            "queasy",
            "feel like vomiting",
        ],
        "category": "Gastrointestinal",
    },
    "vomiting": {
        "synonyms": [
            "vomiting",
            "vomit",
            "throwing up",
            "throwing up food",
            "puking",
            "been vomiting",
        ],
        "category": "Gastrointestinal",
    },
    "diarrhea": {
        "synonyms": [
            "diarrhea",
            "diarrhoea",
            "loose stools",
            "loose motions",
            "watery stools",
            "frequent loose stools",
            "runny stool",
        ],
        "category": "Gastrointestinal",
    },
    "constipation": {
        "synonyms": [
            "constipation",
            "constipated",
            "cannot pass stool",
            "difficulty passing stool",
            "hard stool",
            "not able to go to the bathroom",
        ],
        "category": "Gastrointestinal",
    },
    "bloating": {
        "synonyms": [
            "bloating",
            "bloated",
            "feeling bloated",
            "stomach bloating",
            "abdominal bloating",
            "gas",
            "gassy",
        ],
        "category": "Gastrointestinal",
    },
    "loss_of_appetite": {
        "synonyms": [
            "loss of appetite",
            "no appetite",
            "not hungry",
            "do not feel like eating",
            "cannot eat",
            "poor appetite",
        ],
        "category": "Gastrointestinal",
    },
    "heartburn": {
        "synonyms": [
            "heartburn",
            "acid reflux",
            "burning in chest",
            "burning sensation in chest",
            "acidity",
        ],
        "category": "Gastrointestinal",
    },
    "indigestion": {
        "synonyms": [
            "indigestion",
            "upset stomach",
            "stomach upset",
            "difficulty digesting",
            "dyspepsia",
        ],
        "category": "Gastrointestinal",
    },
    "blood_in_stool": {
        "synonyms": [
            "blood in stool",
            "bloody stool",
            "blood in my stool",
            "bleeding from rectum",
            "rectal bleeding",
        ],
        "category": "Gastrointestinal",
    },
    "difficulty_swallowing": {
        "synonyms": [
            "difficulty swallowing",
            "trouble swallowing",
            "cannot swallow",
            "hard to swallow",
            "food gets stuck",
        ],
        "category": "Gastrointestinal",
    },

    # ── GENERAL ──────────────────────────────────────────────────────

    "fever": {
        "synonyms": [
            "fever",
            "high temperature",
            "temperature",
            "feeling feverish",
            "feverish",
            "running a fever",
            "high fever",
        ],
        "category": "General",
    },
    "chills": {
        "synonyms": [
            "chills",
            "chilling",
            "feeling cold",
            "shivering",
            "cold shivers",
            "rigors",
        ],
        "category": "General",
    },
    "fatigue": {
        "synonyms": [
            "fatigue",
            "tiredness",
            "tired",
            "feeling tired",
            "exhaustion",
            "exhausted",
            "feeling exhausted",
            "no energy",
            "low energy",
        ],
        "category": "General",
    },
    "weakness": {
        "synonyms": [
            "weakness",
            "feeling weak",
            "weak",
            "general weakness",
            "body feels weak",
            "lack of strength",
        ],
        "category": "General",
    },
    "body_ache": {
        "synonyms": [
            "body ache",
            "body aches",
            "body pain",
            "whole body pain",
            "all over body pain",
            "aching all over",
            "generalized pain",
        ],
        "category": "General",
    },
    "weight_loss": {
        "synonyms": [
            "weight loss",
            "losing weight",
            "lost weight",
            "unintentional weight loss",
            "unexplained weight loss",
        ],
        "category": "General",
    },
    "weight_gain": {
        "synonyms": [
            "weight gain",
            "gaining weight",
            "gained weight",
            "putting on weight",
            "unexplained weight gain",
        ],
        "category": "General",
    },
    "dehydration": {
        "synonyms": [
            "dehydration",
            "dehydrated",
            "feeling dehydrated",
            "very thirsty",
            "dry mouth",
            "not enough water",
        ],
        "category": "General",
    },
    "excessive_sweating": {
        "synonyms": [
            "excessive sweating",
            "sweating a lot",
            "night sweats",
            "sweating too much",
            "profuse sweating",
        ],
        "category": "General",
    },
    "insomnia": {
        "synonyms": [
            "insomnia",
            "cannot sleep",
            "difficulty sleeping",
            "trouble sleeping",
            "sleeplessness",
            "not able to sleep",
        ],
        "category": "General",
    },
    "swollen_lymph_nodes": {
        "synonyms": [
            "swollen lymph nodes",
            "swollen glands",
            "lumps in neck",
            "swollen nodes",
        ],
        "category": "General",
    },

    # ── MUSCULOSKELETAL ──────────────────────────────────────────────

    "back_pain": {
        "synonyms": [
            "back pain",
            "pain in my back",
            "my back hurts",
            "lower back pain",
            "upper back pain",
            "backache",
        ],
        "category": "Musculoskeletal",
    },
    "neck_pain": {
        "synonyms": [
            "neck pain",
            "pain in my neck",
            "my neck hurts",
            "stiff neck",
            "neck stiffness",
        ],
        "category": "Musculoskeletal",
    },
    "joint_pain": {
        "synonyms": [
            "joint pain",
            "pain in joints",
            "my joints hurt",
            "aching joints",
            "painful joints",
        ],
        "category": "Musculoskeletal",
    },
    "muscle_pain": {
        "synonyms": [
            "muscle pain",
            "muscle ache",
            "sore muscles",
            "muscles are sore",
            "myalgia",
        ],
        "category": "Musculoskeletal",
    },
    "muscle_cramps": {
        "synonyms": [
            "muscle cramps",
            "cramps",
            "muscle cramping",
            "leg cramps",
            "muscle spasm",
            "spasms",
        ],
        "category": "Musculoskeletal",
    },
    "joint_swelling": {
        "synonyms": [
            "joint swelling",
            "swollen joint",
            "swollen joints",
            "joints are swollen",
        ],
        "category": "Musculoskeletal",
    },
    "difficulty_walking": {
        "synonyms": [
            "difficulty walking",
            "trouble walking",
            "cannot walk properly",
            "hard to walk",
            "limping",
            "unsteady walk",
        ],
        "category": "Musculoskeletal",
    },
    "shoulder_pain": {
        "synonyms": [
            "shoulder pain",
            "pain in my shoulder",
            "my shoulder hurts",
            "shoulder ache",
        ],
        "category": "Musculoskeletal",
    },
    "knee_pain": {
        "synonyms": [
            "knee pain",
            "pain in my knee",
            "my knee hurts",
            "sore knee",
        ],
        "category": "Musculoskeletal",
    },

    # ── DERMATOLOGICAL ───────────────────────────────────────────────

    "rash": {
        "synonyms": [
            "rash",
            "skin rash",
            "rashes",
            "rash on skin",
            "red patches on skin",
            "spots on skin",
        ],
        "category": "Dermatological",
    },
    "itching": {
        "synonyms": [
            "itching",
            "itchy",
            "itchy skin",
            "itchiness",
            "skin itching",
            "scratching a lot",
        ],
        "category": "Dermatological",
    },
    "skin_redness": {
        "synonyms": [
            "skin redness",
            "redness on skin",
            "red skin",
            "skin is red",
        ],
        "category": "Dermatological",
    },
    "skin_swelling": {
        "synonyms": [
            "skin swelling",
            "swelling on skin",
            "swollen skin",
            "puffy skin",
        ],
        "category": "Dermatological",
    },
    "skin_pain": {
        "synonyms": [
            "skin pain",
            "painful skin",
            "skin hurts",
            "tender skin",
            "skin tenderness",
        ],
        "category": "Dermatological",
    },
    "skin_dryness": {
        "synonyms": [
            "skin dryness",
            "dry skin",
            "flaky skin",
            "skin is dry",
            "cracked skin",
        ],
        "category": "Dermatological",
    },
    "skin_lesion": {
        "synonyms": [
            "skin lesion",
            "skin sore",
            "skin wound",
            "open sore on skin",
            "skin ulcer",
        ],
        "category": "Dermatological",
    },

    # ── URINARY ──────────────────────────────────────────────────────

    "painful_urination": {
        "synonyms": [
            "painful urination",
            "pain when urinating",
            "burning urination",
            "burning when urinating",
            "it hurts to urinate",
            "pain during urination",
        ],
        "category": "Urinary",
    },
    "frequent_urination": {
        "synonyms": [
            "frequent urination",
            "urinating frequently",
            "going to the bathroom often",
            "peeing a lot",
            "need to urinate often",
        ],
        "category": "Urinary",
    },
    "blood_in_urine": {
        "synonyms": [
            "blood in urine",
            "bloody urine",
            "blood in my urine",
            "red urine",
            "urine has blood",
        ],
        "category": "Urinary",
    },
    "difficulty_urinating": {
        "synonyms": [
            "difficulty urinating",
            "trouble urinating",
            "cannot urinate",
            "hard to urinate",
            "weak urine stream",
        ],
        "category": "Urinary",
    },

    # ── ENT (Eye / Ear / Nose / Throat) ──────────────────────────────

    "eye_pain": {
        "synonyms": [
            "eye pain",
            "pain in my eye",
            "my eye hurts",
            "eyes are hurting",
            "sore eyes",
        ],
        "category": "ENT",
    },
    "blurred_vision": {
        "synonyms": [
            "blurred vision",
            "blurry vision",
            "cannot see clearly",
            "vision is blurry",
            "cloudy vision",
            "fuzzy vision",
        ],
        "category": "ENT",
    },
    "eye_redness": {
        "synonyms": [
            "eye redness",
            "red eyes",
            "red eye",
            "eyes are red",
            "bloodshot eyes",
        ],
        "category": "ENT",
    },
    "ear_pain": {
        "synonyms": [
            "ear pain",
            "earache",
            "pain in my ear",
            "my ear hurts",
            "ear ache",
        ],
        "category": "ENT",
    },
    "hearing_loss": {
        "synonyms": [
            "hearing loss",
            "cannot hear",
            "hard of hearing",
            "difficulty hearing",
            "hearing problem",
            "reduced hearing",
        ],
        "category": "ENT",
    },
    "ringing_in_ears": {
        "synonyms": [
            "ringing in ears",
            "ringing in my ears",
            "tinnitus",
            "buzzing in ears",
            "ear ringing",
        ],
        "category": "ENT",
    },
}


# =====================================================================
#  HELPER FUNCTIONS
# =====================================================================


def get_symptom(canonical_name: str) -> Optional[SymptomEntry]:
    """Return the symptom definition for *canonical_name*, or ``None``."""
    return SYMPTOM_DB.get(canonical_name)


def get_all_symptoms() -> dict[str, SymptomEntry]:
    """Return the entire symptom dictionary (read-only reference)."""
    return SYMPTOM_DB


def get_category(canonical_name: str) -> Optional[str]:
    """Return the broad clinical category for a canonical symptom."""
    entry = SYMPTOM_DB.get(canonical_name)
    return entry["category"] if entry else None


def get_synonyms(canonical_name: str) -> Optional[list[str]]:
    """Return the synonym list for a canonical symptom."""
    entry = SYMPTOM_DB.get(canonical_name)
    return entry["synonyms"] if entry else None


# ── reverse synonym index ────────────────────────────────────────────

_synonym_index: Optional[dict[str, str]] = None


def build_synonym_index() -> dict[str, str]:
    """Build (or return cached) reverse lookup: normalised phrase → canonical name.

    The index is case-insensitive and whitespace-normalised.
    """
    global _synonym_index
    if _synonym_index is not None:
        return _synonym_index

    index: dict[str, str] = {}
    for canonical, entry in SYMPTOM_DB.items():
        for phrase in entry["synonyms"]:
            key = _normalise(phrase)
            index[key] = canonical
    _synonym_index = index
    return _synonym_index


def lookup_synonym(phrase: str) -> Optional[str]:
    """Look up a patient phrase and return the canonical symptom, or ``None``.

    Matching is case-insensitive and whitespace-normalised.
    """
    index = build_synonym_index()
    return index.get(_normalise(phrase))
