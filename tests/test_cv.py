from jobranker.cv import build_profile, extract_skills


def test_extract_skills_detects_known_terms():
    text = "Experienced in Python, FastAPI and AWS. Also C++ and node.js."
    skills = extract_skills(text)
    assert "python" in skills
    assert "fastapi" in skills
    assert "aws" in skills
    assert "c++" in skills
    assert "node.js" in skills


def test_extract_skills_word_boundaries():
    # "java" should not be matched inside "javascript"
    skills = extract_skills("I write javascript daily.")
    assert "javascript" in skills
    assert "java" not in skills


def test_build_profile_infers_seniority_and_lowercases_roles():
    profile = build_profile(
        "Senior engineer with Python experience.",
        target_roles=["Backend Developer"],
        locations=["Remote"],
    )
    assert profile.seniority == "senior"
    assert profile.target_roles == ["backend developer"]
    assert profile.locations == ["remote"]
    assert "python" in profile.skills
