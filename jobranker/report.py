"""Render a ranking of ScoredJob items as Markdown or HTML."""

from __future__ import annotations

import html
from typing import List

from .scoring import ScoredJob

_SOURCE_CREDITS = {
    "remotive": "Remotive (https://remotive.com)",
    "remoteok": "Remote OK (https://remoteok.com)",
    "arbeitnow": "Arbeitnow (https://www.arbeitnow.com)",
    "jobicy": "Jobicy (https://jobicy.com)",
    "local": "your local file",
}


def _attribution(items: List[ScoredJob]) -> str:
    seen = []
    for s in items:
        src = s.job.source or "local"
        if src not in seen:
            seen.append(src)
    credits = [_SOURCE_CREDITS.get(src, src) for src in seen]
    return ", ".join(credits) if credits else "the selected sources"


def to_markdown(scored: List[ScoredJob], top: int = 0) -> str:
    items = scored[:top] if top else scored
    lines = ["# Job ranking", ""]
    lines.append(f"_{len(items)} offers ranked by fit (score 0-100)._")
    lines.append("")
    lines.append("| # | Score | Title | Company | Location | Why it fits |")
    lines.append("|---|------:|-------|---------|----------|-------------|")
    for i, s in enumerate(items, 1):
        j = s.job
        reasons = "; ".join(s.reasons) or "-"
        title = f"[{_md(j.title)}]({j.url})" if j.url else _md(j.title)
        lines.append(
            f"| {i} | {s.score:.0f} | {title} | {_md(j.company)} | "
            f"{_md(j.location)} | {_md(reasons)} |"
        )
    lines.append("")
    lines.append("## Details")
    for i, s in enumerate(items, 1):
        j = s.job
        lines.append("")
        lines.append(f"### {i}. {_md(j.title)} — {_md(j.company)}  ({s.score:.0f}/100)")
        if j.url:
            lines.append(f"- URL: {j.url}")
        meta = [v for v in [j.location, j.job_type, j.salary, j.category] if v]
        if meta:
            lines.append(f"- {_md(' · '.join(meta))}")
        comp = ", ".join(f"{k}={v:.0f}" for k, v in s.components.items())
        lines.append(f"- Score breakdown: {comp}")
        if s.matched_skills:
            lines.append(f"- Matched skills: {_md(', '.join(s.matched_skills))}")
        if s.missing_skills:
            lines.append(f"- Possible gaps: {_md(', '.join(s.missing_skills))}")
    lines.append("")
    lines.append(f"> Source attribution: offers come from {_attribution(items)}. "
                 "Review each posting before applying.")
    return "\n".join(lines)


def to_html(scored: List[ScoredJob], top: int = 0) -> str:
    items = scored[:top] if top else scored
    rows = []
    for i, s in enumerate(items, 1):
        j = s.job
        title = (f'<a href="{html.escape(j.url)}">{html.escape(j.title)}</a>'
                 if j.url else html.escape(j.title))
        rows.append(
            "<tr>"
            f"<td>{i}</td><td class='score'>{s.score:.0f}</td>"
            f"<td>{title}</td><td>{html.escape(j.company)}</td>"
            f"<td>{html.escape(j.location)}</td>"
            f"<td>{html.escape('; '.join(s.reasons))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Job ranking</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
 table {{ border-collapse: collapse; width: 100%; }}
 th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left;
          vertical-align: top; font-size: 14px; }}
 th {{ background: #0a66c2; color: #fff; }}
 tr:nth-child(even) {{ background: #f6f8fa; }}
 .score {{ font-weight: 700; text-align: right; }}
 caption {{ text-align: left; margin-bottom: .5rem; color: #555; }}
</style></head>
<body>
<h1>Job ranking</h1>
<table>
<caption>{len(items)} offers ranked by fit. Sources: {html.escape(_attribution(items))}.</caption>
<thead><tr><th>#</th><th>Score</th><th>Title</th><th>Company</th>
<th>Location</th><th>Why it fits</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody></table>
</body></html>
"""


def _md(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()
