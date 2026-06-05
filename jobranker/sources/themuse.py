"""Ingest jobs from the public The Muse API (free, no API key required).

Docs: https://www.themuse.com/developers/api/v2 . The endpoint is paginated
(20 results per page) and supports server-side `category` and `level` filters.
We default to software-oriented categories so results match a developer profile;
free-text `search` is applied client-side since the public API has no `q` param.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from ..models import Job

API_URL = "https://www.themuse.com/api/public/jobs"

_DEFAULT_CATEGORIES = ("Software Engineering", "Computer and IT")


def _to_job(item: dict) -> Job:
    company = (item.get("company") or {}).get("name", "")
    locations = ", ".join(
        loc.get("name", "") for loc in item.get("locations", []) if loc.get("name")
    )
    categories = ", ".join(
        c.get("name", "") for c in item.get("categories", []) if c.get("name")
    )
    levels = [lvl.get("name", "") for lvl in item.get("levels", []) if lvl.get("name")]
    url = (item.get("refs") or {}).get("landing_page", "")
    return Job(
        title=item.get("name", ""),
        company=company,
        location=locations,
        description=item.get("contents", "") or "",
        url=url,
        salary="",
        job_type=", ".join(levels),
        category=categories,
        tags=levels,
        publication_date=item.get("publication_date", ""),
        source="themuse",
    )


def fetch_themuse(search: Optional[str] = None,
                  categories: Optional[List[str]] = None,
                  limit: Optional[int] = 100,
                  timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from The Muse.

    `categories` defaults to software-oriented ones. `search` filters the
    aggregated results client-side. Pagination stops once `limit` is reached.
    """
    wanted = categories or list(_DEFAULT_CATEGORIES)
    jobs: List[Job] = []
    for category in wanted:
        page = 1
        page_count = 1
        while page <= page_count and page <= 20:
            params = {"category": category, "page": page}
            resp = requests.get(API_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            page_count = data.get("page_count", 1) or 1
            for item in data.get("results", []):
                jobs.append(_to_job(item))
            if limit and len(jobs) >= limit:
                break
            page += 1
        if limit and len(jobs) >= limit:
            break
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.searchable_text()]
    if limit:
        jobs = jobs[:limit]
    return jobs
