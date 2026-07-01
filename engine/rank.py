import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
import time

# Add the parent directory to sys.path to allow importing from data.validate_submission if needed.
# Since validate_submission.py is in data/, we can import it dynamically.
import importlib.util
from dataclasses import asdict

from engine.schema import load_candidates
from engine.features import compute_features
from engine.honeypot import is_honeypot
from engine.retrieval import HybridRetriever
from engine.jd_parser import JD
from engine.reasoning import generate_reasoning

def validate_submission_file(csv_path: str):
    # Dynamically import validate_submission.py from data/
    val_path = os.path.join(os.path.dirname(__file__), "..", "data", "validate_submission.py")
    if not os.path.exists(val_path):
        print("Warning: validate_submission.py not found in data/. Skipping validation.")
        return
        
    spec = importlib.util.spec_from_file_location("validate_submission", val_path)
    val_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(val_mod)
    
    print("Running validation script...")
    # validate_submission.py has validate_submission(path) function
    if hasattr(val_mod, 'validate_submission'):
        errors = val_mod.validate_submission(csv_path)
        if errors:
            print("FAIL: Validation errors found:")
            for e in errors:
                print(f"  - {e}")
        else:
            print("PASS: Submission is valid.")
    else:
        print("Warning: validate_submission.py has no validate_submission() function. Skipping validation.")

