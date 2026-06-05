"""Lightweight, dependency-free language detection (Spanish / English / other).

Most free remote-job feeds publish in English, so we only need a robust
es/en discriminator plus an "other" fallback. The heuristic counts common
stop-words and Spanish-only characters; it is deterministic and offline.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-záéíóúñüãõç]+", re.IGNORECASE)

_ES_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "los", "del", "las", "un", "por",
    "con", "una", "su", "para", "es", "al", "lo", "como", "más", "pero",
    "sus", "le", "ya", "o", "este", "sí", "porque", "esta", "entre", "cuando",
    "muy", "sin", "sobre", "también", "me", "hasta", "hay", "donde", "quien",
    "desde", "todo", "nos", "durante", "uno", "ni", "contra", "ese", "eso",
    "ante", "ellos", "e", "esto", "trabajo", "empresa", "experiencia",
    "desarrollador", "ingeniero", "conocimientos", "requisitos", "buscamos",
    "ofrecemos", "equipo", "años", "nuestro", "nuestra", "puesto",
}

_EN_STOPWORDS = {
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it", "as",
    "with", "was", "on", "are", "you", "this", "be", "at", "or", "have",
    "from", "we", "your", "an", "will", "our", "they", "their", "has",
    "work", "team", "experience", "company", "role", "skills", "requirements",
    "looking", "developer", "engineer", "years", "join", "build", "remote",
}

# Portuguese shares much vocabulary with Spanish, so we track it separately to
# avoid mislabelling Brazilian/Portuguese offers as Spanish.
_PT_STOPWORDS = {
    "você", "voce", "não", "nao", "são", "sao", "também", "tambem", "vaga",
    "vagas", "trabalho", "experiência", "experiencia", "conhecimento", "nós",
    "nos", "uma", "com", "para", "em", "do", "da", "dos", "das", "no", "na",
    "ção", "ões", "obrigado", "candidato", "empresa", "atuação", "atividades",
    "responsável", "salário", "currículo", "contratação", "ensino", "área",
}

_ES_CHARS = set("ñ¿¡")  # Spanish-only markers (accents alone are shared w/ pt)
_PT_CHARS = set("ãõ")
_PT_HINTS = ("ção", "ções", "ão", "ões", "não", "você")


def detect_language(text: str) -> str:
    """Return 'es', 'en', 'pt', or 'other' for the given text."""
    if not text:
        return "other"
    lowered = text.lower()
    tokens = _TOKEN.findall(lowered)
    if not tokens:
        return "other"
    es_hits = sum(1 for t in tokens if t in _ES_STOPWORDS)
    en_hits = sum(1 for t in tokens if t in _EN_STOPWORDS)
    pt_hits = sum(1 for t in tokens if t in _PT_STOPWORDS)
    if any(c in _ES_CHARS for c in lowered):
        es_hits += 2
    if any(c in _PT_CHARS for c in lowered):
        pt_hits += 3
    pt_hits += sum(lowered.count(h) for h in _PT_HINTS)

    scores = {"es": es_hits, "en": en_hits, "pt": pt_hits}
    best = max(scores, key=lambda k: scores[k])
    if scores[best] < 2:
        return "other"
    return best


_LANG_ALIASES = {
    "es": "es", "spanish": "es", "español": "es", "espanol": "es", "castellano": "es",
    "en": "en", "english": "en", "inglés": "en", "ingles": "en",
}

LANGUAGE_NAMES = {"es": "Español", "en": "English", "pt": "Português", "other": "Otro"}


def normalize_language_code(value: str) -> str:
    """Map a user-supplied language name/code to a canonical code (es/en/...)."""
    return _LANG_ALIASES.get(value.strip().lower(), value.strip().lower())
