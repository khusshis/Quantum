# Quantum HR Core - AI Ranking Engine

This repository contains the solution for the "RedRob Hackathon: India Runs Data & AI Challenge" developed by Antigravity Engineers.

## Architecture

The solution is divided into two decoupled systems to satisfy the strict compute constraints of the ranking challenge while providing a rich recruiter experience:

1. **`engine/` (Offline Ranking Engine)**
   A pure-Python offline engine that runs under the strict budget (no network, CPU-only, 16GB RAM, <5 minutes for 100K candidates).
   - Uses LightGBM Learning-to-Rank (`LGBMRanker`).
   - Uses precomputed dense embeddings (`all-MiniLM-L6-v2`) and BM25 sparse retrieval.
   - Computes robust, rule-based features for career fit, skills, and behavior.
   - Generates deterministic, hallucination-free grounded reasoning using templates.
   - Integrates a honeypot/anomaly detector.

2. **`app/` (React/Vite Web App)**
   A single-purpose Candidate Intelligence Console. It visualizes the output of the offline engine (`ranked_candidates.json`) in a dense, enterprise-grade dashboard meant for recruiters to analyze feature scores, compliance constraints, and contrast top candidates with runners-up.

### Methodology Note: Weak Label Generation
Weak labels are a deterministic function of the same hand-engineered features used as model inputs. This is a documented limitation, not an oversight — the LightGBM model's contribution here is smoothing a hard-bucketed heuristic into a continuous, interaction-aware ranking function, and provides an extension point for real feedback data (recruiter clicks, hire outcomes) if this were deployed. We chose fidelity to the JD's explicit criteria over a more 'ML-native' pipeline that would have been weaker at catching keyword-stuffing and title-chasing patterns the JD specifically warns about.

## Setup & Running the Engine

### Prerequisites
- Python 3.10+
- `pip install -r engine/requirements.txt`

### Data Setup
Ensure `candidates.jsonl` is placed in `data/candidates.jsonl`.
(Note: This file is large and explicitly excluded from git).

### 1. Offline Precomputation (One-Time)
Before ranking, you must generate the candidate embeddings.
```bash
python engine/embed.py
```
This saves artifacts to `engine/embeddings/`. (For the final submission, these are precomputed and committed).

### 2. Model Training (One-Time)
```bash
python engine/train_ranker.py
```
This trains the LightGBM model and saves it to `engine/model.txt` and outputs a feature importance chart.

### 3. Ranking Candidates (The Core Entrypoint)
To run the 5-minute ranking step over the 100K candidates:
```bash
python engine/rank.py --candidates data/candidates.jsonl --out submission.csv
```
This will:
- Load the artifacts (embeddings, model).
- Score 100K candidates using vectorized operations and LightGBM.
- Output the top 100 to `submission.csv`.
- Run the validation script (`data/validate_submission.py`) on the output.
- Export `ranked_candidates.json` for the UI.

### 4. Benchmarking
To verify time and memory constraints:
```bash
python engine/benchmark.py
```
See `engine/benchmark_report.txt` for the results.

### 5. Running the Sandbox (Interactive UI)
```bash
pip install -r sandbox/requirements.txt
streamlit run sandbox/streamlit_app.py
```

### 6. Running the Main Application (React UI)
```bash
cd app
npm install
npm run dev
```
Navigate to the "Candidate Intel" tab to see the ranked pipeline results.

## Testing
Run the engine unit tests with pytest:
```bash
python -m pytest engine/tests/
```