def run_pipeline(candidates, shortlist_size=100, model_path="engine/model.txt",
                  embeddings_path="engine/embeddings/candidate_embeddings.npy",
                  ids_path="engine/embeddings/candidate_ids.json",
                  jd_embedding_path="engine/embeddings/jd_embedding.npy",
                  custom_jd_text=None):
    """
    Core ranking pipeline. Can be called from CLI (main) or from the Flask API.
    Returns a list of ranked candidate dicts ready for the UI.
    """
    if not candidates:
        return []

    print(f"Loading precomputed artifacts (embeddings, model)...")
    retriever = HybridRetriever(candidates, embeddings_path, ids_path)
    jd_emb = np.load(jd_embedding_path)[0]
    
    bst = lgb.Booster(model_file=model_path)

    jd_narrative = custom_jd_text if custom_jd_text else JD.ideal_profile_narrative
    
    print("Computing features and scores...")
    retrieval_scores = retriever.score_all(jd_narrative, jd_embedding=jd_emb)
    
    feature_rows = []
    c_list = []
    hp_list = []
    feat_obj_list = []
    
    for c in candidates:
        hp_score, is_hp, hp_reasons = is_honeypot(c)
        r_scores = retrieval_scores.get(c.candidate_id, {"dense": 0.0, "sparse": 0.0})
        
        feats = compute_features(c, JD, precomputed_semantic_match=r_scores["dense"])
        
        feat_dict = {
            "years_experience_fit": feats.years_experience_fit,
            "title_trajectory_score": feats.title_trajectory_score,
            "production_ml_evidence_score": feats.production_ml_evidence_score,
            "domain_adjacency_penalty": feats.domain_adjacency_penalty,
            "consulting_only_penalty": feats.consulting_only_penalty,
            "research_only_disqualifier": feats.research_only_disqualifier,
            "role_relevance_score": feats.role_relevance_score,
            "skill_semantic_match": feats.skill_semantic_match,
            "bm25_score": r_scores["sparse"],
            "skill_trust_score": feats.skill_trust_score,
            "framework_enthusiast_penalty": feats.framework_enthusiast_penalty,
            "education_tier_score": feats.education_tier_score,
            "availability_score": feats.availability_score,
            "notice_period_fit": feats.notice_period_fit,
            "verification_trust_score": feats.verification_trust_score,
            "location_boost": feats.location_boost,
            "honeypot_suspicion_score": hp_score,
            "github_activity_boost": feats.github_activity_boost,
            "platform_reliability_score": feats.platform_reliability_score,
            "engagement_multiplier": feats.engagement_multiplier,
            "job_hopper_penalty": feats.job_hopper_penalty,
            "overqualified_penalty": feats.overqualified_penalty,
            "immediate_joiner_boost": feats.immediate_joiner_boost,
            "salary_mismatch_penalty": feats.salary_mismatch_penalty,
            "non_coder_penalty": feats.non_coder_penalty
        }
        
        feature_rows.append(feat_dict)
        c_list.append(c)
        hp_list.append(hp_score)
        feat_obj_list.append(feats)
        
    df = pd.DataFrame(feature_rows)
    
    # Model prediction - drop the new post-multipliers so the feature count matches training (17)
    cols_to_drop = ["github_activity_boost", "platform_reliability_score", "engagement_multiplier", "job_hopper_penalty", "overqualified_penalty", "immediate_joiner_boost", "salary_mismatch_penalty", "non_coder_penalty"]
    df_model = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    
    raw_scores = bst.predict(df_model)
    
    # Shift raw scores to be strictly positive so multipliers work correctly
    min_raw = np.min(raw_scores)
    if min_raw < 0:
        shifted_scores = raw_scores - min_raw + 0.1
    else:
        shifted_scores = raw_scores + 0.1
    
    # Apply multipliers to get unbounded final scores
    unbounded_scores = []
    for i, score in enumerate(shifted_scores):
        hp_downweight = 1.0
        if hp_list[i] > 0.6:
            hp_downweight = 0.001
        
        avail = df.loc[i, "availability_score"]
        
        # Apply new multipliers from the data schema
        gh_boost = df.loc[i, "github_activity_boost"] if "github_activity_boost" in df.columns else 1.0
        rel_score = df.loc[i, "platform_reliability_score"] if "platform_reliability_score" in df.columns else 1.0
        eng_mult = df.loc[i, "engagement_multiplier"] if "engagement_multiplier" in df.columns else 1.0
        job_hop = df.loc[i, "job_hopper_penalty"] if "job_hopper_penalty" in df.columns else 1.0
        overqual = df.loc[i, "overqualified_penalty"] if "overqualified_penalty" in df.columns else 1.0
        imm_join = df.loc[i, "immediate_joiner_boost"] if "immediate_joiner_boost" in df.columns else 1.0
        sal_mis = df.loc[i, "salary_mismatch_penalty"] if "salary_mismatch_penalty" in df.columns else 1.0
        non_coder = df.loc[i, "non_coder_penalty"] if "non_coder_penalty" in df.columns else 1.0
        
        final = score * max(0.1, avail) * hp_downweight * gh_boost * rel_score * eng_mult * job_hop * overqual * imm_join * sal_mis * non_coder
        unbounded_scores.append(final)
        
    print("Ranking candidates...")
    results = []
    for i in range(len(c_list)):
        results.append((unbounded_scores[i], c_list[i].candidate_id, i))
        
    # Sort by final unbounded score DESC, candidate_id ASC for ties
    results.sort(key=lambda x: (-x[0], x[1]))
    
    top_n_raw = results[:shortlist_size]
    
    # Rescale top N to [0.60, 0.99] to give a beautiful, readable distribution in the UI
    top_n = []
    if len(top_n_raw) > 0:
        max_top = top_n_raw[0][0]
        min_top = top_n_raw[-1][0]
        for val, cid, orig_idx in top_n_raw:
            if max_top > min_top:
                scaled = 0.60 + 0.39 * ((val - min_top) / (max_top - min_top))
            else:
                scaled = 0.99
            top_n.append((round(scaled, 4), cid, orig_idx))
            
    # Re-sort because rounding to 4 decimals can create new ties
    top_n.sort(key=lambda x: (-x[0], x[1]))
    
    print(f"Generating reasoning for top {len(top_n)}...")
    
    # Calculate SHAP contributions for top N
    top_indices = [orig_idx for _, _, orig_idx in top_n]
    top_df_model = df_model.iloc[top_indices]
    contribs = bst.predict(top_df_model, pred_contrib=True)
    feature_names = df_model.columns.tolist()
    
    json_export = []
    csv_rows = []
    
    for rank_idx, (score, cid, orig_idx) in enumerate(top_n):
        rank = rank_idx + 1
        cand = c_list[orig_idx]
        feats = feat_obj_list[orig_idx]
        
        # Get the specific SHAP contributions for this candidate
        shap_vals = contribs[rank_idx].tolist()
        
        reasoning = generate_reasoning(cand, feats, JD, rank, shap_contribs=shap_vals, feature_names=feature_names)
        
        csv_rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": f"{score:.4f}",
            "reasoning": reasoning["detailed"]
        })
        
        json_export.append({
            "candidate_id": cid,
            "rank": rank,
            "score": score,
            "reasoning": reasoning["detailed"],
            "preview_reasoning": reasoning["preview"],
            "name": cand.profile.anonymized_name,
            "title": cand.profile.current_title,
            "company": cand.profile.current_company,
            "yoe": cand.profile.years_of_experience,
            "features": feature_rows[orig_idx],
            "notice_period_days": cand.redrob_signals.notice_period_days,
            "expected_salary": asdict(cand.redrob_signals.expected_salary_range_inr_lpa),
            "availability_score": feats.availability_score,
            "honeypot_score": hp_list[orig_idx],
            "redrob_signals": asdict(cand.redrob_signals),
            "skills": [asdict(s) for s in cand.skills],
            "career_history": [asdict(ch) for ch in cand.career_history],
            "education": [asdict(e) for e in cand.education],
            "certifications": [asdict(cert) for cert in cand.certifications] if hasattr(cand, 'certifications') and cand.certifications else [],
            "languages": [asdict(l) for l in cand.languages] if hasattr(cand, 'languages') and cand.languages else [],
            "location": cand.profile.location,
            "country": cand.profile.country,
            "headline": cand.profile.headline,
            "summary": cand.profile.summary
          })

    return json_export, csv_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=str, default="data/candidates.jsonl")
    parser.add_argument("--out", type=str, default="submission.csv")
    parser.add_argument("--export-ui-json", type=str, default="app/public/ranked_candidates.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", type=str, default="engine/model.txt")
    parser.add_argument("--embeddings", type=str, default="engine/embeddings/candidate_embeddings.npy")
    parser.add_argument("--ids", type=str, default="engine/embeddings/candidate_ids.json")
    parser.add_argument("--jd_embedding", type=str, default="engine/embeddings/jd_embedding.npy")
    args = parser.parse_args()

    np.random.seed(args.seed)
    
    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    if args.limit:
        candidates = candidates[:args.limit]

    json_export, csv_rows = run_pipeline(
        candidates,
        shortlist_size=100,
        model_path=args.model,
        embeddings_path=args.embeddings,
        ids_path=args.ids,
        jd_embedding_path=args.jd_embedding
    )

    # Write JSON for UI
    if args.export_ui_json:
        export_dir = os.path.dirname(args.export_ui_json)
        if export_dir:
            os.makedirs(export_dir, exist_ok=True)
        with open(args.export_ui_json, "w", encoding="utf-8") as f:
            json.dump(json_export, f, indent=2)
        print(f"Wrote rich JSON to {args.export_ui_json}")

    # Write CSV
    out_df = pd.DataFrame(csv_rows)
    try:
        out_df.to_csv(args.out, index=False, encoding="utf-8")
        print(f"Wrote {len(out_df)} rows to {args.out}")
    except PermissionError:
        print(f"Permission denied: {args.out} is open in another program. Could not update CSV.")
        
    # Validate
    validate_submission_file(args.out)

if __name__ == "__main__":
    main()
