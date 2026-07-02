import pytest
from engine.schema import Candidate, CandidateProfile, Skill, RedrobSignals, ExpectedSalaryRange
from engine.features import CandidateFeatures
from engine.jd_parser import JD
from engine.reasoning import generate_reasoning

def create_synthetic_candidate(i: int):
    return Candidate(
        candidate_id=f"CAND_1000{i:03d}",
        profile=CandidateProfile(
            anonymized_name=f"Test {i}",
            headline="Engineer",
            summary="A short summary",
            location="Pune",
            country="India",
            years_of_experience=6.0,
            current_title=f"Engineer {i}",
            current_company="Tech",
            current_company_size="1-10",
            current_industry="Tech"
        ),
        career_history=[],
        education=[],
        skills=[Skill(f"Python{i}", "expert", 10, 12), Skill("Embedding", "intermediate", 5, 5)],
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
            notice_period_days=30 if i % 2 == 0 else 60, # Some have high notice period
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

def test_reasoning_generation():
    reasonings = set()
    features_top = CandidateFeatures(
        years_experience_fit=1.0, title_trajectory_score=1.0, production_ml_evidence_score=1.0,
        domain_adjacency_penalty=1.0, consulting_only_penalty=1.0, research_only_disqualifier=1.0,
        role_relevance_score=1.0, skill_semantic_match=1.0, skill_trust_score=1.0,
        framework_enthusiast_penalty=1.0, education_tier_score=0.2, availability_score=1.0,
        notice_period_fit=1.0, salary_alignment_flag=1.0, verification_trust_score=0.1,
        location_boost=0.1
    )
    features_mid = CandidateFeatures(
        years_experience_fit=1.0, title_trajectory_score=1.0, production_ml_evidence_score=0.0,
        domain_adjacency_penalty=1.0, consulting_only_penalty=1.0, research_only_disqualifier=1.0,
        role_relevance_score=0.5, skill_semantic_match=0.5, skill_trust_score=1.0,
        framework_enthusiast_penalty=1.0, education_tier_score=0.2, availability_score=0.8,
        notice_period_fit=1.0, salary_alignment_flag=1.0, verification_trust_score=0.1,
        location_boost=0.1
    )
    features_low = CandidateFeatures(
        years_experience_fit=0.0, title_trajectory_score=0.0, production_ml_evidence_score=0.0,
        domain_adjacency_penalty=0.1, consulting_only_penalty=0.1, research_only_disqualifier=1.0,
        role_relevance_score=0.0, skill_semantic_match=0.1, skill_trust_score=0.5,
        framework_enthusiast_penalty=1.0, education_tier_score=0.0, availability_score=0.1,
        notice_period_fit=0.1, salary_alignment_flag=1.0, verification_trust_score=0.0,
        location_boost=0.0
    )

    for i in range(100):
        cand = create_synthetic_candidate(i)
        
        # Rank 1-10
        if i < 10:
            rank = i + 1
            reasoning = generate_reasoning(cand, features_top, JD, rank)
            assert "however" not in reasoning if cand.redrob_signals.notice_period_days <= 30 else True
        # Rank 11-60
        elif i < 60:
            rank = i + 1
            reasoning = generate_reasoning(cand, features_mid, JD, rank)
        # Rank 61-100
        else:
            rank = i + 1
            reasoning = generate_reasoning(cand, features_low, JD, rank)
            assert "Ranked lower" in reasoning or "Lower confidence" in reasoning
            
        reasonings.add(reasoning)
        
        # Check that actual facts are cited (years of experience and title)
        assert str(cand.profile.years_of_experience) in reasoning
        assert cand.profile.current_title in reasoning
        
        # Skills verification
        # The generated reasoning should contain at least one of the candidate's skills
        skills_str = [s.name for s in cand.skills]
        assert any(s in reasoning for s in skills_str)

    # Ensure no two are byte-identical across the 100
    assert len(reasonings) == 100
