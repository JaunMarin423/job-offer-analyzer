"""Minimal web UI for jobranker: paste your CV, run the search, see results.

Run it with:  jobranker-web   (or  uvicorn jobranker.web:app --reload)
Then open http://127.0.0.1:8000 in your browser. It does not scrape LinkedIn
or auto-apply; it only ranks offers so you decide where to apply.
"""

from __future__ import annotations

import html
from argparse import Namespace
from typing import List, Optional

from .cli import _LATAM_COUNTRIES, _SOURCE_FLAGS, filter_and_rank, gather_jobs
from .cv import build_profile
from .geo import normalize_country
from .report import to_html

try:
    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse
except ImportError as exc:  # pragma: no cover - depends on optional extra
    raise RuntimeError(
        "The web UI requires the 'web' extra. Install with: "
        "pip install 'jobranker[web]'"
    ) from exc

app = FastAPI(title="jobranker web")

_COUNTRIES = ["", "colombia", "spain", "mexico", "argentina"]


def _split(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()] if value else []


def _page(body: str) -> str:
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>jobranker — analiza tu CV</title>
<style>
 :root {{ --brand1:#6366f1; --brand2:#0ea5e9; --line:#e2e8f0; --muted:#64748b; }}
 * {{ box-sizing:border-box; }}
 body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif; margin:0;
        background:#f1f5f9; color:#0f172a; }}
 header {{ background:linear-gradient(135deg,var(--brand1),var(--brand2));
          color:#fff; padding:2rem 1.5rem; }}
 header h1 {{ margin:0 0 .3rem; font-size:1.7rem; }}
 header p {{ margin:0; opacity:.92; }}
 .wrap {{ max-width:1180px; margin:1.5rem auto 3rem; padding:0 1.5rem; }}
 .card {{ background:#fff; border:1px solid var(--line); border-radius:16px;
         padding:1.5rem; box-shadow:0 10px 30px rgba(15,23,42,.06);
         margin-bottom:1.5rem; }}
 label {{ display:block; font-weight:600; margin:.9rem 0 .35rem; font-size:.9rem; }}
 textarea, input[type=text], select {{ width:100%; padding:.6rem .7rem;
   border:1px solid var(--line); border-radius:10px; font-size:.92rem;
   font-family:inherit; }}
 textarea {{ min-height:230px; resize:vertical; }}
 .row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
        gap:1rem; }}
 .sources {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
            gap:.4rem; margin-top:.4rem; }}
 .sources label {{ font-weight:400; margin:0; display:flex; align-items:center;
                  gap:.45rem; font-size:.88rem; }}
 .check {{ display:flex; align-items:center; gap:.5rem; margin-top:.6rem; }}
 .check label {{ margin:0; font-weight:400; }}
 button {{ margin-top:1.2rem; background:var(--brand1); color:#fff; border:0;
          padding:.8rem 1.6rem; border-radius:10px; font-size:1rem;
          font-weight:700; cursor:pointer; }}
 button:hover {{ background:#4f46e5; }}
 .hint {{ color:var(--muted); font-size:.82rem; margin:.2rem 0 0; }}
 .notes {{ background:#eef2ff; border:1px solid #c7d2fe; border-radius:10px;
          padding:.8rem 1rem; font-size:.88rem; color:#3730a3; }}
 .err {{ background:#fee2e2; border:1px solid #fecaca; color:#b91c1c; }}
 iframe {{ width:100%; height:1200px; border:1px solid var(--line);
          border-radius:14px; background:#fff; }}
</style></head>
<body>
<header>
  <h1>jobranker — analiza tu CV</h1>
  <p>Pega tu CV en texto plano, elige opciones y busca ofertas que encajen. No
     scrapea LinkedIn ni aplica por ti.</p>
</header>
<div class="wrap">{body}</div>
</body></html>
"""


def _form(cv_text: str = "", roles: str = "", country: str = "",
          language: str = "spanish", lang_only: bool = False,
          selected: Optional[set] = None, top: int = 20,
          search: str = "") -> str:
    selected = selected if selected is not None else set(_SOURCE_FLAGS)
    src_boxes = "".join(
        f"<label><input type='checkbox' name='sources' value='{flag}'"
        f"{' checked' if flag in selected else ''}> {flag}</label>"
        for flag in _SOURCE_FLAGS
    )
    country_opts = "".join(
        f"<option value='{c}'{' selected' if c == country else ''}>"
        f"{c or '— cualquiera —'}</option>"
        for c in _COUNTRIES
    )
    return f"""
<form class="card" method="post" action="/search">
  <label for="cv">Tu CV (texto plano)</label>
  <textarea id="cv" name="cv_text" placeholder="Pega aquí tu CV..."
    >{html.escape(cv_text)}</textarea>
  <p class="hint">Consejo: incluye tus tecnologías (React, Node.js, AWS, etc.)
     para mejores coincidencias.</p>

  <div class="row">
    <div>
      <label for="roles">Roles objetivo</label>
      <input type="text" id="roles" name="roles"
        value="{html.escape(roles)}"
        placeholder="fullstack developer, backend developer, react developer">
    </div>
    <div>
      <label for="country">País</label>
      <select id="country" name="country">{country_opts}</select>
    </div>
    <div>
      <label for="language">Idioma preferido</label>
      <input type="text" id="language" name="language"
        value="{html.escape(language)}" placeholder="spanish">
    </div>
    <div>
      <label for="top">Top N resultados</label>
      <input type="text" id="top" name="top" value="{top}">
    </div>
    <div>
      <label for="search">Búsqueda (opcional)</label>
      <input type="text" id="search" name="search"
        value="{html.escape(search)}" placeholder="react, node, fullstack">
    </div>
  </div>

  <label>Fuentes (gratis, sin API key)</label>
  <div class="sources">{src_boxes}</div>

  <div class="check">
    <input type="checkbox" id="lang_only" name="lang_only" value="1"
      {'checked' if lang_only else ''}>
    <label for="lang_only">Mostrar solo ofertas en el idioma preferido</label>
  </div>

  <button type="submit">Buscar ofertas</button>
</form>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _page(_form())


@app.post("/search", response_class=HTMLResponse)
def search(
    cv_text: str = Form(""),
    roles: str = Form(""),
    country: str = Form(""),
    language: str = Form("spanish"),
    top: str = Form("20"),
    search: str = Form(""),
    lang_only: Optional[str] = Form(None),
    sources: Optional[List[str]] = Form(None),
) -> str:
    selected = set(sources or [])
    lang_only_b = bool(lang_only)
    try:
        top_n = max(0, int(top))
    except (TypeError, ValueError):
        top_n = 20

    form = _form(cv_text=cv_text, roles=roles, country=country,
                 language=language, lang_only=lang_only_b,
                 selected=selected or set(_SOURCE_FLAGS), top=top_n,
                 search=search)

    if not cv_text.strip():
        return _page(form + "<div class='card err'>Pega tu CV para buscar.</div>")
    if not selected:
        return _page(form + "<div class='card err'>Elige al menos una "
                     "fuente.</div>")

    geo = "latam" if normalize_country(country) in _LATAM_COUNTRIES else ""
    args = Namespace(
        file=[], search=search.strip(), source_limit=100,
        category="", geo=geo, country=country,
        **{flag: (flag in selected) for flag in _SOURCE_FLAGS},
    )

    profile = build_profile(
        cv_text,
        target_roles=_split(roles),
        languages=_split(language),
    )
    jobs = gather_jobs(args)
    if not jobs:
        return _page(form + "<div class='card err'>No se encontraron ofertas "
                     "en las fuentes elegidas. Prueba otra búsqueda.</div>")

    scored, notes = filter_and_rank(
        profile, jobs, country=country, lang_only=lang_only_b,
    )
    if not scored:
        return _page(form + "<div class='card err'>Ninguna oferta pasó los "
                     "filtros. Prueba sin filtro de país/idioma o más "
                     "fuentes.</div>")

    report = to_html(scored, top=top_n)
    note_html = ""
    detected = ", ".join(profile.skills) or "(ninguna)"
    summary = [f"{len(scored)} ofertas rankeadas.",
               f"Skills detectadas: {detected}."] + notes
    note_html = ("<div class='card notes'>" +
                 "<br>".join(html.escape(n) for n in summary) + "</div>")
    iframe = (f"<div class='card'><iframe srcdoc=\"{html.escape(report)}\">"
              "</iframe></div>")
    return _page(form + note_html + iframe)


def run() -> None:
    """Console-script entry point: launch the dev server."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":  # pragma: no cover
    run()
