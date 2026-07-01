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
        
    if not candidates:
        print("No candidates loaded.")
        return
        
    print("Loading precomputed artifacts (embeddings, model)...")
    retriever = HybridRetriever(candidates, args.embeddings, args.ids)
    jd_emb = np.load(args.jd_embedding)[0]
    
    bst = lgb.Booster(model_file=args.model)
    
    print("Computing features and scores...")
    retrieval_scores = retriever.score_all(JD.ideal_profile_narrative, jd_embedding=jd_emb)
    
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
            "engagement_multiplier": feats.engagement_multiplier
        }
        
        feature_rows.append(feat_dict)
        c_list.append(c)
        hp_list.append(hp_score)
        feat_obj_list.append(feats)
        
    df = pd.DataFrame(feature_rows)
    
    # Model prediction - drop the new post-multipliers so the feature count matches training (17)
    cols_to_drop = ["github_activity_boost", "platform_reliability_score", "engagement_multiplier"]
    df_model = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
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
        
        final = score * max(0.1, avail) * hp_downweight * gh_boost * rel_score * eng_mult
        unbounded_scores.append(final)
        
    print("Ranking candidates...")
    results = []
    for i in range(len(c_list)):
        results.append((unbounded_scores[i], c_list[i].candidate_id, i))
        
    # Sort by final unbounded score DESC, candidate_id ASC for ties
    results.sort(key=lambda x: (-x[0], x[1]))
    
    top_100_raw = results[:100]
    
    # Rescale top 100 to [0.60, 0.99] to give a beautiful, readable distribution in the UI
    top_100 = []
    if len(top_100_raw) > 0:
        max_top = top_100_raw[0][0]
        min_top = top_100_raw[-1][0]
        for val, cid, orig_idx in top_100_raw:
            if max_top > min_top:
                scaled = 0.60 + 0.39 * ((val - min_top) / (max_top - min_top))
            else:
                scaled = 0.99
            top_100.append((round(scaled, 4), cid, orig_idx))
            
    # Re-sort top_100 because rounding to 4 decimals can create new ties that violate candidate_id ASC
    top_100.sort(key=lambda x: (-x[0], x[1]))
    
    print(f"Generating reasoning for top {len(top_100)}...")
    
    # Calculate SHAP contributions for top 100
    top_indices = [orig_idx for _, _, orig_idx in top_100]
    top_df_model = df_model.iloc[top_indices]
    contribs = bst.predict(top_df_model, pred_contrib=True)
    feature_names = df_model.columns.tolist()
    
    csv_rows = []
    json_export = []
    
    for rank_idx, (score, cid, orig_idx) in enumerate(top_100):
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
            "redrob_signals": asdict(cand.redrob_signals)
        })
        
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
