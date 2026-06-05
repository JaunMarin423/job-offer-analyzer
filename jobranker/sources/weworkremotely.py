"""Ingest jobs from We Work Remotely's public RSS feeds (free, legal).

We Work Remotely publishes per-category RSS feeds (no API key). We read the
"Programming" feed by default so results match a developer profile. Per their
terms we link back to the original posting and credit We Work Remotely.
"""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

import requests

from ..models import Job

FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


def _to_iso(rfc822: str) -> str:
    if not rfc822:
        return ""
    try:
        return parsedate_to_datetime(rfc822).isoformat()
    except (TypeError, ValueError):
        return ""


def _split_title(raw: str) -> tuple[str, str]:
    """WWR titles read 'Company: Role'; split into (company, title)."""
    if ": " in raw:
        company, _, title = raw.partition(": ")
        return company.strip(), title.strip()
    return "", raw.strip()


def _text(item: ET.Element, tag: str) -> str:
    el = item.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _to_job(item: ET.Element) -> Job:
    company, title = _split_title(_text(item, "title"))
    category = _text(item, "category")
    return Job(
        title=title,
        company=company,
        location=_text(item, "region"),
        description=_text(item, "description"),
        url=_text(item, "link"),
        salary="",
        job_type="",
        category=category,
        tags=[category] if category else [],
        publication_date=_to_iso(_text(item, "pubDate")),
        source="weworkremotely",
    )


def fetch_weworkremotely(search: Optional[str] = None,
                         limit: Optional[int] = 100,
                         timeout: float = 30.0) -> List[Job]:
    """Fetch and normalize jobs from the We Work Remotely Programming RSS feed.

    The feed has no query param, so `search` filters the results client-side.
    """
    resp = requests.get(FEED_URL, timeout=timeout)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    jobs = [_to_job(item) for item in root.findall(".//item")]
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.searchable_text()]
    if limit:
        jobs = jobs[:limit]
    return jobs
