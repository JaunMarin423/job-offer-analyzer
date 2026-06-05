from jobranker.models import CVProfile, Job
from jobranker.scoring import rank_jobs, score_job


def _profile():
    return CVProfile(
        skills=["python", "fastapi", "postgresql", "aws", "docker"],
        target_roles=["backend developer"],
        locations=["worldwide"],
        seniority="senior",
    )


def _backend_job():
    return Job(
        title="Senior Backend Developer",
        company="Globex",
        location="Worldwide",
        description="Python FastAPI PostgreSQL AWS Docker microservices.",
        tags=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        publication_date="2026-06-03T10:00:00",
    )


def _marketing_job():
    return Job(
        title="Marketing Manager",
        company="Soylent",
        location="New York",
        description="Lead marketing campaigns and SEO.",
        tags=["SEO", "marketing"],
        publication_date="2026-04-15T10:00:00",
    )


def test_relevant_job_scores_higher_than_irrelevant():
    profile = _profile()
    good = score_job(profile, _backend_job())
    bad = score_job(profile, _marketing_job())
    assert good.score > bad.score
    assert good.score >= 70


def test_matched_skills_reported():
    scored = score_job(_profile(), _backend_job())
    assert "python" in scored.matched_skills
    assert "aws" in scored.matched_skills


def test_rank_orders_by_score_and_filters_min():
    profile = _profile()
    ranked = rank_jobs(profile, [_marketing_job(), _backend_job()])
    assert ranked[0].job.title == "Senior Backend Developer"
    filtered = rank_jobs(profile, [_marketing_job(), _backend_job()], min_score=60)
    assert all(s.score >= 60 for s in filtered)
    assert len(filtered) == 1
