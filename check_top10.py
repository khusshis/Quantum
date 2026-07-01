import pandas as pd
from engine.schema import load_candidates
from collections import Counter

sub = pd.read_csv("submission.csv")
candidates = load_candidates("data/candidates.jsonl")
cid_map = {c.candidate_id: c for c in candidates}

print("=== TOP 10 TITLES + REASONING ===")
for _, row in sub.head(10).iterrows():
    c = cid_map[row["candidate_id"]]
    print(f"Rank {row['rank']} | {row['candidate_id']} | Score: {row['score']}")
    print(f"  Title: {c.profile.current_title}")
    print(f"  Company: {c.profile.current_company}")
    print(f"  YOE: {c.profile.years_of_experience}")
    print(f"  Reasoning: {row['reasoning']}")
    print()

print("=== TIE/SCORE COMPRESSION CHECK (all 100 rows) ===")
scores = sub["score"].tolist()
unique_scores = len(set(scores))
print(f"Unique scores: {unique_scores} / 100")
score_counts = Counter(scores)
ties = {s: cnt for s, cnt in score_counts.items() if cnt > 1}
if ties:
    print(f"Tied scores: {ties}")
else:
    print("No ties detected.")
print(f"Score range: {min(scores)} to {max(scores)}")
print(f"Score spread: {max(scores) - min(scores):.4f}")
