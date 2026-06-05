from jobranker.cli import _dedupe
from jobranker.models import Job


def test_dedupe_removes_same_title_company_across_sources():
    jobs = [
        Job(title="Backend Dev", company="ACME", source="remotive"),
        Job(title="backend dev", company="acme", source="remoteok"),  # dup
        Job(title="Backend Dev", company="Other", source="jobicy"),   # keep
    ]
    out = _dedupe(jobs)
    assert len(out) == 2
    assert out[0].source == "remotive"
    assert out[1].company == "Other"
