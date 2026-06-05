import json
import os

from jobranker.sources import load_local

HERE = os.path.dirname(__file__)
EXAMPLES = os.path.join(HERE, "..", "examples")


def test_load_csv_examples():
    jobs = load_local(os.path.join(EXAMPLES, "sample_jobs.csv"))
    assert len(jobs) == 5
    first = jobs[0]
    assert first.title == "Senior Python Backend Engineer"
    assert "Python" in first.tags
    assert first.source == "local"


def test_load_json(tmp_path):
    data = [{"title": "Dev", "tags": ["python", "aws"]},
            {"title": "Analyst", "tags": "sql, pandas"}]
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    jobs = load_local(str(p))
    assert len(jobs) == 2
    assert jobs[0].tags == ["python", "aws"]
    assert jobs[1].tags == ["sql", "pandas"]
