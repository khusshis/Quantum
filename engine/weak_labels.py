"""
weak_labels.py: Heuristic pseudo-relevance label generator.
Used ONLY to create training signal for the LightGBM model, not a claim of ground truth.
Produces a 0-4 relevance label.
"""

from engine.schema import Candidate
from engine.features import CandidateFeatures

def generate_weak_label(candidate: Candidate, features: CandidateFeatures, honeypot_score: float, retrieval_scores: dict = None) -> int:
    """
    Returns an ordinal label from 0 to 4.
    0: Bad / Honeypot
    1: Poor
    2: Fair
    3: Good
    4: Excellent
    """
    if honeypot_score > 0.6:
        return 0
        
    if features.research_only_disqualifier < 0.5:
        return 0

    score = 0.0
    
    # Career fit adds up to 3 points
    score += features.years_experience_fit
    score += features.title_trajectory_score
    score += features.production_ml_evidence_score
    score *= features.domain_adjacency_penalty
    score *= features.consulting_only_penalty
    
    # Skill match adds up to 1.5 points
    if retrieval_scores:
        dense = max(0.0, retrieval_scores.get("dense", 0.0))
        sparse = max(0.0, retrieval_scores.get("sparse", 0.0))
        # Simple weighted sum for weak label
        skill_score = (dense * 0.7 + sparse * 0.3) * 1.5
        score += skill_score
        
    score += features.skill_trust_score * 0.5
    score *= features.framework_enthusiast_penalty
    
    # Behavior is a multiplier
    score *= (features.availability_score + 0.1)  # allow tiny score even if unavailable just based on resume
    
    # Map raw score to 0-4 buckets (tuned heuristically)
    # The max possible score is roughly 5.0
    if score < 1.0:
        return 1
    elif score < 2.0:
        return 2
    elif score < 3.0:
        return 3
    else:
        return 4
