import os
import subprocess
import sys
import pandas as pd
import pytest

def test_rank_e2e_produces_valid_submission():
    # If the real model or embeddings aren't there, we skip
    if not os.path.exists("engine/model.txt") or not os.path.exists("engine/embeddings/candidate_embeddings.npy"):
        pytest.skip("Precomputed artifacts not available for E2E test.")
        
    # We run rank.py with --limit 200
    res = subprocess.run([
        sys.executable, "engine/rank.py", 
        "--candidates", "data/candidates.jsonl",
        "--limit", "200",
        "--out", "test_submission.csv",
        "--export-ui-json", "test_ranked.json"
    ], capture_output=True, text=True)
    
    assert res.returncode == 0, f"rank.py failed: {res.stderr}"
    
    # Check that CSV was produced
    assert os.path.exists("test_submission.csv")
    
    df = pd.read_csv("test_submission.csv")
    # rank.py outputs exactly min(100, N) rows. 
    # With limit 200, we should get exactly 100 rows.
    assert len(df) == 100
    
    assert list(df.columns) == ["candidate_id", "rank", "score", "reasoning"]
    
    # Ranks 1 to 100
    assert list(df["rank"]) == list(range(1, 101))
    
    # Scores non-increasing
    scores = df["score"].values
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1]
        
    # Check that validate_submission.py passed
    assert "PASS: Submission is valid." in res.stdout
    
    # Cleanup
    if os.path.exists("test_submission.csv"):
        os.remove("test_submission.csv")
    if os.path.exists("test_ranked.json"):
        os.remove("test_ranked.json")
