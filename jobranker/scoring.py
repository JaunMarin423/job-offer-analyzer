"""Score and rank jobs against a CVProfile.

The final score is a 0-100 weighted blend of interpretable components so the
ranking can always be explained to the user (why a job fits, what is missing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from .cv import _contains_term
from .models import CVProfile, Job, strip_html

# Component weights (must sum to 1.0).
WEIGHTS: Dict[str, float] = {
    "skills": 0.50,
    "role": 0.25,
    "location": 0.15,
    "seniority": 0.05,
    "recency": 0.05,
}


@dataclass
class ScoredJob:
    job: Job
    score: float
    components: Dict[str, float] = field(default_factory=dict)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


def _skill_component(profile: CVProfile, blob: str, job: Job):
    cv_skills = profile.normalized_skills()
    if not cv_skills:
        return 0.0, [], []
    matched = [s for s in cv_skills if _contains_term(blob, s)]
    fraction = len(matched) / len(cv_skills)
    # Job tags the CV does NOT cover -> "what you might be missing".
    job_tags = [t.strip().lower() for t in job.tags if t.strip()]
    missing = [t for t in job_tags if t not in cv_skills and not _contains_term(
        " ".join(cv_skills), t)]
    # Reward absolute overlap a bit so jobs matching many skills rank higher.
    abs_bonus = min(len(matched) / 8.0, 1.0)
    score = 100.0 * (0.7 * fraction + 0.3 * abs_bonus)
    return score, matched, missing[:8]


def _role_component(profile: CVProfile, job: Job) -> float:
    if not profile.target_roles:
        return 50.0  # neutral when the user gave no target role
    title = job.title.lower()
    for role in profile.target_roles:
        if role and role in title:
            return 100.0
    # partial: any significant word of a target role appears in the title
    words = {w for role in profile.target_roles for w in role.split() if len(w) > 3}
    if any(w in title for w in words):
        return 60.0
    return 0.0


def _location_component(profile: CVProfile, job: Job) -> float:
    loc = (job.location or "").lower()
    if not profile.locations:
        return 50.0
    if "worldwide" in loc or "anywhere" in loc:
        return 100.0
    for want in profile.locations:
        if want and (want in loc or loc in want):
            return 100.0
    if loc:
        return 20.0
    return 50.0


def _seniority_component(profile: CVProfile, job: Job) -> float:
    if not profile.seniority:
        return 50.0
    blob = (job.title + " " + strip_html(job.description)).lower()
    want = profile.seniority
    present = {
        "senior": any(w in blob for w in ["senior", "lead", "principal", "staff"]),
        "junior": any(w in blob for w in ["junior", "intern", "entry", "trainee"]),
    }
    if want == "senior":
        if present["senior"]:
            return 100.0
        return 30.0 if present["junior"] else 60.0
    if want == "junior":
        if present["junior"]:
            return 100.0
        return 30.0 if present["senior"] else 60.0
    return 50.0


def _recency_component(job: Job) -> float:
    if not job.publication_date:
        return 50.0
    try:
        raw = job.publication_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return 50.0
    days = (datetime.now(timezone.utc) - dt).days
    if days <= 3:
        return 100.0
    if days <= 7:
        return 85.0
    if days <= 14:
        return 70.0
    if days <= 30:
        return 50.0
    return 25.0


def score_job(profile: CVProfile, job: Job) -> ScoredJob:
    blob = job.searchable_text()
    skill_score, matched, missing = _skill_component(profile, blob, job)
    components = {
        "skills": skill_score,
        "role": _role_component(profile, job),
        "location": _location_component(profile, job),
        "seniority": _seniority_component(profile, job),
        "recency": _recency_component(job),
    }
    total = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)

    reasons: List[str] = []
    if matched:
        reasons.append(f"Matches {len(matched)} of your skills: "
                       f"{', '.join(matched[:6])}")
    if components["role"] >= 100:
        reasons.append("Title matches a target role")
    if components["location"] >= 100 and profile.locations:
        reasons.append("Location matches your preference")
    if components["recency"] >= 85:
        reasons.append("Recently posted")
    if missing:
        reasons.append(f"Possible gaps: {', '.join(missing[:5])}")

    return ScoredJob(
        job=job,
        score=round(total, 1),
        components={k: round(v, 1) for k, v in components.items()},
        matched_skills=matched,
        missing_skills=missing,
        reasons=reasons,
    )


def rank_jobs(profile: CVProfile, jobs: List[Job],
              min_score: float = 0.0) -> List[ScoredJob]:
    scored = [score_job(profile, j) for j in jobs]
    scored = [s for s in scored if s.score >= min_score]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
