import os
import sys
import time
import json
import streamlit as st
import pandas as pd
import lightgbm as lgb
import numpy as np

# Add repo root to path so we can import engine
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from engine.schema import load_candidates
from engine.features import compute_features
from engine.honeypot import is_honeypot
from engine.retrieval import HybridRetriever
from engine.jd_parser import JD
from engine.reasoning import generate_reasoning

st.set_page_config(page_title="AI Engineer Candidate Ranker (Offline)", layout="wide")

st.title("Grounded Candidate Ranker")
st.markdown("This is a local offline sandbox demonstrating the ranking engine on a small sample of candidates. No external API calls are made.")

sample_path = os.path.join(os.path.dirname(__file__), "sample_candidates.jsonl")

uploaded_file = st.file_uploader("Upload candidates.jsonl (Max 100 rows)", type=["jsonl"])

candidates_file = None
if uploaded_file is not None:
    # Save temporarily
    temp_path = "temp_uploaded_candidates.jsonl"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    candidates_file = temp_path
else:
    candidates_file = sample_path
    st.info(f"Using default sample: {sample_path}")

if st.button("Run Ranking Pipeline"):
    start_time = time.time()
    
    with st.spinner("Loading candidates..."):
        candidates = load_candidates(candidates_file)
        if len(candidates) > 100:
            st.warning(f"File has {len(candidates)} candidates. Truncating to 100 for interactive demo.")
            candidates = candidates[:100]
            
    with st.spinner("Loading artifacts..."):
        # We assume the artifacts are available in the engine folder
        model_path = os.path.join(repo_root, "engine", "model.txt")
        emb_path = os.path.join(repo_root, "engine", "embeddings", "candidate_embeddings.npy")
        ids_path = os.path.join(repo_root, "engine", "embeddings", "candidate_ids.json")
        jd_emb_path = os.path.join(repo_root, "engine", "embeddings", "jd_embedding.npy")
        
        # NOTE: For a real subset upload, we'd need to compute embeddings live since we don't have them in the offline cache.
        # But per the spec for the sandbox, it says we can use precomputed artifacts or compute.
        # Since this is a demo, we will check if candidate IDs exist in the precomputed index.
        # If not (or if missing), we'll do a fallback embedding live using sentence-transformers.
        try:
            from sentence_transformers import SentenceTransformer
            from engine.embed import build_candidate_text
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Embed jd
            jd_emb = model.encode([JD.ideal_profile_narrative], convert_to_numpy=True)[0]
            
            # Embed candidates
            texts = [build_candidate_text(c) for c in candidates]
            candidate_embeddings = model.encode(texts, convert_to_numpy=True)
            
            # Temporary save for HybridRetriever
            temp_emb = "temp_emb.npy"
            temp_ids = "temp_ids.json"
            np.save(temp_emb, candidate_embeddings)
            with open(temp_ids, "w") as f:
                json.dump([c.candidate_id for c in candidates], f)
                
            retriever = HybridRetriever(candidates, temp_emb, temp_ids)
            
        except Exception as e:
            st.error(f"Error during embedding generation: {e}")
            st.stop()
            
        try:
            bst = lgb.Booster(model_file=model_path)
        except Exception as e:
            st.error(f"Could not load LightGBM model from {model_path}. Make sure to train it first!")
            st.stop()

    with st.spinner("Scoring and Ranking..."):
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
        raw_scores = bst.predict(df)
        
        final_scores = []
        for i, score in enumerate(raw_scores):
            hp_downweight = 1.0
            if hp_list[i] > 0.6:
                hp_downweight = 0.001
            avail = df.loc[i, "availability_score"]
            final = score * max(0.1, avail) * hp_downweight
            final_scores.append(final)
            
        results = []
        for i in range(len(c_list)):
            results.append((final_scores[i], c_list[i], i))
            
        results.sort(key=lambda x: (-x[0], x[1].candidate_id))
        
        out_rows = []
        for rank_idx, (score, cand, orig_idx) in enumerate(results):
            rank = rank_idx + 1
            feats = feat_obj_list[orig_idx]
            reasoning = generate_reasoning(cand, feats, JD, rank)
            
            out_rows.append({
                "Rank": rank,
                "Name": cand.profile.anonymized_name,
                "Score": round(score, 4),
                "Reasoning": reasoning,
                "ID": cand.candidate_id
            })
            
        res_df = pd.DataFrame(out_rows)
        
    elapsed = time.time() - start_time
    
    st.success(f"Pipeline completed in {elapsed:.2f}s for {len(candidates)} candidates.")
    st.info("Note: The full 100K-scale offline benchmark is available in `engine/benchmark_report.txt`.")
    
    st.dataframe(res_df, use_container_width=True, height=600)
