"""Core data models shared across the package."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

_TAG_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace (Remotive descriptions are HTML)."""
    if not text:
        return ""
    return _WS.sub(" ", _TAG_HTML.sub(" ", text)).strip()


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
