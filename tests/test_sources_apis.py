"""Offline tests for API source normalizers (no network calls)."""

from jobranker.models import coerce_tags, epoch_to_iso
from jobranker.sources.arbeitnow import _to_job as arbeitnow_job
from jobranker.sources.jobicy import _to_job as jobicy_job
from jobranker.sources.remoteok import _to_job as remoteok_job
from jobranker.sources.remotive import _to_job as remotive_job


def test_coerce_tags_handles_all_shapes():
    assert coerce_tags(["a", "b"]) == ["a", "b"]
    assert coerce_tags('["python", "aws"]') == ["python", "aws"]      # JSON
    assert coerce_tags("['react', 'node']") == ["react", "node"]      # py-repr
    assert coerce_tags("sql, pandas") == ["sql", "pandas"]            # CSV
    assert coerce_tags("['Finance &amp; Ops']") == ["Finance & Ops"]  # unescaped
    assert coerce_tags("") == []


def test_epoch_to_iso():
    assert epoch_to_iso("1780677038").startswith("2026-")
    assert epoch_to_iso(1780677038).endswith("+00:00")
    assert epoch_to_iso("not-a-number") == ""


def test_remotive_to_job():
    j = remotive_job({
        "title": "Backend Dev", "company_name": "ACME",
        "candidate_required_location": "Worldwide", "url": "u",
        "tags": "['python', 'aws']", "publication_date": "2026-06-01T00:00:00",
    })
    assert j.title == "Backend Dev" and j.company == "ACME"
    assert j.tags == ["python", "aws"] and j.source == "remotive"


def test_remoteok_to_job_salary_and_fields():
    j = remoteok_job({
        "id": "1", "position": "Node Dev", "company": "X",
        "location": "Remote", "url": "u", "tags": ["node", "react"],
        "salary_min": 90000, "salary_max": 130000, "date": "2026-06-01",
    })
    assert j.title == "Node Dev"
    assert j.salary == "$90000 - $130000"
    assert j.tags == ["node", "react"] and j.source == "remoteok"


def test_arbeitnow_to_job_epoch_and_jobtypes():
    j = arbeitnow_job({
        "title": "Fullstack", "company_name": "Y", "location": "Berlin",
        "url": "u", "tags": "['React']", "job_types": "['full_time']",
        "created_at": "1780677038",
    })
    assert j.title == "Fullstack" and j.job_type == "full_time"
    assert j.publication_date.startswith("2026-") and j.source == "arbeitnow"


def test_jobicy_to_job_industry_as_category_and_tags():
    j = jobicy_job({
        "jobTitle": "React Dev", "companyName": "Z", "jobGeo": "USA",
        "url": "u", "jobIndustry": "['Software Development']",
        "jobType": "['Full-Time']", "pubDate": "2026-06-05T08:39:42+00:00",
    })
    assert j.title == "React Dev" and j.location == "USA"
    assert j.tags == ["Software Development"]
    assert j.category == "Software Development" and j.source == "jobicy"
