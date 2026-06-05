from jobranker.models import Job
from jobranker.report import _attribution, to_html, to_markdown
from jobranker.scoring import ScoredJob


def _scored(source):
    return ScoredJob(job=Job(title="T", company="C", source=source), score=50.0,
                     reasons=["x"])


def test_attribution_lists_unique_sources_in_order():
    items = [_scored("remotive"), _scored("jobicy"), _scored("remotive")]
    out = _attribution(items)
    assert "Remotive" in out and "Jobicy" in out
    assert out.index("Remotive") < out.index("Jobicy")


def test_reports_render_with_dynamic_attribution():
    items = [_scored("remoteok")]
    assert "Remote OK" in to_markdown(items)
    assert "Remote OK" in to_html(items)
