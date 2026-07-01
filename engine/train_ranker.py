"""
train_ranker.py: OFFLINE training script for LightGBM Learning-to-Rank model.
This script is run ONCE, offline, NOT during the 5-minute ranking step.
"""

import os
import argparse
import numpy as np
import pandas as pd
import lightgbm as lgb
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from engine.schema import load_candidates
from engine.features import compute_features
from engine.honeypot import is_honeypot
from engine.retrieval import HybridRetriever
from engine.weak_labels import generate_weak_label
from engine.jd_parser import JD

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=str, default="data/candidates.jsonl")
    parser.add_argument("--embeddings", type=str, default="engine/embeddings/candidate_embeddings.npy")
    parser.add_argument("--ids", type=str, default="engine/embeddings/candidate_ids.json")
    parser.add_argument("--jd_embedding", type=str, default="engine/embeddings/jd_embedding.npy")
    parser.add_argument("--out_dir", type=str, default="engine")
    args = parser.parse_args()
    
    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    
    print("Setting up retrieval...")
    retriever = HybridRetriever(candidates, args.embeddings, args.ids)
    
    print("Scoring candidates (retrieval)...")
    jd_emb = np.load(args.jd_embedding)[0]
    retrieval_scores = retriever.score_all(JD.ideal_profile_narrative, jd_embedding=jd_emb)
    
    print("Computing features and weak labels...")
    feature_rows = []
    labels = []
    
    for c in candidates:
        hp_score, is_hp, hp_reasons = is_honeypot(c)
        r_scores = retrieval_scores.get(c.candidate_id, {"dense": 0.0, "sparse": 0.0})
        
        feats = compute_features(c, JD, precomputed_semantic_match=r_scores["dense"])
        
        weak_label = generate_weak_label(c, feats, hp_score, r_scores)
        
        # Build feature dict
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
        labels.append(weak_label)
        
    df = pd.DataFrame(feature_rows)
    y = np.array(labels)
    
    print(f"Feature matrix shape: {df.shape}")
    
    # Train/Val split
    # Since this is a single JD, we treat the entire dataset as a single query group.
    # To properly evaluate NDCG on a holdout set, we split candidates. 
    # LightGBM requires groups. We will have 1 group for train, 1 for val.
    X_train, X_val, y_train, y_val = train_test_split(df, y, test_size=0.2, random_state=42)
    
    def chunk_groups(total_len, chunk_size=10000):
        groups = []
        while total_len > 0:
            groups.append(min(total_len, chunk_size))
            total_len -= chunk_size
        return groups

    group_train = chunk_groups(len(X_train))
    group_val = chunk_groups(len(X_val))
    
    print("Training LightGBM Ranker...")
    ranker = lgb.LGBMRanker(
        objective="lambdarank",
        metric="ndcg",
        eval_at=[10, 50],
        learning_rate=0.05,
        n_estimators=100,
        importance_type="gain",
        random_state=42
    )
    
    # LightGBM requires validation data for early stopping
    ranker.fit(
        X_train, y_train,
        group=group_train,
        eval_set=[(X_val, y_val)],
        eval_group=[group_val],
        callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(10)]
    )
    
    # Save model
    model_path = os.path.join(args.out_dir, "model.txt")
    ranker.booster_.save_model(model_path)
    print(f"Saved trained model to {model_path}")
    
    # Feature Importance Plot
    importance = ranker.feature_importances_
    features = X_train.columns
    
    plt.figure(figsize=(10, 8))
    indices = np.argsort(importance)
    plt.barh(range(len(indices)), importance[indices], color='b', align='center')
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel('LightGBM Feature Importance (Gain)')
    plt.title('Feature Importances for Candidate Ranker')
    plt.tight_layout()
    
    plot_path = os.path.join(args.out_dir, "feature_importance.png")
    plt.savefig(plot_path)
    print(f"Saved feature importance plot to {plot_path}")

if __name__ == "__main__":
    main()
