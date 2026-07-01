import hashlib
from engine.schema import Candidate
from engine.features import CandidateFeatures
from engine.jd_parser import ParsedJD

def generate_reasoning(candidate: Candidate, features: CandidateFeatures, jd: ParsedJD, rank: int,
                       shap_contribs: list = None, feature_names: list = None) -> dict:
    """
    Generates a mathematically grounded reasoning string using LightGBM SHAP feature contributions.
    Returns a dict with 'preview' and 'detailed' keys.
    """
    if shap_contribs is None or feature_names is None:
        return {
            "preview": "Solid technical foundation",
            "detailed": "Ranked based on overall profile alignment."
        }

    # Remove the base value (last element in LightGBM pred_contrib output)
    feat_vals = shap_contribs[:-1]
    
    # Combine feature names with their contributions
    contributions = list(zip(feature_names, feat_vals))
    
    # Sort by absolute contribution to find the strongest drivers
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Format a human-readable feature name
    def format_feat(f_name):
        return f_name.replace("_", " ").title()
        
    positives = []
    negatives = []
    
    pos_preview = []
    for f_name, f_val in contributions:
        # Ignore weak signals
        if abs(f_val) < 0.05:
            continue
            
        formatted_name = format_feat(f_name)
        if f_val > 0:
            # Scale SHAP roughly to a 0-100 metric for user-friendly display
            scaled_score = min(99, max(75, int(75 + f_val * 12)))
            pos_preview.append(f"{formatted_name} {scaled_score}")
            positives.append(formatted_name)
        else:
            negatives.append(formatted_name)
            
    # Construct the preview string
    preview_str = " | ".join(pos_preview[:3]) if pos_preview else "Solid technical foundation"
            
    # Extract candidate background for profile summary
    title = candidate.profile.current_title or "professional"
    yoe = candidate.profile.years_of_experience
    skills_list = [s.name for s in getattr(candidate, 'skills', [])[:3]]
    skills_str = f"expertise in {', '.join(skills_list)}" if skills_list else "strong technical skills"

    # Construct the detailed explanation as a profile summary
    detailed = f"{yoe} YOE {title} with {skills_str}. "
    if len(positives) >= 2:
        detailed += f"Top candidate driven by exceptionally high {positives[0]} and {positives[1]}."
    elif positives:
        detailed += f"Solid match due to strong {positives[0]}."
    else:
        detailed += "Matched based on overall profile alignment."
        
    if negatives:
        detailed += f" (Note: Minor gap in {negatives[0]})."
        
    return {
        "preview": preview_str,
        "detailed": detailed
    }
