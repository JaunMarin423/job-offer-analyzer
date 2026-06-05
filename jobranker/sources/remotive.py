"""Ingest jobs from the public Remotive API.

Remotive's API is free and key-less. Per their legal notice we link back to the
original Remotive URL and credit Remotive as the source; we do not republish
their listings to third parties.
"""

from __future__ import annotations

import ast
from typing import List, Optional

import requests

from ..models import Job

API_URL = "https://remotive.com/api/remote-jobs"


def _parse_tags(raw) -> List[str]:
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str) and raw:
        try:
            val = ast.literal_eval(raw)
            if isinstance(val, list):
                return [str(t) for t in val]
        except (ValueError, SyntaxError):
            return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _to_job(item: dict) -> Job:
    return Job(
        title=item.get("title", ""),
        company=item.get("company_name", ""),
        location=item.get("candidate_required_location", ""),
        description=item.get("description", ""),
        url=item.get("url", ""),
        salary=item.get("salary", ""),
        job_type=item.get("job_type", ""),
        category=item.get("category", ""),
        tags=_parse_tags(item.get("tags")),
        publication_date=item.get("publication_date", ""),
        source="remotive",
    )


def fetch_remotive(search: Optional[str] = None,
                   category: Optional[str] = None,
                   limit: Optional[int] = None,
                   timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from Remotive.

    Args:
        search: free-text query (e.g. "python backend").
        category: Remotive category slug (e.g. "software-dev").
        limit: max number of jobs to return from the API.
    """
    params = {}
    if search:
        params["search"] = search
    if category:
        params["category"] = category
    if limit:
        params["limit"] = limit
    resp = requests.get(API_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return [_to_job(item) for item in data.get("jobs", [])]
