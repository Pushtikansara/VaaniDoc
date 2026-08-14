export const SUPPORTED_LANGUAGES = [
  { label: "Assamese", code: "as" },
  { label: "Bengali", code: "bn" },
  { label: "Bodo", code: "brx" },
  { label: "Dogri", code: "doi" },
  { label: "Gujarati", code: "gu" },
  { label: "Hindi", code: "hi" },
  { label: "Kannada", code: "kn" },
  { label: "Kashmiri", code: "ks" },
  { label: "Konkani", code: "kok" },
  { label: "Maithili", code: "mai" },
  { label: "Malayalam", code: "ml" },
  { label: "Manipuri", code: "mni" },
  { label: "Marathi", code: "mr" },
  { label: "Nepali", code: "ne" },
  { label: "Odia", code: "or" },
  { label: "Punjabi", code: "pa" },
  { label: "Sanskrit", code: "sa" },
  { label: "Santali", code: "sat" },
  { label: "Sindhi", code: "sd" },
  { label: "Tamil", code: "ta" },
  { label: "Telugu", code: "te" },
  { label: "Urdu", code: "ur" }
];

export function assertSupportedLanguages() {
  const codes = SUPPORTED_LANGUAGES.map((item) => item.code);
  const uniqueCodes = new Set(codes);

  if (SUPPORTED_LANGUAGES.length !== 22) {
    throw new Error(`Expected 22 languages, found ${SUPPORTED_LANGUAGES.length}`);
  }

  if (uniqueCodes.size !== 22) {
    throw new Error("Language codes must be unique");
  }
}
