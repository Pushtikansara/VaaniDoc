import { SUPPORTED_LANGUAGES } from "../src/languages.js";

const codes = SUPPORTED_LANGUAGES.map((item) => item.code);
const uniqueCodes = new Set(codes);

if (SUPPORTED_LANGUAGES.length !== 22) {
  throw new Error(`Expected 22 languages, found ${SUPPORTED_LANGUAGES.length}`);
}

if (uniqueCodes.size !== 22) {
  throw new Error("Language codes must be unique");
}

console.log("Language check passed:", codes.join(", "));
