"""
weak_labels.py: Heuristic pseudo-relevance label generator.
Used ONLY to create training signal for the LightGBM model, not a claim of ground truth.
Returns a continuous score (used as regression target) and a bucketed 0-4 ordinal label.
"""

from engine.schema import Candidate
from engine.features import CandidateFeatures

def generate_weak_label(candidate: Candidate, features: CandidateFeatures, honeypot_score: float, retrieval_scores: dict = None):
    """
    Returns (continuous_score: float, ordinal_label: int).
    continuous_score is the raw heuristic score before bucketing (used as regression target).
    ordinal_label is the 0-4 bucketed version (for diagnostics/backward compat).
    """
    if honeypot_score > 0.6:
        return 0.0, 0
        
    if features.research_only_disqualifier < 0.5:
        return 0.0, 0

    score = 0.0
    
    # Career fit adds up to 3 points
    score += features.years_experience_fit
    score += features.title_trajectory_score
    score += features.production_ml_evidence_score
    
    # Skill match adds up to 1.5 points
    if retrieval_scores:
        dense = max(0.0, retrieval_scores.get("dense", 0.0))
        sparse = max(0.0, retrieval_scores.get("sparse", 0.0))
        skill_score = (dense * 0.7 + sparse * 0.3) * 1.5
        score += skill_score
        
    score += features.skill_trust_score * 0.5
    
    # --- MULTIPLICATIVE PENALTIES applied AFTER skill scores ---
    score *= features.domain_adjacency_penalty
    score *= features.consulting_only_penalty
    score *= features.framework_enthusiast_penalty
    score *= features.role_relevance_score  # The critical gate
    
    # Behavior is a multiplier
    score *= (features.availability_score + 0.1)
    
    # Bucket into ordinal label for diagnostics
    if score < 1.0:
        label = 1
    elif score < 2.0:
        label = 2
    elif score < 3.0:
        label = 3
    else:
        label = 4
    
    return score, label
