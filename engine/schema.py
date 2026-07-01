import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class CandidateProfile:
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str

@dataclass
class CareerHistoryEntry:
    company: str
    title: str
    start_date: str
    end_date: Optional[str]
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str

@dataclass
class Education:
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Optional[str] = None

@dataclass
class Skill:
    name: str
    proficiency: str
    endorsements: int
    duration_months: Optional[int] = None

@dataclass
class Certification:
    name: str
    issuer: str
    year: int

@dataclass
class Language:
    language: str
    proficiency: str

@dataclass
class ExpectedSalaryRange:
    min: float
    max: float

@dataclass
class RedrobSignals:
    profile_completeness_score: float
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int
    applications_submitted_30d: int
    recruiter_response_rate: float
    avg_response_time_hours: float
    skill_assessment_scores: Dict[str, float]
    connection_count: int
    endorsements_received: int
    notice_period_days: int
    expected_salary_range_inr_lpa: ExpectedSalaryRange
    preferred_work_mode: str
    willing_to_relocate: bool
    github_activity_score: Optional[float]
    search_appearance_30d: int
    saved_by_recruiters_30d: int
    interview_completion_rate: float
    offer_acceptance_rate: Optional[float]
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool

@dataclass
class Candidate:
    candidate_id: str
    profile: CandidateProfile
    career_history: List[CareerHistoryEntry]
    education: List[Education]
    skills: List[Skill]
    redrob_signals: RedrobSignals
    certifications: List[Certification] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)

def _parse_candidate(data: Dict[str, Any]) -> Candidate:
    profile_data = data["profile"]
    profile = CandidateProfile(**profile_data)
    if profile.years_of_experience < 0 or profile.years_of_experience > 50:
        raise ValueError(f"years_of_experience out of range: {profile.years_of_experience}")
    
    career_history = []
    for entry in data["career_history"]:
        career_history.append(CareerHistoryEntry(**entry))
        
    education = []
    for entry in data.get("education", []):
        education.append(Education(**entry))
        
    skills = []
    for entry in data.get("skills", []):
        skills.append(Skill(**entry))
        
    certifications = []
    for entry in data.get("certifications", []):
        certifications.append(Certification(**entry))
        
    languages = []
    for entry in data.get("languages", []):
        languages.append(Language(**entry))
        
    signals_data = data["redrob_signals"]
    
    # Handle -1 sentinel values
    if signals_data.get("github_activity_score") == -1:
        signals_data["github_activity_score"] = None
    if signals_data.get("offer_acceptance_rate") == -1:
        signals_data["offer_acceptance_rate"] = None
        
    salary_data = signals_data.pop("expected_salary_range_inr_lpa")
    salary = ExpectedSalaryRange(**salary_data)
    signals = RedrobSignals(expected_salary_range_inr_lpa=salary, **signals_data)
    
    return Candidate(
        candidate_id=data["candidate_id"],
        profile=profile,
        career_history=career_history,
        education=education,
        skills=skills,
        redrob_signals=signals,
        certifications=certifications,
        languages=languages
    )

def load_candidates(path: str) -> List[Candidate]:
    candidates = []
    malformed_count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                candidate = _parse_candidate(data)
                candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Malformed row at line {line_num}: {e}")
                malformed_count += 1
    
    if malformed_count > 0:
        logger.info(f"Skipped {malformed_count} malformed rows.")
    return candidates
