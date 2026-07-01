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
            "skill_semantic_match": feats.skill_semantic_match,
            "bm25_score": r_scores["sparse"],
            "skill_trust_score": feats.skill_trust_score,
            "framework_enthusiast_penalty": feats.framework_enthusiast_penalty,
            "education_tier_score": feats.education_tier_score,
            "availability_score": feats.availability_score,
            "notice_period_fit": feats.notice_period_fit,
            "verification_trust_score": feats.verification_trust_score,
            "location_boost": feats.location_boost,
            "honeypot_suspicion_score": hp_score
        }
        
        feature_rows.append(feat_dict)
        c_list.append(c)
        hp_list.append(hp_score)
        feat_obj_list.append(feats)
        
    df = pd.DataFrame(feature_rows)
    
    # Model prediction
    raw_scores = bst.predict(df)
    
    # Final adjustment
    # Applying availability multiplier and honeypot downweight
    final_scores = []
    for i, score in enumerate(raw_scores):
        hp_downweight = 1.0
        if hp_list[i] > 0.6:
            hp_downweight = 0.001
        
        avail = df.loc[i, "availability_score"]
        final = score * max(0.1, avail) * hp_downweight
        final_scores.append(round(final, 4))
        
    print("Ranking candidates...")
    results = []
    for i in range(len(c_list)):
        results.append((final_scores[i], c_list[i].candidate_id, i))
        
    # Sort by final score DESC, candidate_id ASC for ties
    results.sort(key=lambda x: (-x[0], x[1]))
    
    top_100 = results[:100]
    
    print(f"Generating reasoning for top {len(top_100)}...")
    csv_rows = []
    json_export = []
    
    for rank_idx, (score, cid, orig_idx) in enumerate(top_100):
        rank = rank_idx + 1
        cand = c_list[orig_idx]
        feats = feat_obj_list[orig_idx]
        
        reasoning = generate_reasoning(cand, feats, JD, rank)
        
        csv_rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": f"{score:.4f}",
            "reasoning": reasoning
        })
        
        json_export.append({
            "candidate_id": cid,
            "rank": rank,
            "score": score,
            "reasoning": reasoning,
            "name": cand.profile.anonymized_name,
            "title": cand.profile.current_title,
            "company": cand.profile.current_company,
            "features": feature_rows[orig_idx],
            "notice_period_days": cand.redrob_signals.notice_period_days,
            "availability_score": feats.availability_score,
            "honeypot_score": hp_list[orig_idx]
        })
        
    # Write CSV
    out_df = pd.DataFrame(csv_rows)
    out_df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {len(out_df)} rows to {args.out}")
    
    # Write JSON for UI
    if args.export_ui_json:
        os.makedirs(os.path.dirname(args.export_ui_json), exist_ok=True)
        with open(args.export_ui_json, "w", encoding="utf-8") as f:
            json.dump(json_export, f, indent=2)
        print(f"Wrote rich JSON to {args.export_ui_json}")
        
    # Validate
    validate_submission_file(args.out)

if __name__ == "__main__":
    main()
