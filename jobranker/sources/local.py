"""Load jobs from a local CSV or JSON file you provide.

This lets you analyze offers from anywhere (including a posting you copied from
LinkedIn) without any scraping. Expected columns/keys (only `title` required):

    title, company, location, description, url, salary, job_type, category,
    tags, publication_date

`tags` may be a comma-separated string or a JSON list.
"""

from __future__ import annotations

import csv
import json
import os
from typing import List

from ..models import Job, coerce_tags

_FIELDS = {
    "title", "company", "location", "description", "url", "salary",
    "job_type", "category", "tags", "publication_date", "source",
}


def _row_to_job(row: dict) -> Job:
    data = {k: row.get(k, "") for k in _FIELDS if k != "tags"}
    data["tags"] = coerce_tags(row.get("tags"))
    if not data.get("source"):
        data["source"] = "local"
    return Job(**data)


def load_local(path: str) -> List[Job]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        return _load_json(path)
    if ext in (".csv", ".tsv"):
        return _load_csv(path, delimiter="\t" if ext == ".tsv" else ",")
    raise ValueError(f"Unsupported file type: {ext} (use .csv, .tsv or .json)")


def _load_json(path: str) -> List[Job]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("jobs", [])
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of jobs or {'jobs': [...]}")
    return [_row_to_job(item) for item in data]


def _load_csv(path: str, delimiter: str = ",") -> List[Job]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        return [_row_to_job(row) for row in reader]
