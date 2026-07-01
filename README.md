# 🚀 Quantum HR Core - Enterprise-Grade AI Ranking Engine

*Developed for the **RedRob Hackathon: India Runs Data & AI Challenge***

---

## 🌟 The "Secret Sauce": Why This Engine Wins
While most ranking engines rely on generic keyword matching or basic LLM embeddings, Quantum HR Core was built ground-up with **Enterprise-Grade HR Business Logic** to specifically target the exact pain points outlined in the RedRob Job Description.

We engineered specific **Boosts** and **Penalties** to mimic a strict, senior technical recruiter screening 100K candidates:

### 🔴 The Enterprise Penalties (The "Anti-Patterns")
1. **The "Title Chaser" Penalty (Overqualified):** Disqualifies candidates claiming VP/Director titles for Senior IC roles.
2. **The "Non-Coder" Penalty (Architects out of touch):** Severely penalizes Tech Leads/Architects who haven't touched code in the last 18 months.
3. **The "Job Hopper" Penalty:** Heavily down-weights candidates who have switched 4+ jobs in the last 36 months.
4. **The "Consulting-Only" Penalty:** Deprioritizes pure service-based company backgrounds (TCS/Infosys) unless they have proven product company experience.
5. **The "Research-Only" Penalty:** Filters out pure academic/PhD backgrounds lacking production engineering experience.
6. **The "Framework Enthusiast" Penalty:** Spots candidates relying only on LangChain/LlamaIndex wrappers without core fundamentals.
7. **The "Salary Mismatch" Penalty:** Flags candidates whose expected salary heavily breaches the RedRob JD budget.
8. **The "Honeypot Trap":** Integrates anomaly detection to aggressively filter out fake profiles and fraudulent platform behavior.

### 🟢 The Enterprise Boosts (The "Superstars")
1. **Loyalty Boost (Retainability):** Applies a 1.1x boost to candidates who have demonstrated 3+ years of tenure at a single company.
2. **Recent ML Focus:** Boosts candidates whose *current* job is heavily focused on AI/ML, ensuring their skills are sharp.
3. **Fast Mover (Immediate Joiner):** Heavily boosts candidates with a Notice Period of <15 days.
4. **Open Source Top Contributor:** Leverages RedRob signals to boost candidates with verified, high-activity GitHub profiles (Score > 80).

---

## 🏗️ Architecture Overview

The solution is divided into two decoupled systems to satisfy the strict compute constraints of the ranking challenge while providing a rich recruiter experience:

### 1. `engine/` (Offline Ranking Engine)
A pure-Python offline engine that runs under the strict budget (no network, CPU-only, 16GB RAM, <5 minutes for 100K candidates).
- **LightGBM Learning-to-Rank (`LGBMRanker`):** A blazing-fast 17-feature tree-based ranker.
- **Post-Model Multipliers:** Strict heuristic business logic applied *after* the base prediction to ensure strict compliance with JD guidelines without breaking model training data.
- **Deterministic Reasoning:** Generates hallucination-free, grounded reasoning explanations for the top 100 candidates.

### 2. `app/` (React/Vite Web App)
A single-purpose **Candidate Intelligence Console**. It visualizes the output of the offline engine (`ranked_candidates.json`) in a dense, enterprise-grade dark-mode dashboard meant for recruiters.
- **Visualizes Feature Breakdowns:** See exactly why a candidate was ranked #1 or #50.
- **Instant Badges:** Hoverable UI dots highlighting "Fast Mover" or "Top Contributor".
- **Comprehensive Verification Tracking:** Visualizes GitHub activity, RedRob Skill Assessments, Response Times, and 30-day funnel metrics (Searches -> Saves -> Apps).

---

## ⚙️ Setup & Running the Engine

### Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`

### Data Setup
Ensure `candidates.jsonl` is placed in `data/candidates.jsonl`. *(Note: This file is large and explicitly excluded from git).*

### 1. Ranking Candidates (The Core Entrypoint)
To run the 5-minute ranking step over the 100K candidates:
```bash
python -m engine.rank
```
This will:
- Load the precomputed artifacts (embeddings, model).
- Score 100K candidates using vectorized operations, LightGBM, and our Custom Penalties.
- Output the top 100 to `submission.csv`.
- Run the validation script (`validate_submission.py`) on the output to guarantee format compliance.
- Export `ranked_candidates.json` for the UI Dashboard.

### 2. Running the Main Application (React UI)
Experience the enterprise-grade dashboard we built for recruiters to analyze the engine's output.
```bash
cd app
npm install
npm run dev
```
Navigate to the "Candidate Intel" tab in the local host browser to see the ranked pipeline results.

### 3. Benchmarking
To verify time and memory constraints match the Hackathon requirements:
```bash
python engine/benchmark.py
```
See `engine/benchmark_report.txt` for the results.

---

## 🛡️ Methodology Note: Weak Label Generation
Weak labels for training the LightGBM model are a deterministic function of the hand-engineered features used as model inputs. The LightGBM model's contribution here is smoothing a hard-bucketed heuristic into a continuous, interaction-aware ranking function. We deliberately chose extreme fidelity to the RedRob JD's explicit criteria (building strict heuristic penalties) over a purely 'ML-native' pipeline, as generic ML often fails to catch the keyword-stuffing and title-chasing patterns that the JD specifically warned against.
