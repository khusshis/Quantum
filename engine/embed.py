"""
embed.py: ONE-TIME OFFLINE precomputation script.
This script is EXPLICITLY NOT RUN during the 5-minute ranking step. 
It precomputes the dense embeddings for all candidates and the JD using the small CPU-friendly 
`sentence-transformers/all-MiniLM-L6-v2` model.

Run this once: `python engine/embed.py`
Artifacts are saved to `engine/embeddings/`.
"""

import os
import json
import numpy as np
import argparse
from typing import List
from sentence_transformers import SentenceTransformer
from engine.schema import load_candidates, Candidate
from engine.jd_parser import JD

def build_candidate_text(candidate: Candidate) -> str:
    parts = []
    if candidate.profile.headline:
        parts.append(candidate.profile.headline)
    if candidate.profile.summary:
        parts.append(candidate.profile.summary)
        
    # Get top 5 skills by simple heuristic: Expert/Advanced first, then duration
    prof_map = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
    sorted_skills = sorted(candidate.skills, 
                           key=lambda x: (prof_map.get(x.proficiency.lower(), 0), x.duration_months or 0), 
                           reverse=True)
    top_skills = [s.name for s in sorted_skills[:5]]
    if top_skills:
        parts.append("Skills: " + ", ".join(top_skills))
        
    # Recent 2 career descriptions
    sorted_roles = sorted(candidate.career_history, key=lambda x: x.start_date, reverse=True)
    for role in sorted_roles[:2]:
        if role.description:
            # truncate sensible
            desc = role.description[:200]
            parts.append(f"{role.title}: {desc}")
            
    return " | ".join(parts)[:1000] # Truncate to avoid blowing up token count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=str, default="data/candidates.jsonl")
    parser.add_argument("--out_dir", type=str, default="engine/embeddings")
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    
    print("Building text representations...")
    texts = [build_candidate_text(c) for c in candidates]
    candidate_ids = [c.candidate_id for c in candidates]
    
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    # Using all-MiniLM-L6-v2 which is ~80MB and fast on CPU
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Encoding candidates (this may take a few minutes for 100K candidates)...")
    embeddings = model.encode(texts, batch_size=256, show_progress_bar=True, convert_to_numpy=True)
    
    emb_path = os.path.join(args.out_dir, "candidate_embeddings.npy")
    np.save(emb_path, embeddings.astype(np.float32))
    
    ids_path = os.path.join(args.out_dir, "candidate_ids.json")
    with open(ids_path, "w", encoding="utf-8") as f:
        json.dump(candidate_ids, f)
        
    print(f"Saved {len(candidate_ids)} candidate embeddings to {emb_path}")
    
    # Embed JD narrative text
    print("Encoding JD text...")
    jd_text = JD.ideal_profile_narrative
    jd_embedding = model.encode([jd_text], convert_to_numpy=True)
    
    jd_emb_path = os.path.join(args.out_dir, "jd_embedding.npy")
    np.save(jd_emb_path, jd_embedding.astype(np.float32))
    print(f"Saved JD embedding to {jd_emb_path}")
    
    print("Done!")

if __name__ == "__main__":
    main()
