"""Deterministic language choice; an uncertain source needs human confirmation."""
import re
from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0
SUPPORTED_LANGUAGES = {"ro": "română", "en": "English", "fr": "français", "de": "Deutsch", "es": "español", "it": "italiano"}


class LanguageAmbiguous(ValueError):
    def __init__(self, detection):
        self.detection = detection
        super().__init__("Limba documentului nu este sigură. Confirmă limba sursei înainte de generare.")


def detect_document_language(text):
    sample = re.sub(r"https?://\S+|\b[\w.]+@[\w.]+\b", " ", text)
    words = re.findall(r"[^\W\d_]+", sample, re.UNICODE)
    short = len(words) < 20 or sum(map(len, words)) < 100
    try:
        candidates = detect_langs(sample[:20000])
    except LangDetectException:
        candidates = []
    top = candidates[0] if candidates else None
    mixed = False
    if len(sample) > 1400:
        positions = [0, max(0, len(sample) // 2 - 500), max(0, len(sample) - 1000)]
        chunk_languages = set()
        for position in positions:
            try:
                result = detect_langs(sample[position:position + 1000])[0]
                if result.prob > .90:
                    chunk_languages.add(result.lang)
            except LangDetectException:
                pass
        mixed = len(chunk_languages) > 1
    return {"language": top.lang if top else None, "confidence": round(top.prob, 3) if top else 0,
            "ambiguous": short or not top or top.prob < .88 or mixed, "mixed": mixed,
            "candidates": [{"language": c.lang, "confidence": round(c.prob, 3)} for c in candidates[:3]]}


def resolve_language(text, override=None):
    result = detect_document_language(text)
    override = override.strip().lower() if override else None
    if override and override not in SUPPORTED_LANGUAGES:
        raise ValueError("Limbă nesuportată. Sunt disponibile: ro, en, fr, de, es, it.")
    if result["ambiguous"]:
        if not override:
            raise LanguageAmbiguous(result)
        result["language"] = override
        result["confirmed"] = True
    elif override and override != result["language"]:
        raise ValueError("Materialele trebuie generate în limba detectată a documentului. Traducerea nu este activată.")
    if result["language"] not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Limba detectată ({result['language']}) nu este încă suportată pentru generare. Nu vom schimba automat limba.")
    return result
