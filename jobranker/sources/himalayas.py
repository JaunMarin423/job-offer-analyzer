"""Ingest jobs from the public Himalayas API (free, no API key required).

Docs: https://himalayas.app/jobs/api . The endpoint returns remote jobs in
pages of 20; we follow `offset` until we have enough. Salaries are annual
amounts with a currency, which feeds the price-comparison report directly.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from ..models import Job, epoch_to_iso

API_URL = "https://himalayas.app/jobs/api"

_PAGE_SIZE = 20


def _num(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n or None


def _company_name(item: dict) -> str:
    """Himalayas occasionally returns the placeholder 'name'; fall back to slug."""
    name = (item.get("companyName") or "").strip()
    if name and name.lower() != "name":
        return name
    slug = (item.get("companySlug") or "").strip()
    return slug.replace("-", " ").title() if slug else name


def _to_job(item: dict) -> Job:
    locations = ", ".join(
        str(x) for x in (item.get("locationRestrictions") or []) if str(x).strip()
    )
    categories = [str(c) for c in (item.get("categories") or []) if str(c).strip()]
    seniority = [str(s) for s in (item.get("seniority") or []) if str(s).strip()]
    salary_min = _num(item.get("minSalary"))
    salary_max = _num(item.get("maxSalary"))
    return Job(
        title=item.get("title", ""),
        company=_company_name(item),
        location=locations,
        description=item.get("description", "") or item.get("excerpt", "") or "",
        url=item.get("applicationLink", "") or item.get("guid", ""),
        salary="",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=(item.get("currency", "") or "") if (salary_min or salary_max) else "",
        salary_period="yearly" if (salary_min or salary_max) else "",
        job_type=item.get("employmentType", "") or "",
        category=", ".join(categories),
        tags=seniority,
        publication_date=epoch_to_iso(item.get("pubDate")),
        source="himalayas",
    )


def fetch_himalayas(search: Optional[str] = None,
                    limit: Optional[int] = 100,
                    timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize remote jobs from Himalayas.

    The API has no free-text query, so `search` filters client-side. Pagination
    walks `offset` in pages of 20 until `limit` is reached or pages run out.
    """
    jobs: List[Job] = []
    offset = 0
    pages = 0
    target = limit or 100
    while pages < 25:
        params = {"limit": _PAGE_SIZE, "offset": offset}
        resp = requests.get(API_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("jobs", [])
        if not batch:
            break
        jobs.extend(_to_job(item) for item in batch)
        offset += _PAGE_SIZE
        pages += 1
        if len(jobs) >= target:
            break
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.searchable_text()]
    if limit:
        jobs = jobs[:limit]
    return jobs
