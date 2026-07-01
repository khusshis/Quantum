import pytest
from engine.schema import Candidate, CandidateProfile, CareerHistoryEntry, Skill, RedrobSignals, ExpectedSalaryRange
from engine.honeypot import is_honeypot

def create_base_candidate(candidate_id="CAND_2222222"):
    return Candidate(
        candidate_id=candidate_id,
        profile=CandidateProfile(
            anonymized_name="Test",
            headline="H",
            summary="This is a summary with enough words to pass the signal implausibility check nicely.",
            location="Pune",
            country="India",
            years_of_experience=2.0,
            current_title="Software Engineer",
            current_company="Test Corp",
            current_company_size="51-200",
            current_industry="Tech"
        ),
        career_history=[],
        education=[],
        skills=[],
        redrob_signals=RedrobSignals(
            profile_completeness_score=100.0,
            signup_date="2020-01-01",
            last_active_date="2024-05-01",
            open_to_work_flag=True,
            profile_views_received_30d=10,
            applications_submitted_30d=1,
            recruiter_response_rate=0.8,
            avg_response_time_hours=24.0,
            skill_assessment_scores={},
            connection_count=100,
            endorsements_received=10,
            notice_period_days=30,
            expected_salary_range_inr_lpa=ExpectedSalaryRange(10, 20),
            preferred_work_mode="hybrid",
            willing_to_relocate=True,
            github_activity_score=50,
            search_appearance_30d=5,
            saved_by_recruiters_30d=2,
            interview_completion_rate=0.9,
            offer_acceptance_rate=0.5,
            verified_email=True,
            verified_phone=True,
            linkedin_connected=True
        )
    )

def test_normal_candidate():
    cand = create_base_candidate()
    cand.profile.years_of_experience = 2.0
    cand.career_history = [
        CareerHistoryEntry("Test", "Engineer", "2020-01-01", "2022-01-01", 24, False, "IT", "51-200", "Desc")
    ]
    cand.skills = [Skill("Python", "intermediate", 10, 24)]
    score, is_hp, reasons = is_honeypot(cand)
    assert score == 0.0
    assert not is_hp

def test_tenure_mismatch():
    cand = create_base_candidate()
    cand.profile.years_of_experience = 8.0  # 96 months expected
    cand.career_history = [
        CareerHistoryEntry("Test", "Engineer", "2020-01-01", "2021-01-01", 12, False, "IT", "51-200", "Desc")
    ]  # only 12 months in history, wildly inconsistent
    score, is_hp, reasons = is_honeypot(cand)
    assert score >= 0.3
    assert any("Tenure mismatch" in r for r in reasons)

def test_skill_duration_impossibility():
    cand = create_base_candidate()
    cand.skills = [Skill("Python", "expert", 10, 0)]  # expert with 0 duration
    score, is_hp, reasons = is_honeypot(cand)
    assert score >= 0.4
    assert any("Skill impossibility" in r for r in reasons)

def test_overlapping_tenure():
    cand = create_base_candidate()
    cand.career_history = [
        CareerHistoryEntry("Test1", "Engineer", "2020-01-01", "2022-01-01", 24, False, "IT", "51-200", "Desc"),
        CareerHistoryEntry("Test2", "Engineer", "2020-06-01", "2023-01-01", 30, False, "IT", "51-200", "Desc"),
        CareerHistoryEntry("Test3", "Engineer", "2021-01-01", "2024-01-01", 36, False, "IT", "51-200", "Desc")
    ]
    score, is_hp, reasons = is_honeypot(cand)
    assert score >= 0.2
    assert any("Overlapping tenure" in r for r in reasons)

def test_skill_count_vs_seniority():
    cand = create_base_candidate()
    cand.profile.years_of_experience = 1.0
    cand.skills = [Skill(f"Skill{i}", "expert", 10, 12) for i in range(12)]
    score, is_hp, reasons = is_honeypot(cand)
    assert score >= 0.5
    assert any("Skill/Seniority mismatch" in r for r in reasons)

def test_signal_implausibility():
    cand = create_base_candidate()
    cand.profile.summary = "A"
    cand.redrob_signals.profile_completeness_score = 100.0
    score, is_hp, reasons = is_honeypot(cand)
    assert score >= 0.2
    assert any("Signal implausibility" in r for r in reasons)
