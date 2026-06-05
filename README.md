# jobranker — job-offer analyzer & ranker

Analyze job offers and rank them by how well they fit **your CV and career
goals**. It reads your CV, pulls offers from a legal source, scores each one,
and produces an explained ranking (Markdown or HTML) so you can decide where to
apply.

## Why it does NOT touch LinkedIn

Automating LinkedIn (scraping listings, auto-applying, sending messages with a
bot) **violates LinkedIn's Terms of Service** and can get your account
permanently banned. Auto-submitted applications also tend to be low quality.

`jobranker` is deliberately **read-only and human-in-the-loop**:

- It never logs into LinkedIn or any account.
- It never auto-applies or sends your CV anywhere.
- It ingests offers from **legal sources** and only ranks them for you. **You**
  decide where to apply and click "apply" yourself.

## Job sources

1. **Remotive API** (`--remotive`): free, key-less public API of remote jobs.
   We link back to the original Remotive URL and credit Remotive as required by
   their API terms.
2. **Local file** (`--file path.csv` / `.json`): analyze offers you collected
   yourself — including a posting you copied from LinkedIn into a row. No
   scraping involved.

The architecture makes it easy to add more providers later (e.g. Adzuna,
JSearch) — those require a free API key.

## Install

```bash
cd job-offer-analyzer
pip install -e .            # core
pip install -e ".[pdf]"     # add PDF CV support (pypdf)
pip install -e ".[dev]"     # add pytest
```

## Usage

Rank live remote Python backend jobs against your CV:

```bash
jobranker --cv path/to/your_cv.pdf \
          --roles "backend developer,python developer" \
          --locations "remote,worldwide,colombia" \
          --remotive --search "python backend" --remotive-limit 50 \
          --top 15 --format markdown -o ranking.md
```

Analyze offers from a CSV you built:

```bash
jobranker --cv examples/sample_cv.txt --file examples/sample_jobs.csv --top 10
```

Combine both sources and export HTML:

```bash
jobranker --cv my_cv.txt --remotive --search "data analyst" \
          --file extra_jobs.csv --format html -o ranking.html
```

### Local file format

CSV header or JSON keys (only `title` is required):

```
title, company, location, description, url, salary, job_type, category,
tags, publication_date
```

`tags` can be a comma-separated string or a JSON list. See
[`examples/sample_jobs.csv`](examples/sample_jobs.csv).

## How the score works

The 0–100 score is a transparent weighted blend so every ranking is
explainable:

| Component  | Weight | What it measures |
|------------|-------:|------------------|
| skills     | 50%    | overlap between your CV skills and the offer |
| role       | 25%    | offer title vs. your target roles |
| location   | 15%    | offer location vs. your preferences |
| seniority  | 5%     | junior/senior alignment |
| recency    | 5%     | how recently the offer was posted |

Each ranked offer lists matched skills, possible gaps, and a per-component
breakdown.

## Tests

```bash
pytest -q
```

## Roadmap

- Additional legal providers (Adzuna, JSearch, Jooble) behind API keys.
- Optional CV/cover-letter tailoring per offer (still human-reviewed).
