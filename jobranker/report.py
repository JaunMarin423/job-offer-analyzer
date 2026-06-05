"""Render a ranking of ScoredJob items as Markdown or HTML."""

from __future__ import annotations

import html
import statistics
from typing import Dict, List, Optional, Tuple

from .language import LANGUAGE_NAMES
from .salary import SalaryInfo
from .scoring import ScoredJob

_SOURCE_CREDITS = {
    "remotive": "Remotive (https://remotive.com)",
    "remoteok": "Remote OK (https://remoteok.com)",
    "arbeitnow": "Arbeitnow (https://www.arbeitnow.com)",
    "jobicy": "Jobicy (https://jobicy.com)",
    "local": "your local file",
}

_LANG_LABEL = {"es": "ES", "en": "EN", "pt": "PT", "other": "—"}


def _attribution(items: List[ScoredJob]) -> str:
    seen = []
    for s in items:
        src = s.job.source or "local"
        if src not in seen:
            seen.append(src)
    credits = [_SOURCE_CREDITS.get(src, src) for src in seen]
    return ", ".join(credits) if credits else "the selected sources"


def _price_groups(items: List[ScoredJob]) -> Dict[str, List[Tuple[ScoredJob, SalaryInfo]]]:
    """Group offers that publish a salary by currency."""
    groups: Dict[str, List[Tuple[ScoredJob, SalaryInfo]]] = {}
    for s in items:
        info = s.job.salary_info()
        if info and info.annual_midpoint():
            groups.setdefault(info.currency, []).append((s, info))
    return groups


def _price_summary(items: List[ScoredJob]) -> str:
    """One-line price comparison (counts + median of the dominant currency)."""
    groups = _price_groups(items)
    with_salary = sum(len(v) for v in groups.values())
    if not with_salary:
        return f"0 of {len(items)} offers publish a salary."
    dominant = max(groups, key=lambda c: len(groups[c]))
    mids = sorted(info.annual_midpoint() for _, info in groups[dominant])
    lo = min(mids)
    hi = max(mids)
    med = statistics.median(mids)
    return (f"{with_salary} of {len(items)} offers publish a salary. "
            f"{dominant} range {_k(lo)}–{_k(hi)}/yr, median ~{_k(med)}/yr "
            f"(across {len(mids)} {dominant} offers).")


def _k(amount: Optional[float]) -> str:
    if not amount:
        return "-"
    if amount >= 1000:
        return f"{amount / 1000:.0f}k"
    return f"{amount:.0f}"


def _salary_cell(s: ScoredJob) -> str:
    info = s.job.salary_info()
    return info.format_annual() if info else ""


def to_markdown(scored: List[ScoredJob], top: int = 0) -> str:
    items = scored[:top] if top else scored
    lines = ["# Job ranking", ""]
    lines.append(f"_{len(items)} offers ranked by fit (score 0-100)._")
    lines.append("")
    lines.append(f"**Price comparison:** {_price_summary(items)}")
    lines.append("")
    lines.append("| # | Score | Title | Company | Location | Lang | Salary | Why it fits |")
    lines.append("|---|------:|-------|---------|----------|:----:|--------|-------------|")
    for i, s in enumerate(items, 1):
        j = s.job
        reasons = "; ".join(s.reasons) or "-"
        title = f"[{_md(j.title)}]({j.url})" if j.url else _md(j.title)
        lang = _LANG_LABEL.get(j.language(), "—")
        lines.append(
            f"| {i} | {s.score:.0f} | {title} | {_md(j.company)} | "
            f"{_md(j.location)} | {lang} | {_md(_salary_cell(s))} | {_md(reasons)} |"
        )
    lines.append("")
    _markdown_price_table(lines, items)
    lines.append("## Details")
    for i, s in enumerate(items, 1):
        j = s.job
        lines.append("")
        lines.append(f"### {i}. {_md(j.title)} — {_md(j.company)}  ({s.score:.0f}/100)")
        if j.url:
            lines.append(f"- URL: {j.url}")
        meta = [v for v in [j.location, j.job_type, _salary_cell(s), j.category] if v]
        if meta:
            lines.append(f"- {_md(' · '.join(meta))}")
        lines.append(f"- Language: {LANGUAGE_NAMES.get(j.language(), j.language())}")
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


