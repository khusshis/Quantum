import pytest
from engine.schema import Candidate, CandidateProfile, CareerHistoryEntry, RedrobSignals, ExpectedSalaryRange, Skill
from engine.jd_parser import JD
from engine.features import compute_features

def create_base_candidate(candidate_id="CAND_1111111"):
    return Candidate(
        candidate_id=candidate_id,
        profile=CandidateProfile(
            anonymized_name="Test",
            headline="H",
            summary="S",
            location="Pune",
            country="India",
            years_of_experience=7.0,
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

def test_years_experience_fit():
    cand = create_base_candidate()
    
    cand.profile.years_of_experience = 7.0  # inside 5-9
    feats = compute_features(cand, JD)
    assert feats.years_experience_fit == 1.0
    
    cand.profile.years_of_experience = 3.0  # 2 years outside (dist=2), max(0, 1 - 2/5) = 0.6
    feats = compute_features(cand, JD)
    assert pytest.approx(feats.years_experience_fit, 0.01) == 0.6

def test_consulting_only_penalty():
    cand = create_base_candidate()
    # 100% Consulting
    cand.career_history = [
        CareerHistoryEntry("TCS", "Engineer", "2020", None, 24, True, "IT", "10001+", "Coded")
    ]
    feats = compute_features(cand, JD)
    assert feats.consulting_only_penalty < 0.5  # Penalized
    
    # Restored with product company
    cand.career_history = [
        CareerHistoryEntry("Product Corp", "Engineer", "2018", "2020", 24, False, "Tech", "51-200", "Coded"),
        CareerHistoryEntry("TCS", "Engineer", "2020", None, 24, True, "IT", "10001+", "Coded")
    ]
    feats = compute_features(cand, JD)
    assert feats.consulting_only_penalty == 1.0  # Restored

def test_production_ml_evidence_score():
    cand = create_base_candidate()
    cand.career_history = [
        CareerHistoryEntry("Test", "Engineer", "2020", None, 24, True, "IT", "51-200", 
                           "Developed a machine learning model.")  # No production/deployment words
    ]
    feats = compute_features(cand, JD)
    assert feats.production_ml_evidence_score == 0.0
    
    cand.career_history = [
        CareerHistoryEntry("Test", "Engineer", "2020", None, 24, True, "IT", "51-200", 
                           "Deployed a ranking model to production, served 1M requests.")
    ]
    feats = compute_features(cand, JD)
    assert feats.production_ml_evidence_score > 0.0

def test_research_only_disqualifier():
    cand = create_base_candidate()
    cand.career_history = [
        CareerHistoryEntry("University Lab", "PhD Researcher", "2020", None, 48, True, "Edu", "51-200", 
                           "Researched stuff.")
    ]
    feats = compute_features(cand, JD)
    assert feats.research_only_disqualifier < 0.5  # Penalized
    
    cand.career_history[0].description = "Deployed models to real users in production."
    feats = compute_features(cand, JD)
    assert feats.research_only_disqualifier == 1.0  # Restored

def test_framework_enthusiast_penalty():
    cand = create_base_candidate()
    cand.skills = [
        Skill("LangChain", "beginner", 0, 1),
        Skill("LlamaIndex", "beginner", 0, 1),
        Skill("OpenAI", "beginner", 0, 1),
        Skill("HuggingFace", "beginner", 0, 1)
    ]
    cand.career_history = [
        CareerHistoryEntry("Test", "Engineer", "2020", None, 24, True, "IT", "51-200", "Built a demo app.")
    ]
    feats = compute_features(cand, JD)
    assert feats.framework_enthusiast_penalty < 1.0
