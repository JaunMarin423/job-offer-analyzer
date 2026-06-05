"""Core data models shared across the package."""

from __future__ import annotations

import ast
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .language import detect_language
from .salary import SalaryInfo, parse_salary_string

_TAG_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def fix_mojibake(text: str) -> str:
    """Repair UTF-8 text that was double-encoded as Latin-1 (e.g. 'Ã¡' -> 'á').

    Some feeds (notably RemoteOK) store already-mangled strings. We only attempt
    the round-trip when the tell-tale 'Ã'/'Â' sequences are present, and keep the
    original if the repair fails.
    """
    if not text or ("Ã" not in text and "Â" not in text):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def strip_html(text: str) -> str:
    """Remove HTML tags/entities and collapse whitespace (descriptions are HTML)."""
    if not text:
        return ""
    cleaned = fix_mojibake(text)
    return _WS.sub(" ", html.unescape(_TAG_HTML.sub(" ", cleaned))).strip()


def coerce_tags(raw) -> List[str]:
    """Normalize tags from a list, JSON list, Python-repr list, or CSV string."""
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str) and raw.strip():
        s = html.unescape(raw.strip())
        if s.startswith("["):
            for parser in (json.loads, ast.literal_eval):
                try:
                    val = parser(s)
                    if isinstance(val, list):
                        return [str(t).strip() for t in val if str(t).strip()]
                except (ValueError, SyntaxError):
                    continue
        return [t.strip() for t in s.split(",") if t.strip()]
    return []


def epoch_to_iso(value) -> str:
    """Convert a unix-epoch (int or numeric string) to an ISO-8601 UTC string."""
    try:
        ts = int(float(value))
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


@dataclass
class Job:
    """A normalized job posting from any source."""

    title: str
    company: str = ""
    location: str = ""
    description: str = ""
    url: str = ""
    salary: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = ""
    salary_period: str = ""
    job_type: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    publication_date: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        self.title = fix_mojibake(self.title)
        self.company = fix_mojibake(self.company)
        self.location = fix_mojibake(self.location)
        self.category = fix_mojibake(self.category)
        self.tags = [fix_mojibake(t) for t in self.tags]

    def salary_info(self) -> Optional[SalaryInfo]:
        """Structured salary if available, else parsed from the free-form string."""
        if self.salary_min or self.salary_max:
            return SalaryInfo(
                min_amount=self.salary_min,
                max_amount=self.salary_max,
                currency=self.salary_currency or "USD",
                period=self.salary_period or "yearly",
            )
        return parse_salary_string(self.salary)

    def language(self) -> str:
        """Detected language code ('es'/'en'/'other'), cached per instance."""
        cached = self.__dict__.get("_language")
        if cached is None:
            cached = detect_language(self.title + " " + strip_html(self.description))
            self.__dict__["_language"] = cached
        return cached

    def searchable_text(self) -> str:
        """Lowercased blob used for keyword/skill matching."""
        parts = [
            self.title,
            self.company,
            self.category,
            " ".join(self.tags),
            strip_html(self.description),
        ]
        return " ".join(p for p in parts if p).lower()


@dataclass
class CVProfile:
    """A candidate profile extracted from a CV plus user preferences."""

    raw_text: str = ""
    skills: List[str] = field(default_factory=list)
    target_roles: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    seniority: Optional[str] = None  # e.g. "junior", "mid", "senior"
    languages: List[str] = field(default_factory=list)  # preferred codes, e.g. ["es"]

    def normalized_skills(self) -> List[str]:
        seen = []
        for s in self.skills:
            s = s.strip().lower()
            if s and s not in seen:
                seen.append(s)
        return seen
