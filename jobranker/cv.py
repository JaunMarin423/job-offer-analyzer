"""Read a CV from disk (txt/md/pdf) or raw text and extract a CVProfile."""

from __future__ import annotations

import os
import re
from typing import List, Optional

from .language import normalize_language_code
from .models import CVProfile

# Curated catalog of skills/technologies to detect in free-form CV text.
# Keep multi-word entries first so they are matched as a unit.
SKILL_CATALOG: List[str] = [
    # languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "kotlin", "swift", "scala", "r", "matlab", "bash",
    "sql", "html", "css", "dart",
    # web / frameworks
    "react", "react native", "next.js", "vue", "angular", "svelte", "node.js",
    "express", "django", "flask", "fastapi", "spring", "spring boot", "rails",
    "laravel", "dotnet", ".net", "tailwind", "redux", "graphql", "rest api",
    # data / ml
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "machine learning", "deep learning", "data analysis", "data science",
    "nlp", "computer vision", "spark", "hadoop", "airflow", "dbt", "etl",
    "power bi", "tableau", "looker", "excel", "statistics",
    # databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
    "elasticsearch", "cassandra", "dynamodb", "snowflake", "bigquery",
    # cloud / devops
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "github actions", "gitlab ci", "ci/cd", "linux",
    "nginx", "kafka", "rabbitmq", "serverless", "lambda",
    # tools / methods
    "git", "jira", "agile", "scrum", "kanban", "rest", "microservices",
    "oauth", "unit testing", "tdd", "selenium", "playwright", "figma",
    # soft / business
    "project management", "leadership", "communication", "sales", "marketing",
    "seo", "customer support", "product management",
]


def read_cv_text(path_or_text: str) -> str:
    """Return raw text from a CV path (.txt/.md/.pdf) or treat input as text."""
    if os.path.exists(path_or_text):
        ext = os.path.splitext(path_or_text)[1].lower()
        if ext == ".pdf":
            return _read_pdf(path_or_text)
        with open(path_or_text, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    # Not a path: treat the argument itself as CV text.
    return path_or_text


def _read_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Reading PDF CVs requires the 'pdf' extra. Install with: "
            "pip install 'jobranker[pdf]'"
        ) from exc
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_skills(text: str, extra_skills: Optional[List[str]] = None) -> List[str]:
    """Detect known skills present in the CV text (case-insensitive, word-aware)."""
    blob = text.lower()
    found: List[str] = []
    catalog = list(SKILL_CATALOG)
    if extra_skills:
        catalog = [s.lower() for s in extra_skills] + catalog
    for skill in catalog:
        if _contains_term(blob, skill) and skill not in found:
            found.append(skill)
    return found


def _contains_term(blob: str, term: str) -> bool:
    """Whole-token match that tolerates symbols like c++, c#, .net, node.js."""
    escaped = re.escape(term)
    # Allow the term to be bounded by non-alphanumeric chars or string ends.
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, blob) is not None


def build_profile(
    cv_path_or_text: str,
    target_roles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    seniority: Optional[str] = None,
    extra_skills: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
) -> CVProfile:
    text = read_cv_text(cv_path_or_text)
    skills = extract_skills(text, extra_skills=extra_skills)
    return CVProfile(
        raw_text=text,
        skills=skills,
        target_roles=[r.strip().lower() for r in (target_roles or []) if r.strip()],
        locations=[l.strip().lower() for l in (locations or []) if l.strip()],
        seniority=(seniority or _infer_seniority(text)),
        languages=[normalize_language_code(x) for x in (languages or []) if x.strip()],
    )


def _infer_seniority(text: str) -> Optional[str]:
    blob = text.lower()
    senior_terms = ["senior", "lead", "principal", "staff engineer"]
    junior_terms = ["junior", "intern", "entry level", "trainee"]
    if any(_contains_term(blob, t) for t in senior_terms):
        return "senior"
    if any(_contains_term(blob, t) for t in junior_terms):
        return "junior"
    return None
