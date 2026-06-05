"""Core data models shared across the package."""

from __future__ import annotations

import ast
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

_TAG_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags/entities and collapse whitespace (descriptions are HTML)."""
    if not text:
        return ""
    return _WS.sub(" ", html.unescape(_TAG_HTML.sub(" ", text))).strip()


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
    job_type: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    publication_date: str = ""
    source: str = ""

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

    def normalized_skills(self) -> List[str]:
        seen = []
        for s in self.skills:
            s = s.strip().lower()
            if s and s not in seen:
                seen.append(s)
        return seen
