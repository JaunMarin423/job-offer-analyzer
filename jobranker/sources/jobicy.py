"""Ingest jobs from the public Jobicy API (free, no API key).

Docs: https://jobicy.com/jobicy-job-feed-api . Supports server-side filters:
`count` (max 50), `tag` (keyword), `geo` (region) and `industry`.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from ..models import Job, coerce_tags

API_URL = "https://jobicy.com/api/v2/remote-jobs"


def _num(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n or None


def _to_job(item: dict) -> Job:
    industries = coerce_tags(item.get("jobIndustry"))
    job_types = coerce_tags(item.get("jobType"))
    return Job(
        title=item.get("jobTitle", ""),
        company=item.get("companyName", ""),
        location=item.get("jobGeo", ""),
        description=item.get("jobDescription", "") or item.get("jobExcerpt", ""),
        url=item.get("url", ""),
        salary="",
        salary_min=_num(item.get("salaryMin")),
        salary_max=_num(item.get("salaryMax")),
        salary_currency=item.get("salaryCurrency", "") or "",
        salary_period=item.get("salaryPeriod", "") or "",
        job_type=", ".join(job_types),
        category=", ".join(industries),
        tags=industries,
        publication_date=item.get("pubDate", ""),
        source="jobicy",
    )


def fetch_jobicy(search: Optional[str] = None,
                 geo: Optional[str] = None,
                 industry: Optional[str] = None,
                 limit: Optional[int] = 50,
                 timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from Jobicy.

    `search` maps to Jobicy's `tag` keyword filter (server-side). `geo` and
    `industry` are optional server-side filters.
    """
    params = {}
    # Jobicy caps `count` at 50.
    params["count"] = min(limit or 50, 50)
    if search:
        params["tag"] = search
    if geo:
        params["geo"] = geo
    if industry:
        params["industry"] = industry
    resp = requests.get(API_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return [_to_job(item) for item in data.get("jobs", [])]
