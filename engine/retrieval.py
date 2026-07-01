import json
import numpy as np
from typing import Dict, List
from rank_bm25 import BM25Okapi
from engine.schema import Candidate
from engine.embed import build_candidate_text

class HybridRetriever:
    def __init__(self, candidates: List[Candidate], embeddings_path: str, ids_path: str):
        """
        Loads precomputed embeddings and builds the BM25 index in memory.
        """
        self.candidates = candidates
        
        # Load precomputed embeddings
        self.embeddings = np.load(embeddings_path)  # Shape (N, D)
        with open(ids_path, "r", encoding="utf-8") as f:
            self.emb_ids = json.load(f)
            
        # Create an id->index mapping
        self.id_to_idx = {cid: i for i, cid in enumerate(self.emb_ids)}
        
        # Build BM25 index over candidate texts
        # We re-build candidate text representations here. 
        # (Alternatively, we could have pre-saved the text strings, but it's fast enough on CPU)
        tokenized_corpus = []
        for c in self.candidates:
            text = build_candidate_text(c).lower()
            tokenized_corpus.append(text.split())
            
        self.bm25 = BM25Okapi(tokenized_corpus)

    def score_all(self, jd_text: str, precomputed_jd_emb_path: str = None, jd_embedding: np.ndarray = None) -> Dict[str, Dict[str, float]]:
        """
        Returns a dict of candidate_id -> {"dense": float, "sparse": float}
        """
        # Load JD embedding
        if jd_embedding is None:
            if precomputed_jd_emb_path:
                jd_emb = np.load(precomputed_jd_emb_path)[0] # Shape (D,)
            else:
                raise ValueError("Either jd_embedding or precomputed_jd_emb_path must be provided.")
        else:
            jd_emb = jd_embedding
            
        # Dense Cosine Similarity
        # Normalize both vectors to compute cosine sim via dot product
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1e-9
        normalized_embeddings = self.embeddings / norms
        
        jd_norm = np.linalg.norm(jd_emb)
        if jd_norm > 0:
            jd_emb = jd_emb / jd_norm
            
        dense_scores = np.dot(normalized_embeddings, jd_emb)
        
        # Sparse BM25
        tokenized_query = jd_text.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores to roughly 0-1 range for easier usage, or leave raw.
        # We will max-normalize it
        max_bm25 = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1.0
        sparse_scores = bm25_scores / max_bm25
        
        results = {}
        for i, c in enumerate(self.candidates):
            cid = c.candidate_id
            
            # Lookup dense score using id mapping (in case N is different, which shouldn't happen)
            idx = self.id_to_idx.get(cid)
            dense = float(dense_scores[idx]) if idx is not None else 0.0
            sparse = float(sparse_scores[i])
            
            results[cid] = {
                "dense": dense,
                "sparse": sparse
            }
            
        return results
