"""Command-line interface for jobranker."""

from __future__ import annotations

import argparse
import sys
from typing import List

from .cv import build_profile
from .models import Job
from .report import to_html, to_markdown
from .scoring import rank_jobs
from .sources import (
    fetch_arbeitnow,
    fetch_jobicy,
    fetch_remoteok,
    fetch_remotive,
    load_local,
)

_SOURCE_FLAGS = ("remotive", "remoteok", "arbeitnow", "jobicy")


def _split(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()] if value else []


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jobranker",
        description="Analyze and rank job offers against your CV. Does not "
                    "scrape LinkedIn or auto-apply; you decide where to apply.",
    )
    p.add_argument("--cv", required=True,
                   help="Path to your CV (.txt/.md/.pdf) or raw CV text.")
    p.add_argument("--roles", default="",
                   help="Comma-separated target roles, e.g. 'backend developer,data analyst'.")
    p.add_argument("--locations", default="",
                   help="Comma-separated preferred locations, e.g. 'remote,colombia,worldwide'.")
    p.add_argument("--seniority", choices=["junior", "mid", "senior"],
                   help="Override seniority (otherwise inferred from the CV).")
    p.add_argument("--skills", default="",
                   help="Extra comma-separated skills to add to those detected in the CV.")

    src = p.add_argument_group("job sources (all free, no API key)")
    src.add_argument("--remotive", action="store_true",
                     help="Fetch live offers from the free Remotive API.")
    src.add_argument("--remoteok", action="store_true",
                     help="Fetch live offers from the free RemoteOK API.")
    src.add_argument("--arbeitnow", action="store_true",
                     help="Fetch live offers from the free Arbeitnow API.")
    src.add_argument("--jobicy", action="store_true",
                     help="Fetch live offers from the free Jobicy API.")
    src.add_argument("--search", default="",
                     help="Search query applied to every selected source.")
    src.add_argument("--category", default="",
                     help="Remotive category slug (e.g. 'software-dev').")
    src.add_argument("--geo", default="",
                     help="Jobicy geo filter (e.g. 'usa', 'latin-america').")
    src.add_argument("--source-limit", type=int, default=100,
                     help="Max offers to pull from each live source (default 100).")
    src.add_argument("--file", action="append", default=[],
                     metavar="PATH",
                     help="Load offers from a local CSV/JSON file (repeatable).")

    out = p.add_argument_group("output")
    out.add_argument("--top", type=int, default=20,
                     help="Show only the top N results (0 = all). Default 20.")
    out.add_argument("--min-score", type=float, default=0.0,
                     help="Drop offers below this score (0-100).")
    out.add_argument("--format", choices=["markdown", "html"], default="markdown")
    out.add_argument("-o", "--output", help="Write the report to this file.")
    return p


def _dedupe(jobs: List[Job]) -> List[Job]:
    """Drop duplicate postings (same title+company) across sources."""
    seen = set()
    unique: List[Job] = []
    for j in jobs:
        key = (j.title.strip().lower(), j.company.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(j)
    return unique


def gather_jobs(args) -> List[Job]:
    jobs: List[Job] = []
    search = args.search or None
    limit = args.source_limit
    for path in args.file:
        jobs.extend(load_local(path))
    if args.remotive:
        jobs.extend(fetch_remotive(
            search=search, category=args.category or None, limit=limit,
        ))
    if args.remoteok:
        jobs.extend(fetch_remoteok(search=search, limit=limit))
    if args.arbeitnow:
        jobs.extend(fetch_arbeitnow(search=search, limit=limit))
    if args.jobicy:
        jobs.extend(fetch_jobicy(
            search=search, geo=args.geo or None, limit=limit,
        ))
    return _dedupe(jobs)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    any_live = any(getattr(args, flag) for flag in _SOURCE_FLAGS)
    if not args.file and not any_live:
        print("error: choose at least one source (e.g. --remotive, --remoteok, "
              "--arbeitnow, --jobicy, and/or --file PATH)", file=sys.stderr)
        return 2

    profile = build_profile(
        args.cv,
        target_roles=_split(args.roles),
        locations=_split(args.locations),
        seniority=args.seniority,
        extra_skills=_split(args.skills),
    )

    jobs = gather_jobs(args)
    if not jobs:
        print("No jobs found from the selected sources.", file=sys.stderr)
        return 1

    scored = rank_jobs(profile, jobs, min_score=args.min_score)

    if args.format == "html":
        report = to_html(scored, top=args.top)
    else:
        report = to_markdown(scored, top=args.top)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Wrote {args.format} report with {len(scored)} ranked offers "
              f"to {args.output}", file=sys.stderr)
        print(f"Detected skills: {', '.join(profile.skills) or '(none)'}",
              file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
