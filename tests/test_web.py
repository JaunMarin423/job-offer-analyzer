import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from jobranker import web  # noqa: E402
from jobranker.models import Job  # noqa: E402

client = TestClient(web.app)


def test_index_renders_form():
    res = client.get("/")
    assert res.status_code == 200
    assert "Tu CV (texto plano)" in res.text
    assert 'name="cv_text"' in res.text


def test_search_requires_cv():
    res = client.post("/search", data={"cv_text": "", "sources": ["remotive"]})
    assert res.status_code == 200
    assert "Pega tu CV para buscar." in res.text


def test_search_ranks_with_stubbed_jobs(monkeypatch):
    sample = [
        Job(title="React Developer", company="Acme",
            location="Colombia", description="react node.js typescript",
            url="https://example.com/1", source="remotive"),
    ]
    monkeypatch.setattr(web, "gather_jobs", lambda args: sample)
    res = client.post("/search", data={
        "cv_text": "React, Node.js, TypeScript developer",
        "roles": "react developer",
        "country": "colombia",
        "language": "spanish",
        "top": "10",
        "sources": ["remotive"],
    })
    assert res.status_code == 200
    assert "ofertas rankeadas" in res.text
    assert "React Developer" in res.text