def _markdown_price_table(lines: List[str], items: List[ScoredJob]) -> None:
    groups = _price_groups(items)
    if not groups:
        return
    priced = [(s, info) for v in groups.values() for (s, info) in v]
    priced.sort(key=lambda pair: pair[1].annual_midpoint() or 0, reverse=True)
    lines.append("## Comparación de precios")
    lines.append("")
    lines.append("| Salario (anual) | Oferta | Empresa | Fuente |")
    lines.append("|-----------------|--------|---------|--------|")
    for s, info in priced:
        j = s.job
        title = f"[{_md(j.title)}]({j.url})" if j.url else _md(j.title)
        lines.append(f"| {info.format_annual()} | {title} | {_md(j.company)} | "
                     f"{j.source or 'local'} |")
    lines.append("")


def to_html(scored: List[ScoredJob], top: int = 0) -> str:
    items = scored[:top] if top else scored
    rows = []
    for i, s in enumerate(items, 1):
        j = s.job
        title = (f'<a href="{html.escape(j.url)}">{html.escape(j.title)}</a>'
                 if j.url else html.escape(j.title))
        salary = html.escape(_salary_cell(s)) or "<span class='muted'>—</span>"
        reasons = html.escape("; ".join(s.reasons))
        rows.append(
            "<tr>"
            f"<td class='rank'>{i}</td>"
            f"<td><span class='score {_score_class(s.score)}'>{s.score:.0f}</span></td>"
            f"<td class='title'>{title}"
            f"<div class='reasons'>{reasons}</div></td>"
            f"<td>{html.escape(j.company)}</td>"
            f"<td>{html.escape(j.location)}</td>"
            f"<td>{_lang_badge(j.language())}</td>"
            f"<td class='salary'>{salary}</td>"
            f"<td>{_source_chip(j.source)}</td>"
            "</tr>"
        )
    stats = _stats_cards(items)
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>jobranker — ranking de ofertas</title>
<style>
 :root {{
   --bg:#0f172a; --card:#ffffff; --ink:#0f172a; --muted:#64748b;
   --line:#e2e8f0; --brand1:#6366f1; --brand2:#0ea5e9;
   --good:#16a34a; --mid:#d97706; --low:#64748b;
 }}
 * {{ box-sizing:border-box; }}
 body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
        margin:0; background:#f1f5f9; color:var(--ink); }}
 header {{ background:linear-gradient(135deg,var(--brand1),var(--brand2));
          color:#fff; padding:2rem 1.5rem 2.5rem; }}
 header h1 {{ margin:0 0 .3rem; font-size:1.7rem; }}
 header p {{ margin:0; opacity:.9; font-size:.95rem; }}
 .wrap {{ max-width:1180px; margin:-1.6rem auto 3rem; padding:0 1.5rem; }}
 .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
          gap:1rem; margin-bottom:1.5rem; }}
 .stat {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
         padding:1rem 1.2rem; box-shadow:0 6px 18px rgba(15,23,42,.06); }}
 .stat .n {{ font-size:1.5rem; font-weight:800; }}
 .stat .l {{ color:var(--muted); font-size:.8rem; text-transform:uppercase;
            letter-spacing:.04em; }}
 .panel {{ background:var(--card); border:1px solid var(--line); border-radius:16px;
          overflow:hidden; box-shadow:0 10px 30px rgba(15,23,42,.08); }}
 table {{ border-collapse:collapse; width:100%; }}
 thead th {{ background:#f8fafc; color:var(--muted); text-align:left;
            font-size:.72rem; text-transform:uppercase; letter-spacing:.05em;
            padding:.8rem 1rem; border-bottom:1px solid var(--line);
            position:sticky; top:0; }}
 tbody td {{ padding:.85rem 1rem; border-bottom:1px solid var(--line);
            vertical-align:top; font-size:.9rem; }}
 tbody tr:hover {{ background:#f8fafc; }}
 .rank {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
 .title a {{ color:var(--brand1); font-weight:600; text-decoration:none; }}
 .title a:hover {{ text-decoration:underline; }}
 .reasons {{ color:var(--muted); font-size:.78rem; margin-top:.25rem;
            max-width:430px; line-height:1.35; }}
 .score {{ display:inline-block; min-width:2.4rem; text-align:center;
          font-weight:800; color:#fff; padding:.25rem .5rem; border-radius:999px;
          font-variant-numeric:tabular-nums; }}
 .score.good {{ background:var(--good); }}
 .score.mid {{ background:var(--mid); }}
 .score.low {{ background:var(--low); }}
 .badge {{ display:inline-block; font-size:.72rem; font-weight:700;
          padding:.15rem .5rem; border-radius:6px; }}
 .badge.es {{ background:#fee2e2; color:#b91c1c; }}
 .badge.en {{ background:#dbeafe; color:#1d4ed8; }}
 .badge.pt {{ background:#dcfce7; color:#15803d; }}
 .badge.other {{ background:#f1f5f9; color:#64748b; }}
 .chip {{ display:inline-block; font-size:.72rem; color:var(--muted);
         background:#f1f5f9; border:1px solid var(--line);
         padding:.15rem .5rem; border-radius:999px; }}
 .salary {{ font-variant-numeric:tabular-nums; font-weight:600; }}
 .muted {{ color:var(--muted); font-weight:400; }}
 footer {{ max-width:1180px; margin:0 auto 3rem; padding:0 1.5rem;
          color:var(--muted); font-size:.82rem; }}
</style></head>
<body>
<header>
  <h1>Ranking de ofertas de empleo</h1>
  <p>{len(items)} ofertas ordenadas por encaje con tu CV · tú decides a cuáles aplicar.</p>
</header>
<div class="wrap">
  <div class="cards">{stats}</div>
  <div class="panel">
  <table>
  <thead><tr><th>#</th><th>Score</th><th>Oferta</th><th>Empresa</th>
  <th>Ubicación</th><th>Idioma</th><th>Salario</th><th>Fuente</th></tr></thead>
  <tbody>
  {''.join(rows)}
  </tbody></table>
  </div>
</div>
<footer>Fuentes: {html.escape(_attribution(items))}. jobranker no scrapea LinkedIn
ni aplica por ti; revisa cada oferta antes de postularte.</footer>
</body></html>
"""


def _score_class(score: float) -> str:
    if score >= 70:
        return "good"
    if score >= 50:
        return "mid"
    return "low"


def _lang_badge(code: str) -> str:
    label = _LANG_LABEL.get(code, "—")
    cls = code if code in ("es", "en", "pt") else "other"
    return f"<span class='badge {cls}'>{label}</span>"


def _source_chip(source: str) -> str:
    return f"<span class='chip'>{html.escape(source or 'local')}</span>"


def _stats_cards(items: List[ScoredJob]) -> str:
    if not items:
        return ""
    avg = sum(s.score for s in items) / len(items)
    groups = _price_groups(items)
    with_salary = sum(len(v) for v in groups.values())
    es_count = sum(1 for s in items if s.job.language() == "es")
    cards = [
        ("Ofertas", f"{len(items)}"),
        ("Mejor score", f"{items[0].score:.0f}"),
        ("Score medio", f"{avg:.0f}"),
        ("En español", f"{es_count}"),
        ("Con salario", f"{with_salary}"),
    ]
    return "".join(
        f"<div class='stat'><div class='n'>{html.escape(n)}</div>"
        f"<div class='l'>{html.escape(l)}</div></div>"
        for l, n in cards
    )


def _md(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()
