import json
import pandas as pd
from engine.schema import load_candidates
from engine.rank import run_pipeline

candidates = load_candidates('data/candidates.jsonl')
json_export, csv_rows = run_pipeline(candidates, shortlist_size=120)

df = pd.DataFrame(json_export)
print('=== CANDIDATES 91-100 (JUST INSIDE) ===')
for i in range(90, 100):
    c = df.iloc[i]
    print(f"{c['rank']} | {c['candidate_id']} | Score: {c['score']:.4f} | YOE: {c['yoe']} | Rel: {c['features']['role_relevance_score']:.2f} | ML Ev: {c['features']['production_ml_evidence_score']:.2f} | Title: {c['title']}")
print('\n=== CANDIDATES 101-110 (JUST OUTSIDE) ===')
for i in range(100, 110):
    c = df.iloc[i]
    print(f"{c['rank']} | {c['candidate_id']} | Score: {c['score']:.4f} | YOE: {c['yoe']} | Rel: {c['features']['role_relevance_score']:.2f} | ML Ev: {c['features']['production_ml_evidence_score']:.2f} | Title: {c['title']}")
