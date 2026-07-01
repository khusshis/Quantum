import hashlib
from engine.schema import Candidate
from engine.features import CandidateFeatures
from engine.jd_parser import ParsedJD

def generate_reasoning(candidate: Candidate, features: CandidateFeatures, jd: ParsedJD, rank: int) -> str:
    """
    Generates a grounded, template-based reasoning string (no LLMs).
    """
    # 1. Facts extraction
    yoe = candidate.profile.years_of_experience
    title = candidate.profile.current_title or "Engineer"
    
    # 2. Extract matched skills
    jd_skills = ["python", "embedding", "retrieval", "search", "ranking", "llm", "pinecone", "weaviate", "qdrant"]
    matched_skills = [s.name for s in candidate.skills if any(jsk in s.name.lower() for jsk in jd_skills)]
    if not matched_skills and candidate.skills:
        matched_skills = [s.name for s in candidate.skills[:2]]
    
    skill_str = " and ".join(matched_skills[:2]) if matched_skills else "general engineering"
    
    # 3. Connection to JD
    if features.production_ml_evidence_score > 0.5:
        jd_category = "production embeddings/retrieval experience"
    elif features.years_experience_fit == 1.0:
        jd_category = "ideal experience range (5-9 years)"
    elif features.skill_trust_score > 0.5:
        jd_category = "strong python and ML toolset"
    else:
        jd_category = "general technical background"
        
    # 4. Identify concerns
    concerns = []
    if candidate.redrob_signals.notice_period_days > 30:
        concerns.append(f"notice period is {candidate.redrob_signals.notice_period_days} days (above JD preference)")
    if features.availability_score < 0.3:
        concerns.append("platform activity is low")
    if features.consulting_only_penalty < 0.5:
        concerns.append("background is heavily consulting-focused")
    if features.domain_adjacency_penalty < 0.8:
        concerns.append("experience is primarily CV/robotics rather than NLP/IR")
    if features.framework_enthusiast_penalty < 0.8:
        concerns.append("skills show a framework-enthusiast pattern")

    concern_str = ""
    if concerns:
        concern_str = "; however, " + " and ".join(concerns[:2]) + "."
    else:
        concern_str = "."

    # 5. Variation via hashing
    # Hash candidate ID to pick a deterministic template
    h = int(hashlib.md5(candidate.candidate_id.encode('utf-8')).hexdigest(), 16)
    
    if rank <= 10:
        # Confidently positive
        templates = [
            f"Strong fit driven by {jd_category}: {yoe} years of experience as a {title}, with verified expertise in {skill_str}{concern_str}",
            f"Top candidate based on {jd_category}. Brings {yoe} years of experience currently as {title}, leveraging {skill_str}{concern_str}",
            f"Highly aligned with {jd_category}, featuring {yoe} years as a {title} and demonstrated hands-on work with {skill_str}{concern_str}"
        ]
        return templates[h % len(templates)]
    elif rank <= 60:
        # Balanced/mixed
        templates = [
            f"Solid candidate with {yoe} years as a {title} matching our need for {jd_category} (skills: {skill_str}){concern_str}",
            f"Meets core requirements for {jd_category} via {yoe} years of experience as {title} with {skill_str}{concern_str}",
            f"A fair fit providing {yoe} years as a {title} and {skill_str} aligned to {jd_category}{concern_str}"
        ]
        return templates[h % len(templates)]
    else:
        # Foreground the concern before positive
        if not concerns:
            concern_prefix = "Lower confidence match."
        else:
            concern_prefix = "Included as filler given " + concerns[0] + "."
        
        templates = [
            f"{concern_prefix} Profile shows {yoe} years as a {title} with {skill_str}.",
            f"{concern_prefix} Brings {yoe} years of experience as {title} ({skill_str})."
        ]
        return templates[h % len(templates)]
