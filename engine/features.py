import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from engine.schema import Candidate
from engine.jd_parser import ParsedJD

@dataclass
class CandidateFeatures:
    years_experience_fit: float
    title_trajectory_score: float
    production_ml_evidence_score: float
    domain_adjacency_penalty: float
    consulting_only_penalty: float
    research_only_disqualifier: float
    
    skill_semantic_match: float
    skill_trust_score: float
    framework_enthusiast_penalty: float
    
    education_tier_score: float
    
    availability_score: float
    notice_period_fit: float
    salary_alignment_flag: float
    verification_trust_score: float
    location_boost: float

def compute_features(candidate: Candidate, jd: ParsedJD, precomputed_semantic_match: float = 0.0) -> CandidateFeatures:
    # --- CAREER-FIT FEATURES ---
    
    # years_experience_fit
    yoe = candidate.profile.years_of_experience
    min_yoe, max_yoe = jd.required_years_range
    mid_yoe = (min_yoe + max_yoe) / 2
    # simple triangular decay
    if min_yoe <= yoe <= max_yoe:
        yoe_fit = 1.0
    else:
        dist = min(abs(yoe - min_yoe), abs(yoe - max_yoe))
        yoe_fit = max(0.0, 1.0 - (dist / 5.0))
        
    # title_trajectory_score
    title_trajectory = 0.5
    title_chasing_jobs = 0
    recent_manager = False
    for entry in candidate.career_history:
        title_lower = entry.title.lower()
        if entry.duration_months <= 18 and any(k in title_lower for k in ["senior", "staff", "principal", "lead", "manager"]):
            title_chasing_jobs += 1
        if entry.is_current and entry.duration_months >= 18 and any(k in title_lower for k in ["architect", "lead", "manager"]):
            desc_lower = entry.description.lower()
            if not any(k in desc_lower for k in ["code", "python", "hands-on", "implemented", "developed"]):
                recent_manager = True
    
    if title_chasing_jobs >= 3:
        title_trajectory -= 0.3
    if recent_manager:
        title_trajectory -= 0.3
        
    title_trajectory = max(0.0, title_trajectory)
    
    # production_ml_evidence_score
    prod_keywords = ["deployed", "production", "served", "requests", "in prod", "real users", "scaled to"]
    ml_keywords = ["retrieval", "ranking", "embeddings", "search", "recommender", "llm"]
    prod_score = 0.0
    for entry in candidate.career_history:
        desc_lower = entry.description.lower()
        has_prod = any(k in desc_lower for k in prod_keywords)
        has_ml = any(k in desc_lower for k in ml_keywords)
        if has_prod and has_ml:
            prod_score += 0.5
    prod_score = min(1.0, prod_score)
    
    # domain_adjacency_penalty
    cv_speech_keywords = ["computer vision", "cv", "speech", "robotics", "object detection", "asr"]
    nlp_ir_keywords = ["nlp", "ir", "information retrieval", "natural language", "text"]
    
    cv_speech_count = 0
    nlp_ir_count = 0
    for entry in candidate.career_history:
        desc_lower = entry.description.lower()
        title_lower = entry.title.lower()
        if any(k in desc_lower or k in title_lower for k in cv_speech_keywords):
            cv_speech_count += 1
        if any(k in desc_lower or k in title_lower for k in nlp_ir_keywords):
            nlp_ir_count += 1
            
    if cv_speech_count > 0 and nlp_ir_count == 0:
        domain_penalty = 0.5  # reduced score
    else:
        domain_penalty = 1.0

    # consulting_only_penalty
    consulting_firms = [f.lower() for f in jd.consulting_companies]
    all_consulting = True
    any_product_before_current = False
    
    for i, entry in enumerate(candidate.career_history):
        is_consulting = any(c in entry.company.lower() for c in consulting_firms)
        if not is_consulting:
            all_consulting = False
            if not entry.is_current:
                any_product_before_current = True

    if all_consulting:
        consulting_penalty = 0.3
    elif candidate.career_history and any(c in candidate.career_history[0].company.lower() for c in consulting_firms) and any_product_before_current:
        consulting_penalty = 1.0 # Restored
    else:
        consulting_penalty = 1.0
        
    # research_only_disqualifier
    academic_keywords = ["research assistant", "phd", "postdoc", "academic", "university", "lab"]
    all_research = True
    any_prod_ever = False
    for entry in candidate.career_history:
        is_research = any(k in entry.title.lower() or k in entry.company.lower() for k in academic_keywords)
        if not is_research:
            all_research = False
        desc_lower = entry.description.lower()
        if any(k in desc_lower for k in prod_keywords):
            any_prod_ever = True
            
    if all_research and not any_prod_ever:
        research_disqualifier = 0.1
    else:
        research_disqualifier = 1.0
        
    # --- SKILLS FEATURES ---
    
    # skill_trust_score
    prof_weights = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}
    skill_trust = 0.0
    trendy_frameworks = ["langchain", "llamaindex", "huggingface", "openai"]
    trendy_count = 0
    total_trendy_duration = 0
    total_trendy_endorsements = 0
    
    for skill in candidate.skills:
        name_lower = skill.name.lower()
        prof_w = prof_weights.get(skill.proficiency.lower(), 0.5)
        dur = skill.duration_months or 0
        end = skill.endorsements or 0
        
        trust_contribution = math.log1p(end) * math.log1p(dur) * prof_w
        skill_trust += trust_contribution
        
        if any(f in name_lower for f in trendy_frameworks):
            trendy_count += 1
            total_trendy_duration += dur
            total_trendy_endorsements += end

    # Normalize skill trust roughly
    skill_trust = min(1.0, skill_trust / 50.0)
    
    # framework_enthusiast_penalty
    framework_penalty = 1.0
    if trendy_count > 3:
        avg_dur = total_trendy_duration / trendy_count
        avg_end = total_trendy_endorsements / trendy_count
        if avg_dur < 6 and avg_end < 5 and prod_score < 0.3:
            framework_penalty = 0.5
            
    # --- EDUCATION FEATURES ---
    tier_scores = {"tier_1": 0.2, "tier_2": 0.1, "tier_3": 0.05, "tier_4": 0.0, "unknown": 0.0}
    edu_score = 0.0
    for edu in candidate.education:
        if edu.tier:
            edu_score = max(edu_score, tier_scores.get(edu.tier.lower(), 0.0))
            
    # --- BEHAVIORAL FEATURES ---
    signals = candidate.redrob_signals
    
    # recency decay
    try:
        last_active = datetime.strptime(signals.last_active_date, "%Y-%m-%d")
        days_since_active = (datetime(2024, 6, 1) - last_active).days # Assume some static ref date, or datetime.now() if dynamic
    except:
        days_since_active = 0
    
    recency_score = max(0.0, 1.0 - (days_since_active / 365.0))
    open_work_bonus = 1.2 if signals.open_to_work_flag else 1.0
    
    resp_rate = signals.recruiter_response_rate
    int_comp = signals.interview_completion_rate
    
    availability = (recency_score * open_work_bonus * (resp_rate + 0.1) * (int_comp + 0.1))
    availability = min(1.0, availability)
    
    # notice_period_fit
    np_days = signals.notice_period_days
    if np_days <= 30:
        np_fit = 1.0
    elif np_days <= 60:
        np_fit = 0.7
    else:
        np_fit = 0.4
        
    # verification
    ver_score = 0.0
    if signals.verified_email: ver_score += 0.05
    if signals.verified_phone: ver_score += 0.05
    if signals.linkedin_connected: ver_score += 0.05
    
    # location_boost
    loc_boost = 0.0
    cand_loc = candidate.profile.location.lower()
    if any(pref.lower() in cand_loc for pref in jd.location_preference) or signals.willing_to_relocate:
        loc_boost = 0.1
        
    return CandidateFeatures(
        years_experience_fit=yoe_fit,
        title_trajectory_score=title_trajectory,
        production_ml_evidence_score=prod_score,
        domain_adjacency_penalty=domain_penalty,
        consulting_only_penalty=consulting_penalty,
        research_only_disqualifier=research_disqualifier,
        skill_semantic_match=precomputed_semantic_match,
        skill_trust_score=skill_trust,
        framework_enthusiast_penalty=framework_penalty,
        education_tier_score=edu_score,
        availability_score=availability,
        notice_period_fit=np_fit,
        salary_alignment_flag=1.0, # Not used heavily
        verification_trust_score=ver_score,
        location_boost=loc_boost
    )
