import os
import sys
import pandas as pd
from engine.schema import load_candidates
from engine.honeypot import is_honeypot

def main():
    sub = pd.read_csv("submission.csv")
    top_ids = set(sub['candidate_id'].tolist())
    
    candidates = load_candidates("data/candidates.jsonl")
    top_cands = [c for c in candidates if c.candidate_id in top_ids]
    
    threshold = 0.6
    above_threshold = 0
    
    print("=== TOP 100 HONEYPOT AUDIT ===")
    for c in top_cands:
        score, _, reasons = is_honeypot(c)
        print(f"[{c.candidate_id}] Score: {score:.2f} | Reasons: {reasons}")
        if score > threshold:
            above_threshold += 1
            
    print(f"\nTotal exceeding 0.6 threshold: {above_threshold} / 100")
    
if __name__ == "__main__":
    main()
