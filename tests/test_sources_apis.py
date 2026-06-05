"""Offline tests for API source normalizers (no network calls)."""

from xml.etree import ElementTree as ET

from jobranker.models import coerce_tags, epoch_to_iso
from jobranker.sources.arbeitnow import _to_job as arbeitnow_job
from jobranker.sources.himalayas import _to_job as himalayas_job
from jobranker.sources.jobicy import _to_job as jobicy_job
from jobranker.sources.remoteok import _to_job as remoteok_job
from jobranker.sources.remotive import _to_job as remotive_job
from jobranker.sources.themuse import _to_job as themuse_job
from jobranker.sources.weworkremotely import _to_job as wwr_job


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
    assert j.salary_min == 90000 and j.salary_max == 130000
    assert j.salary_currency == "USD"
    assert j.salary_info().format_annual() == "USD 90k–130k/yr"
    assert j.tags == ["node", "react"] and j.source == "remoteok"


def test_remoteok_ignores_placeholder_salary():
    j = remoteok_job({
        "id": "2", "position": "Dev", "company": "X", "url": "u",
        "salary_min": 15, "salary_max": 27,
    })
    assert j.salary_min is None and j.salary_max is None
    assert j.salary_info() is None


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


def test_themuse_to_job_flattens_nested_fields():
    j = themuse_job({
        "name": "Senior Backend Engineer",
        "company": {"name": "Merge"},
        "locations": [{"name": "New York, NY"}, {"name": "Remote"}],
        "categories": [{"name": "Software Engineering"}],
        "levels": [{"name": "Senior Level", "short_name": "senior"}],
        "refs": {"landing_page": "https://themuse.com/jobs/merge/x"},
        "contents": "<p>Build APIs</p>",
        "publication_date": "2026-04-28T23:36:38Z",
    })
    assert j.title == "Senior Backend Engineer" and j.company == "Merge"
    assert j.location == "New York, NY, Remote"
    assert j.category == "Software Engineering"
    assert j.url == "https://themuse.com/jobs/merge/x"
    assert j.source == "themuse"


def test_himalayas_to_job_annual_salary_and_epoch():
    j = himalayas_job({
        "title": "Full Stack Engineer", "companyName": "Acme",
        "locationRestrictions": ["United States", "Canada"],
        "categories": ["Software-Engineer"], "seniority": ["Senior"],
        "minSalary": 100000, "maxSalary": 150000, "currency": "USD",
        "employmentType": "Full Time", "applicationLink": "https://himalayas.app/x",
        "pubDate": 1780648167,
    })
    assert j.title == "Full Stack Engineer" and j.company == "Acme"
    assert j.location == "United States, Canada"
    assert j.salary_min == 100000 and j.salary_max == 150000
    assert j.salary_currency == "USD" and j.salary_period == "yearly"
    assert j.salary_info().format_annual() == "USD 100k–150k/yr"
    assert j.publication_date.startswith("2026-") and j.source == "himalayas"


def test_himalayas_company_name_falls_back_to_slug():
    j = himalayas_job({
        "title": "Staff Engineer", "companyName": "name",
        "companySlug": "hunger-rush",
    })
    assert j.company == "Hunger Rush"


def test_himalayas_to_job_without_salary():
    j = himalayas_job({
        "title": "Dev", "companyName": "Acme", "currency": "USD",
        "minSalary": None, "maxSalary": None,
    })
    assert j.salary_min is None and j.salary_max is None
    assert j.salary_currency == "" and j.salary_period == ""
    assert j.salary_info() is None


def test_weworkremotely_splits_company_from_title():
    xml = (
        "<item><title>Mitek Systems: Senior Full-Stack Developer</title>"
        "<region>Anywhere in the World</region>"
        "<category>Full-Stack Programming</category>"
        "<description>&lt;p&gt;Great role&lt;/p&gt;</description>"
        "<link>https://weworkremotely.com/remote-jobs/mitek</link>"
        "<pubDate>Mon, 18 May 2026 20:31:00 +0000</pubDate></item>"
    )
    j = wwr_job(ET.fromstring(xml))
    assert j.company == "Mitek Systems"
    assert j.title == "Senior Full-Stack Developer"
    assert j.location == "Anywhere in the World"
    assert j.category == "Full-Stack Programming"
    assert j.publication_date.startswith("2026-05-18") and j.source == "weworkremotely"
