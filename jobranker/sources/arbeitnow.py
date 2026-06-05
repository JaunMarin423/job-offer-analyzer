"""Ingest jobs from the public Arbeitnow Job Board API (free, no API key).

Docs: https://www.arbeitnow.com/api/job-board-api . The endpoint is paginated;
we follow `links.next` until we have enough jobs or run out of pages.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from ..models import Job, coerce_tags, epoch_to_iso

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def _to_job(item: dict) -> Job:
    job_types = coerce_tags(item.get("job_types"))
    return Job(
        title=item.get("title", ""),
        company=item.get("company_name", ""),
        location=item.get("location", ""),
        description=item.get("description", ""),
        url=item.get("url", ""),
        salary="",
        job_type=", ".join(job_types),
        category="",
        tags=coerce_tags(item.get("tags")),
        publication_date=epoch_to_iso(item.get("created_at")),
        source="arbeitnow",
    )


def fetch_arbeitnow(search: Optional[str] = None,
                    limit: Optional[int] = 100,
                    remote_only: bool = False,
                    timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from Arbeitnow.

    Arbeitnow has no server-side search param, so `search` filters client-side.
    `remote_only` keeps only postings flagged as remote.
    """
    jobs: List[Job] = []
    url: Optional[str] = API_URL
    pages = 0
    while url and pages < 10:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            if remote_only and str(item.get("remote")).lower() != "true":
                continue
            jobs.append(_to_job(item))
        if limit and len(jobs) >= limit:
            break
        url = (data.get("links") or {}).get("next")
        pages += 1
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.searchable_text()]
    if limit:
        jobs = jobs[:limit]
    return jobs
