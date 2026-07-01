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
1. **Fast Mover (Immediate Joiner):** Heavily boosts candidates with a Notice Period of <15 days.
2. **Open Source Top Contributor:** Leverages RedRob signals to boost candidates with verified, high-activity GitHub profiles (Score > 80).

---

## 🏗️ Architecture Overview

The solution provides both a blazing-fast CLI for evaluation and a dynamic API-powered UI for real recruiters:

### 1. `engine/` (Offline Ranking Engine)
A pure-Python engine optimized for strict compute constraints (CPU-only, <5 minutes for 100K candidates).
- **LightGBM Learning-to-Rank (`LGBMRanker`):** A blazing-fast 17-feature tree-based ranker.
- **Post-Model Multipliers:** Strict heuristic business logic applied *after* the base prediction.
- **Dynamic Retrieval Fallback:** If a custom JD is passed, it intelligently decouples from the ML bias and relies purely on Semantic/BM25 retrieval + quality multipliers.

### 2. `api.py` (Flask API Server)
A lightweight HTTP wrapper around the engine that allows real-time execution of the AI pipeline on custom JSON files with custom Job Descriptions.

### 3. `app/` (React/Vite Web App)
A single-purpose **Candidate Intelligence Console** featuring an enterprise-grade dark-mode dashboard.
- **Visualizes Feature Breakdowns:** See exactly why a candidate was ranked #1 or #50 via SHAP-driven reasoning.
- **Live Configuration:** Upload a raw candidates JSON file, set a shortlist size, provide a Custom JD, and watch it rank candidates on the fly!

---

## ⚙️ Step-by-Step Execution Guide

### Prerequisites
- Node.js (v18+)
- Python 3.10+

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
pip install flask flask-cors
```

### Step 2: Data Setup
Ensure your 100,000 row dataset `candidates.jsonl` is placed inside the `data/` folder:
`data/candidates.jsonl`
*(Note: This file is large and explicitly excluded from git).*

### Step 3: Start the Backend (API Server)
Open a terminal and start the Flask server. This server handles dynamic ranking requests when you upload a custom file in the UI.
```bash
python api.py
```
*(Runs on port 5000)*

### Step 4: Start the Frontend (Candidate Console)
Open a **new, separate terminal** and start the React application:
```bash
cd app
npm install
npm run dev
```
*(Runs on port 3000)*

### Step 5: Using the UI
1. Navigate to `http://localhost:3000`.
2. By default, it will load the pre-computed `ranked_candidates.json` for the original ML Engineer JD.
3. **To test the dynamic pipeline:** Click **"IMPORT JSON"** in the top right.
4. Select `data/candidates.jsonl` (or any raw schema file).
5. A sleek configuration modal will appear. Enter a custom shortlist size and a **Custom JD** (e.g., "Project Manager").
6. Click **Run AI Pipeline**. The UI will send the file to the Flask backend, execute the pipeline on the fly, and render the new results in a new tab!

---

## 📊 Offline Evaluation & Benchmarking

If you just want to run the core engine from the command line for scoring and benchmarking (without the UI):

**Generate Submission (CLI):**
```bash
python -m engine.rank
```
*Outputs the top 100 to `submission.csv` and validates it.*

**Run Benchmark:**
```bash
python engine/benchmark.py
```
*Checks memory usage and execution time.*
