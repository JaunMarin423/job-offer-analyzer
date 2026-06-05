"""Tests for language detection, salary parsing, and language scoring."""

from jobranker.language import detect_language, normalize_language_code
from jobranker.models import CVProfile, Job, fix_mojibake
from jobranker.salary import SalaryInfo, parse_salary_string
from jobranker.scoring import score_job


def test_detect_language_spanish_vs_english():
    es = ("Buscamos un desarrollador senior con experiencia en React y Node. "
          "Trabajo remoto para toda Latinoamérica.")
    en = ("We are looking for a senior developer with experience in React and "
          "Node. Remote work for the whole team.")
    assert detect_language(es) == "es"
    assert detect_language(en) == "en"
    assert detect_language("") == "other"
    assert detect_language("12345 +++ ---") == "other"


def test_detect_portuguese_not_spanish():
    pt = ("Vaga para analista de experiência do cliente. Você vai atuar com "
          "atividades de atenção e contratação. Não perca, trabalho remoto.")
    assert detect_language(pt) == "pt"


def test_fix_mojibake():
    assert fix_mojibake("Ã¡rea") == "área"
    assert fix_mojibake("EspaÃ±a") == "España"
    assert fix_mojibake("plain ascii") == "plain ascii"
    # Job display fields are repaired on construction.
    j = Job(title="Analista del Ã¡rea", company="MÃ©xico SA")
    assert j.title == "Analista del área"
    assert j.company == "México SA"


def test_normalize_language_code():
    assert normalize_language_code("Spanish") == "es"
    assert normalize_language_code("español") == "es"
    assert normalize_language_code("EN") == "en"


def test_job_language_cached():
    j = Job(title="Desarrollador Backend",
            description="Buscamos ingeniero con experiencia en microservicios.")
    assert j.language() == "es"


def test_parse_salary_string_variants():
    a = parse_salary_string("$109k - $228k")
    assert a.currency == "USD" and a.annual_min() == 109000 and a.annual_max() == 228000
    b = parse_salary_string("€40k")
    assert b.currency == "EUR" and b.format_annual() == "EUR 40k/yr"
    c = parse_salary_string("USD 50,000-70,000")
    assert c.annual_min() == 50000 and c.annual_max() == 70000
    assert parse_salary_string("") is None
    assert parse_salary_string("competitive") is None


def test_salary_period_annualization():
    hourly = SalaryInfo(min_amount=50, max_amount=50, currency="USD", period="hourly")
    assert hourly.annual_max() == 50 * 2080
    monthly = SalaryInfo(min_amount=5000, max_amount=5000, currency="USD", period="monthly")
    assert monthly.annual_max() == 60000


def test_language_component_prefers_spanish():
    profile = CVProfile(skills=["python"], languages=["es"])
    spanish = Job(title="Desarrollador", description="Buscamos un ingeniero senior con experiencia.")
    english = Job(title="Developer", description="We are looking for a senior engineer with experience.")
    s_es = score_job(profile, spanish)
    s_en = score_job(profile, english)
    assert s_es.components["language"] == 100.0
    assert s_en.components["language"] == 10.0
    assert s_es.score > s_en.score
