import os
import json
import time
import numpy as np
import pytest
from engine.schema import Candidate, CandidateProfile, RedrobSignals, ExpectedSalaryRange
from engine.retrieval import HybridRetriever

def test_retrieval_benchmark(tmp_path):
    # Create 1000 synthetic candidates to test performance and functionality
    # We won't test 100K in CI because it might be too slow to setup the mock data, 
    # but we can extrapolate or just test 10K. Let's do 10K.
    N = 10000
    candidates = []
    for i in range(N):
        c = Candidate(
            candidate_id=f"CAND_{1000000+i}",
            profile=CandidateProfile(
                anonymized_name=f"Test {i}",
                headline="AI Engineer",
                summary="Built some models.",
                location="Pune",
                country="India",
                years_of_experience=5.0,
                current_title="AI Engineer",
                current_company="Corp",
                current_company_size="1-10",
                current_industry="Tech"
            ),
            career_history=[],
            education=[],
            skills=[],
            redrob_signals=RedrobSignals(
                profile_completeness_score=100.0,
                signup_date="2020-01-01",
                last_active_date="2024-05-01",
                open_to_work_flag=True,
                profile_views_received_30d=10,
                applications_submitted_30d=1,
                recruiter_response_rate=0.8,
                avg_response_time_hours=24.0,
                skill_assessment_scores={},
                connection_count=100,
                endorsements_received=10,
                notice_period_days=30,
                expected_salary_range_inr_lpa=ExpectedSalaryRange(10, 20),
                preferred_work_mode="hybrid",
                willing_to_relocate=True,
                github_activity_score=50,
                search_appearance_30d=5,
                saved_by_recruiters_30d=2,
                interview_completion_rate=0.9,
                offer_acceptance_rate=0.5,
                verified_email=True,
                verified_phone=True,
                linkedin_connected=True
            )
        )
        candidates.append(c)
        
    # Mock embeddings
    embeddings = np.random.randn(N, 384).astype(np.float32)
    ids = [c.candidate_id for c in candidates]
    
    emb_path = tmp_path / "candidate_embeddings.npy"
    ids_path = tmp_path / "candidate_ids.json"
    
    np.save(str(emb_path), embeddings)
    with open(ids_path, "w") as f:
        json.dump(ids, f)
        
    start_time = time.time()
    retriever = HybridRetriever(candidates, str(emb_path), str(ids_path))
    build_time = time.time() - start_time
    
    jd_text = "Looking for an AI Engineer with experience in Python and machine learning."
    jd_embedding = np.random.randn(384).astype(np.float32)
    
    start_time = time.time()
    scores = retriever.score_all(jd_text, jd_embedding=jd_embedding)
    score_time = time.time() - start_time
    
    print(f"Build time (BM25 for {N}): {build_time:.2f}s")
    print(f"Scoring time (Dense+Sparse for {N}): {score_time:.2f}s")
    
    assert len(scores) == N
    # Asserting that 100K would comfortably fit in 60 seconds (10K taking < 6s)
    assert build_time + score_time < 6.0
    
    assert "dense" in scores[ids[0]]
    assert "sparse" in scores[ids[0]]
