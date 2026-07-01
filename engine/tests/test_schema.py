import json
import pytest
import os
from engine.schema import load_candidates, Candidate

def test_valid_candidate_parses_correctly(tmp_path):
    candidate_data = {
        "candidate_id": "CAND_1234567",
        "profile": {
            "anonymized_name": "Test Name",
            "headline": "Test Headline",
            "summary": "Test Summary",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 6.5,
            "current_title": "AI Engineer",
            "current_company": "Test Co",
            "current_company_size": "51-200",
            "current_industry": "Tech"
        },
        "career_history": [{
            "company": "Test Co",
            "title": "AI Engineer",
            "start_date": "2020-01-01",
            "end_date": None,
            "duration_months": 48,
            "is_current": True,
            "industry": "Tech",
            "company_size": "51-200",
            "description": "Deployed models."
        }],
        "education": [],
        "skills": [],
        "redrob_signals": {
            "profile_completeness_score": 90.0,
            "signup_date": "2020-01-01",
            "last_active_date": "2024-01-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 10,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 24.0,
            "skill_assessment_scores": {},
            "connection_count": 100,
            "endorsements_received": 10,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 30},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 50.0,
            "search_appearance_30d": 5,
            "saved_by_recruiters_30d": 2,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.5,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True
        }
    }
    
    file_path = tmp_path / "candidates.jsonl"
    with open(file_path, "w") as f:
        f.write(json.dumps(candidate_data) + "\n")
        
    candidates = load_candidates(str(file_path))
    assert len(candidates) == 1
    assert candidates[0].candidate_id == "CAND_1234567"
    assert candidates[0].profile.years_of_experience == 6.5
    assert candidates[0].redrob_signals.github_activity_score == 50.0


def test_missing_required_field_handled(tmp_path):
    # Missing profile entirely
    candidate_data = {
        "candidate_id": "CAND_1234567"
    }
    file_path = tmp_path / "candidates.jsonl"
    with open(file_path, "w") as f:
        f.write(json.dumps(candidate_data) + "\n")
        
    candidates = load_candidates(str(file_path))
    assert len(candidates) == 0  # Should be skipped and logged, not crash


def test_malformed_jsonl_line_is_skipped(tmp_path):
    file_path = tmp_path / "candidates.jsonl"
    with open(file_path, "w") as f:
        f.write("{ invalid json...\n")
        
    candidates = load_candidates(str(file_path))
    assert len(candidates) == 0  # Should be skipped


def test_redrob_signals_sentinel_values(tmp_path):
    candidate_data = {
        "candidate_id": "CAND_1234568",
        "profile": {
            "anonymized_name": "Test Name 2",
            "headline": "Test Headline",
            "summary": "Test Summary",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 6.5,
            "current_title": "AI Engineer",
            "current_company": "Test Co",
            "current_company_size": "51-200",
            "current_industry": "Tech"
        },
        "career_history": [],
        "redrob_signals": {
            "profile_completeness_score": 90.0,
            "signup_date": "2020-01-01",
            "last_active_date": "2024-01-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 10,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 24.0,
            "skill_assessment_scores": {},
            "connection_count": 100,
            "endorsements_received": 10,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 30},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": -1,  # Sentinel
            "search_appearance_30d": 5,
            "saved_by_recruiters_30d": 2,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": -1,  # Sentinel
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True
        }
    }
    
    file_path = tmp_path / "candidates.jsonl"
    with open(file_path, "w") as f:
        f.write(json.dumps(candidate_data) + "\n")
        
    candidates = load_candidates(str(file_path))
    assert len(candidates) == 1
    # Check that it parsed successfully (downstream logic will handle the -1 logic, or we handle it here)
    assert candidates[0].redrob_signals.github_activity_score is None
    assert candidates[0].redrob_signals.offer_acceptance_rate is None

def test_years_of_experience_handled(tmp_path):
    candidate_data = {
        "candidate_id": "CAND_1234569",
        "profile": {
            "anonymized_name": "Test",
            "headline": "H",
            "summary": "S",
            "location": "L",
            "country": "C",
            "years_of_experience": -5,  # Out of range
            "current_title": "T",
            "current_company": "C",
            "current_company_size": "1-10",
            "current_industry": "I"
        },
        "career_history": [],
        "redrob_signals": {
            "profile_completeness_score": 90.0,
            "signup_date": "2020-01-01",
            "last_active_date": "2024-01-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 10,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 24.0,
            "skill_assessment_scores": {},
            "connection_count": 100,
            "endorsements_received": 10,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 30},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 50,
            "search_appearance_30d": 5,
            "saved_by_recruiters_30d": 2,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.5,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True
        }
    }
    
    file_path = tmp_path / "candidates.jsonl"
    with open(file_path, "w") as f:
        f.write(json.dumps(candidate_data) + "\n")
        
    # Depending on our parser, it might raise an exception or flag it. Let's see how our parser handles it.
    # Currently _parse_candidate doesn't throw on negative years. We should add that validation.
    # We will update schema.py to raise ValueError if years_of_experience < 0 or > 50
    candidates = load_candidates(str(file_path))
    assert len(candidates) == 0
