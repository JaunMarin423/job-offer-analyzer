"""Ingest jobs from the public RemoteOK API (free, no API key).

RemoteOK requires a descriptive User-Agent and, per their API terms, a
do-follow link back to the job URL and credit to "Remote OK" as the source.
The first element of the response is a legal/metadata object and is skipped.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from ..models import Job, coerce_tags

API_URL = "https://remoteok.com/api"
USER_AGENT = "jobranker/0.1 (+https://github.com/JaunMarin423/job-offer-analyzer)"


def _sane_salary(item: dict):
    """Return (min, max) only when the values look like real annual figures.

    RemoteOK frequently returns tiny placeholder numbers (e.g. 15, 27), so we
    require a maximum of at least 1000 before trusting the salary.
    """
    lo, hi = item.get("salary_min") or 0, item.get("salary_max") or 0
    if hi and hi >= 1000:
        return float(lo) or None, float(hi)
    return None, None


def _to_job(item: dict) -> Job:
    lo, hi = _sane_salary(item)
    return Job(
        title=item.get("position", "") or item.get("title", ""),
        company=item.get("company", ""),
        location=item.get("location", "") or "Remote",
        description=item.get("description", ""),
        url=item.get("url", "") or item.get("apply_url", ""),
        salary="",
        salary_min=lo,
        salary_max=hi,
        salary_currency="USD" if hi else "",
        salary_period="yearly" if hi else "",
        job_type="",
        category="",
        tags=coerce_tags(item.get("tags")),
        publication_date=item.get("date", ""),
        source="remoteok",
    )


def fetch_remoteok(search: Optional[str] = None,
                   limit: Optional[int] = None,
                   timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from RemoteOK.

    The API has no server-side search, so `search` filters client-side against
    the title, tags and description.
    """
    resp = requests.get(API_URL, headers={"User-Agent": USER_AGENT},
                        timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # First element is the legal/metadata notice.
    items = [it for it in data if isinstance(it, dict) and it.get("id")]
    jobs = [_to_job(it) for it in items]
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.searchable_text()]
    if limit:
        jobs = jobs[:limit]
    return jobs
