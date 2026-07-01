# Quantum → Redrob Ranking Engine: Antigravity + Stitch Prompt Playbook

## 0. Read this first — the strategic diagnosis

Your current `Quantum-main` repo is a polished "AI Career CoPilot" that calls Groq (Llama 3.3 70B) live from the browser for resume analysis. That's a legitimate product demo, but it **cannot be the code path that produces your `submission.csv`**, because `submission_spec.docx` bans, during the ranking step:

- Hosted LLM API calls (OpenAI, Anthropic, Cohere, Gemini, Groq — all of them)
- GPUs
- Network access
- >5 minutes wall-clock, >16GB RAM, >5GB disk, for the full ~100K-candidate pool

So the winning shape of this project is **two decoupled systems sharing one data contract**:

1. **The Ranking Engine** (`/engine`) — pure Python, CPU-only, offline. Takes `candidates.jsonl` + `job_description`, outputs `submission.csv` in Stage 3's sandbox. This is what gets scored and reproduced. No API keys, no network calls, deterministic.
2. **The Recruiter Console** (`/app`, your existing React/Vite/Quantum codebase) — the enterprise UI. It reads the engine's *precomputed* output (scores + feature breakdowns + reasoning) and renders it beautifully. It can still use Groq/Gemini for the *candidate-facing* career-copilot features (interview sim, course ROI, chat) since those aren't part of the scored ranking pipeline — just don't let any of that touch the ranking decision.

This split is also your strongest talking point at Stage 5 (the "defend your work" interview): you can explain exactly why you separated them, which is precisely the "genuine engineering vs. paste-and-pray" signal the organizers say they're filtering for.

### The unique angle worth building (nobody else will do this well)

The JD is unusually explicit about what it does **not** want: title-chasers, "framework enthusiast" GitHub tourists, pure-consulting-only backgrounds, CV/speech/robotics-only people, research-only people, stale architects who stopped coding. A naive cosine-similarity-on-embeddings system will miss all of this — that's the trap the JD literally says it built into the dataset. Your differentiator:

- **Encode the JD's negative space as explicit, named scoring components** (not just a single opaque embedding score) — e.g. `title_trajectory_score`, `keyword_stuffing_penalty`, `consulting_only_flag`, `research_only_disqualifier`, `staleness_penalty` (senior title but no recent hands-on evidence), `domain_adjacency_penalty` (CV/speech/robotics without NLP/IR).
- **Weak-supervision, not hand-tuning**: since there's no ground truth, generate heuristic pseudo-labels straight from the JD's stated rules, then train a small LightGBM LambdaMART ranker on top of hand-engineered + embedding features. This generalizes better than pure rules and is a legitimate, explainable ML technique you can defend in the interview.
- **A standalone honeypot/anomaly detector** as its own auditable module (internal consistency checks: tenure math, skill-duration-vs-proficiency mismatches, experience-years vs. career-history sum mismatches), reported separately in your methodology so reviewers can see you treated it as a first-class problem, not an afterthought.
- **Fully grounded, template-driven reasoning generation** — no LLM needed at all, which conveniently also means it can run inside the compute-constrained ranking step if you want reasoning baked into `rank.py` itself. Every reasoning string is built from actual extracted fields (years, current title, named skills that matched, signal values, explicit gap callouts) — this directly satisfies every one of the six Stage 4 reasoning checks (specificity, JD connection, honest concerns, no hallucination, variation, rank-consistency) by construction, since it's assembled from real data rather than generated freeform.
- **The Recruiter Console visualizes all of this**: per-candidate score breakdown radar/bar, honeypot flags, "why not the next 5 candidates" contrastive view, a compliance/audit export, and a live "compute budget" badge showing your engine's actual measured runtime — enterprise reviewers *love* seeing operational self-awareness like that.

### Target repo structure

```
redrob-ranker/
├── engine/
│   ├── rank.py                  # single entrypoint: python rank.py --candidates ... --jd ... --out submission.csv
│   ├── features.py              # feature engineering (profile, career, signals)
│   ├── honeypot.py              # anomaly / honeypot detector
│   ├── retrieval.py             # BM25/TF-IDF + local embedding hybrid retrieval
│   ├── embeddings/               # precomputed embedding artifacts (or script to build them)
│   ├── weak_labels.py           # heuristic pseudo-label generator for training
│   ├── train_ranker.py          # trains LightGBM LTR model offline, saves model.txt
│   ├── model.txt                # trained model artifact (checked in)
│   ├── reasoning.py             # grounded template-based reasoning generator
│   ├── benchmark.py             # measures runtime/memory against the 5min/16GB budget
│   └── tests/
├── app/                          # your existing Quantum React app, retargeted as Recruiter Console
├── sandbox/                      # tiny Streamlit app for the required hosted demo link
├── submission_metadata.yaml
├── requirements.txt
├── README.md
└── submission.csv
```

Now here are the prompts. Paste each into Antigravity as its own task, in order — each one assumes the previous ones' files exist. Adjust file paths if Antigravity places things differently.

---

## PROMPT 1 — Repo bootstrap & data contract

```
Create a new top-level directory `engine/` in this repo for a compute-constrained candidate ranking
pipeline, separate from the existing React app (which will move to `app/` unchanged for now — just
create the folder and don't touch its contents yet).

Requirements for everything you build in `engine/`:
- Pure Python 3.11, stdlib + numpy/pandas/scikit-learn/lightgbm/rank-bm25/sentence-transformers only.
- NO calls to any hosted API (no requests to openai/anthropic/groq/google endpoints) anywhere in engine/.
- Must run fully offline after a one-time setup step that downloads a small local embedding model
  (e.g. sentence-transformers/all-MiniLM-L6-v2, ~80MB, CPU-only) — this download happens in a separate
  `engine/setup.py` / README step, NOT during the ranking step itself.
- All randomness must be seeded for reproducibility.

Build `engine/schema.py` defining typed dataclasses (or pydantic models) mirroring
candidate_schema.json exactly: CandidateProfile, CareerHistoryEntry, Education, Skill, Certification,
Language, RedrobSignals, Candidate (the top-level object). Include a `load_candidates(path: str) ->
list[Candidate]` function that streams candidates.jsonl line by line (don't load the whole 100K-row
file into memory as raw JSON twice — parse once into the dataclasses) and validates against the schema,
collecting and logging (not crashing on) any malformed rows.

Also build `engine/jd_parser.py` with a `ParsedJD` dataclass that manually encodes the structured
requirements extracted from job_description.docx as explicit fields (I'll paste the JD text below) —
NOT via an LLM call, just as a hardcoded structured config, since the JD is fixed for this challenge:
- required_years_range: (5, 9), soft — flag as a modifier not a hard filter
- required_skills_categories: embeddings/retrieval production experience, vector DB / hybrid search
  production experience, strong Python, ranking evaluation experience (NDCG/MRR/MAP/A-B testing)
- nice_to_have: LLM fine-tuning (LoRA/QLoRA/PEFT), learning-to-rank models, HR-tech background,
  distributed systems, open-source contributions
- hard_disqualifiers: pure-research-only career (no production deployment ever), title suggests
  "architect"/"tech lead"/"manager" for 18+ months with no coding evidence in recent role descriptions
- soft_penalties: title-chasing pattern (3+ jobs each <=18 months with escalating seniority titles),
  "framework enthusiast" pattern (skills list dominated by trendy frameworks with low endorsement/
  duration and generic descriptions), consulting-only career (TCS/Infosys/Wipro/Accenture/Cognizant/
  Capgemini as EVERY employer, no product company ever) unless currently at one of those WITH prior
  product-company experience, CV/speech/robotics-primary background without NLP/IR exposure,
  closed-source-only 5+ years with zero external validation signals
- location_preference: Pune, Noida, Hyderabad, Mumbai, Delhi NCR (soft boost, not a filter — JD says
  "candidates welcome to apply" from these, doesn't exclude others)
- notice_period_preference: <=30 days ideal, 30+ acceptable but higher bar
- ideal_profile_narrative: 6-8 years, 4-5 in applied ML/AI at product companies, has shipped an
  end-to-end ranking/search/recommendation system to real users at scale

[paste the full job_description.docx text here]

Write engine/tests/test_schema.py with at least 5 unit tests covering: valid candidate parses correctly,
missing required field raises a clear error (not a crash), malformed jsonl line is skipped and logged,
years_of_experience out of range is flagged, redrob_signals with -1 sentinel values (github_activity_score,
offer_acceptance_rate) are handled as "no signal" not as literal negative scores downstream.

Set up requirements.txt pinning exact versions of: pandas, numpy, scikit-learn, lightgbm, rank-bm25,
sentence-transformers, pyyaml, pytest. Set up a Makefile or engine/setup.sh with a one-time
`download-embedding-model` step.
```

---

## PROMPT 2 — Feature engineering

```
Build `engine/features.py`. Given a `Candidate` (from schema.py) and the `ParsedJD` (from jd_parser.py),
compute a `CandidateFeatures` dataclass / dict with these named, independently-inspectable components
(each should be a float, most normalized to roughly [0,1] so they're comparable and can be visualized
individually later in a UI):

CAREER-FIT FEATURES
- years_experience_fit: triangular/gaussian score peaking in the 5-9y band, gently decaying outside it
  (not a hard cutoff — JD explicitly says this is a range not a requirement)
- title_trajectory_score: analyze career_history titles chronologically; reward evidence of hands-on
  IC seniority growth in applied ML/AI/search/ranking roles; penalize a title-chasing pattern (see
  jd_parser thresholds); penalize "architect/lead/manager" titles held 18+ months with no recent
  hands-on-coding language in description text
- production_ml_evidence_score: scan career_history[].description text (rule-based keyword/phrase
  matching against a curated list, NOT semantic — keep this cheap and auditable) for evidence of
  PRODUCTION deployment language ("deployed", "production", "served X requests", "in prod",
  "real users", "scaled to") co-occurring with retrieval/ranking/embeddings/search vocabulary, as
  distinct from purely academic/tutorial language
- domain_adjacency_penalty: 1.0 if no CV/speech/robotics-primary signal, tapering down if current_title
  or majority of career_history is computer-vision/speech/robotics AND there's no NLP/IR keyword
  co-occurrence anywhere
- consulting_only_penalty: 1.0 normally; reduced sharply if 100% of career_history employers are in a
  hardcoded consulting-firm list AND none show product-company patterns; restored to ~1.0 if candidate
  is CURRENTLY at a consulting firm but has ANY prior product-company employer (per JD's explicit carve-out)
- research_only_disqualifier: near-0 multiplier if ALL career_history entries are academic/research-lab
  with zero production-deployment language detected anywhere

SKILLS FEATURES
- skill_semantic_match: cosine similarity between a JD requirement-text embedding and an embedding of
  the candidate's concatenated skills+headline+summary (using the precomputed local embedding model —
  do NOT compute embeddings inside this function per-call; accept a precomputed vector as an argument)
- skill_trust_score: for each skill matching JD-relevant categories, weight by
  log1p(endorsements) * log1p(duration_months) * proficiency_weight, NOT just presence/absence —
  this is your anti-keyword-stuffing mechanism (a skill listed with 0 duration_months and "expert"
  proficiency should contribute ~nothing)
- framework_enthusiast_penalty: flag if skills are dominated by trendy-framework names with near-zero
  average duration_months/endorsements AND career_history descriptions read as tutorial/demo-language
  rather than production language

EDUCATION FEATURES
- education_tier_score: map education[].tier (tier_1..tier_4/unknown) to a modest, capped bonus —
  keep this a SMALL contribution; the JD never emphasizes pedigree

BEHAVIORAL / AVAILABILITY FEATURES (from redrob_signals — this is the "is this candidate actually
gettable" layer per redrob_signals_doc.docx)
- availability_score: composite of recency (days since last_active_date, decayed), open_to_work_flag,
  recruiter_response_rate, interview_completion_rate — this should behave as a MULTIPLIER on the final
  score, not an additive term, per the JD's explicit "down-weight them appropriately" instruction for
  a perfect-on-paper but inactive candidate
- notice_period_fit: piecewise score, high for <=30 days, gently declining after, per JD
- salary_alignment_flag: informational only for now (no target comp given in this run) — compute but
  don't weight heavily
- verification_trust_score: small bonus for verified_email/verified_phone/linkedin_connected —
  legitimacy signal, keep it minor
- location_boost: modest boost if location/willing_to_relocate aligns with Pune/Noida/Hyderabad/
  Mumbai/Delhi NCR, per JD's explicit welcome list — must NOT be an exclusionary filter

Every one of these functions must be pure, unit-testable, and take already-parsed data (no I/O, no
model loading inside them). Write engine/tests/test_features.py with hand-constructed synthetic
candidates that each isolate ONE feature (e.g. a candidate who is 100% TCS/Infosys/Wipro their whole
career with no product-company stint → assert consulting_only_penalty is low; the same candidate but
with one prior product-company job → assert it's restored).
```

---

## PROMPT 3 — Honeypot / anomaly detector

```
Build `engine/honeypot.py` as a standalone, clearly-named module (this needs to be easy for a reviewer
to find and read in isolation — Stage 3 explicitly checks honeypot rate in your top 100).

Implement `is_honeypot(candidate: Candidate) -> tuple[bool, list[str]]` returning whether the profile
looks internally inconsistent, plus a list of human-readable reasons (for your own debugging/methodology
writeup, not for the submission CSV). Rule-based checks, no ML:

1. Tenure-sum mismatch: sum(career_history[].duration_months) implies total experience wildly
   inconsistent with profile.years_of_experience (e.g. off by more than ~30%, accounting for gaps).
2. Skill-duration impossibility: any skill with proficiency == "expert" AND duration_months == 0 (or
   duration_months missing/zero while endorsements are implausibly high, e.g. >100).
3. Overlapping-impossible-tenure: career_history entries whose date ranges overlap by more than a
   plausible amount (people don't usually hold two full-time non-current roles simultaneously for
   long stretches) — flag but weight lightly since some overlap is legitimate (contracting, etc).
4. Skill-count vs seniority implausibility: 10+ skills all at "expert" proficiency combined with total
   years_of_experience under ~2 years.
5. Signal implausibility: profile_completeness_score is high (>90) but core narrative fields (summary,
   headline) are near-empty or generated-looking (very short, <15 words) — a completeness/content
   mismatch.
6. Education date impossibility: end_year before start_year, or end_year in the future beyond a
   reasonable current-year assumption, or field_of_study/degree combos that don't parse as real values
   (empty strings where required).

Return a composite `honeypot_suspicion_score` (0-1, weighted combination of the above, not just a hard
boolean) so this can be used as a strong DOWNWEIGHT multiplier in the final ranking rather than a brittle
hard exclude (the brief says "we expect a good ranking system to naturally avoid them; you don't need to
special-case them" — so build this as a natural, explainable low-relevance signal, not a lookup table).

Write engine/tests/test_honeypot.py with synthetic examples matching the brief's own stated honeypot
patterns ("8 years experience... 'expert' proficiency in 10 skills with 0 years used") and confirm they
score high suspicion, while normal varied profiles score near 0.

Also write a small `engine/audit_honeypots.py` CLI script that runs this over the full candidates.jsonl
and prints a distribution summary (how many candidates flagged at various thresholds) — this becomes
evidence for your methodology write-up, not part of the scored pipeline.
```

---

## PROMPT 4 — Hybrid retrieval + local embeddings (precomputed, offline)

```
Build `engine/embed.py` as a ONE-TIME OFFLINE precomputation script (explicitly not run during the
5-minute ranking step — document this clearly in comments and the README). It should:
- Load sentence-transformers/all-MiniLM-L6-v2 (or similar small CPU-friendly model) locally.
- For every candidate, build a compact text representation: headline + summary + top skills by
  trust_score + most recent 2 career_history descriptions (truncate sensibly, don't blow up token count).
- Batch-encode all 100K candidates on CPU (use batching + show progress; expect this step to take
  several minutes to tens of minutes — that's fine, it's offline precomputation).
- Save the resulting float32 matrix to `engine/embeddings/candidate_embeddings.npy` plus a parallel
  `candidate_ids.json` index, and commit these artifacts to the repo (or provide a documented script
  to regenerate them — either is acceptable per the spec's "pre-computed artifacts" allowance).
- Also embed the JD's narrative text (the "how to read between the lines" ideal-candidate paragraph)
  once and save `engine/embeddings/jd_embedding.npy`.

Build `engine/retrieval.py` with a `HybridRetriever` class that, GIVEN the precomputed embeddings
(loaded from disk, no model inference at ranking time — just a dot product against the cached JD vector,
which is cheap enough to run for 100K candidates in well under a second with numpy):
- Computes dense cosine similarity (skill_semantic_match feature input) via vectorized numpy matrix ops.
- Also builds a BM25 index (rank_bm25) over the same candidate text representations for a sparse/lexical
  signal — this is cheap to build at ranking time (BM25 index construction over 100K short documents
  is fast, well within budget) OR can also be precomputed if you find it's not fast enough; benchmark
  both and document your choice.
- Exposes `score_all(jd_text) -> dict[candidate_id, dict]` returning both dense and sparse component
  scores per candidate, ready to feed into features.py / the final ranker.

Write a benchmark assertion in engine/tests/test_retrieval.py that loading the precomputed embeddings
and scoring all 100K candidates completes in well under 60 seconds on CPU (leaving budget for the rest
of the pipeline within the 5-minute total).
```

---

## PROMPT 5 — Weak supervision + LightGBM learning-to-rank model

```
Since there's no ground-truth relevance data, build a defensible weak-supervision training pipeline —
this is something you should be ready to explain clearly at the Stage 5 interview.

Build `engine/weak_labels.py`: a `generate_weak_label(candidate, features, honeypot_score) -> float`
function that produces a 0-4 pseudo-relevance label PURELY from the hand-engineered features.py
components and honeypot.py score — essentially your best rule-based judgment of the JD's stated criteria,
combined into a single ordinal label. Document explicitly in the module docstring that this is a
heuristic label generator used ONLY to create training signal for a model that will hopefully generalize
smoother and better than the raw rules alone — not a claim of ground truth. Force honeypot-flagged
candidates (suspicion_score above a documented threshold) to label 0, mirroring how the brief says real
honeypots are treated in the hidden ground truth.

Build `engine/train_ranker.py`:
- Loads all 100K candidates, computes features.py + honeypot.py + retrieval.py scores for each,
  generates weak labels, and trains a LightGBM LGBMRanker (lambdarank objective) using candidate_id as
  a single query group (since this is one JD, treat it as one ranking group — document this choice and
  the alternative you considered, e.g. k-fold grouping, in a comment).
- Uses the individual named features (title_trajectory_score, production_ml_evidence_score,
  skill_trust_score, availability_score, etc. — NOT just the raw dense/sparse embedding scores) as
  model inputs, so feature importances are interpretable afterward.
- Does a train/validation split, reports NDCG@10 on held-out weak labels (acknowledging this validates
  "did the model learn the heuristic," not "did it match hidden ground truth" — be explicit about this
  limitation in a printed summary and in the README).
- Prints and saves a feature-importance chart (matplotlib, saved as a static PNG the README can embed)
  so you can screenshot it for your submission write-up.
- Saves the trained model as `engine/model.txt` (LightGBM's native text format — small, loads fast,
  no GPU needed for inference) and commits it to the repo.
- This whole training script is run ONCE, offline, NOT during the 5-minute ranking step — document
  that clearly.

Write engine/tests/test_train_ranker.py verifying the saved model file loads correctly and produces
finite, differentiated scores for a small synthetic batch of candidates (not all identical — this
directly guards against the "all scores set to the same value" common rejection reason in the spec).
```

---

## PROMPT 6 — Grounded reasoning generator (no LLM)

```
Build `engine/reasoning.py` with `generate_reasoning(candidate, features, jd, rank) -> str`.

This must produce a 1-2 sentence, specific, honest justification string built ENTIRELY from a template
system that pulls real values out of the candidate object and computed features — no LLM call, no
free-generation, so it is impossible for it to hallucinate. Design it to satisfy every one of the six
Stage 4 checks by construction:

- SPECIFIC FACTS: always cite the actual years_of_experience, current_title, and 1-2 actual matched
  skill names (pulled from the candidate's real skills list, not a generic phrase).
- JD CONNECTION: reference which specific JD requirement category drove the score (e.g. "production
  embeddings/retrieval experience", "vector DB operational experience", "ranking evaluation background")
  rather than generic praise like "great fit."
- HONEST CONCERNS: if notice_period_days > 30, or availability_score is low, or a soft_penalty fired
  (e.g. consulting_only_penalty, framework_enthusiast_penalty, domain_adjacency_penalty), the sentence
  MUST mention it explicitly (e.g. "...though notice period is 90 days, above the JD's stated
  preference" or "...though recent activity is low (last active 140 days ago)").
- NO HALLUCINATION: build the sentence via string templates filled from real dict lookups only — add
  an assertion/test that every skill name or employer name appearing in generated reasoning text
  actually exists verbatim in that candidate's profile.
- VARIATION: use a bank of 6-8 phrasing templates selected by a deterministic hash of candidate_id
  (not random per-run, so results are reproducible) so consecutive rows don't read identically, and
  interpolate different real facts each time so even same-template rows differ in substance.
- RANK CONSISTENCY: tone must scale with the row's rank/score bucket — top ~10 rows read confidently
  positive framed around 1-2 real strengths, middle rows read balanced/mixed (strength + concern),
  bottom rows explicitly foreground the concern before any positive (e.g. "Adjacent skills only —
  primarily [domain]; included as lower-confidence filler given [one real positive]").

Write engine/tests/test_reasoning.py that generates reasoning for ~50 synthetic candidates across the
full rank/score range and asserts: no two are byte-identical, every quoted skill/employer name is
verifiably present in the source candidate object (regex-extract quoted terms and check membership),
and low-rank rows contain a concern-indicating substring while top-rank rows don't fabricate concerns
that aren't in the data.
```

---

## PROMPT 7 — rank.py entrypoint, validator integration, benchmarking

```
Build `engine/rank.py` as the single CLI entrypoint required by the submission spec:

    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

It must, within the 5-minute/16GB/CPU-only/no-network budget:
1. Load candidates.jsonl (schema.py).
2. Load precomputed embeddings + JD embedding (embed.py artifacts) and the trained model.txt
   (train_ranker.py artifact) — NO training and NO embedding-model inference happens here, only
   loading precomputed artifacts and doing cheap vector math / model.predict on features.
3. Compute features.py + honeypot.py + retrieval.py scores for all candidates.
4. Score every candidate with the loaded LightGBM model, apply the availability multiplier and
   honeypot-suspicion downweight as final adjustments on top of the model score.
5. Select the top 100 by final score.
6. Break ties deterministically by candidate_id ascending (per spec section 3).
7. Generate reasoning.py strings for exactly those 100.
8. Write submission.csv with EXACTLY the columns `candidate_id,rank,score,reasoning`, UTF-8, ranks
   1-100 each used once, scores non-increasing by rank.
9. At the very end, call the provided validate_submission.py logic (import it directly, don't shell
   out) against the file it just wrote and print PASS/FAIL with any error list, so a broken run fails
   loudly instead of silently producing an invalid file.

Add a `--seed` flag (default fixed) threaded through anywhere randomness could occur, and a
`--limit N` flag for fast local testing on a subset without touching the real pipeline logic.

Build `engine/benchmark.py`: runs rank.py end-to-end, measures wall-clock time and peak RSS memory
(use `resource` module or `psutil` if available, fall back gracefully if not installed since this
itself must not require network to pip install at benchmark time — document memory measurement caveat),
and asserts/prints whether it's within the 5-minute / 16GB budget. Save the benchmark output to
`engine/benchmark_report.txt` and reference this file directly in the README as evidence.

Add engine/tests/test_rank_e2e.py that runs the full pipeline on a small synthetic sample (~200
candidates crafted to include at least a few honeypot-like and title-chaser-like profiles) and asserts
the output CSV passes validate_submission.py and that no honeypot-like synthetic candidate lands in
the top 10.
```

---

## PROMPT 8 — Sandbox demo app (satisfies the mandatory sandbox/demo link requirement)

```
Build a minimal `sandbox/streamlit_app.py` (Streamlit, since it's free-tier deployable to Streamlit
Cloud per the spec's accepted sandbox platforms) that:

- Lets a reviewer upload a small candidates.jsonl sample (up to 100 candidates) OR use a bundled
  sample file already in sandbox/sample_candidates.jsonl (reuse the challenge's own
  sample_candidates.json, converted to jsonl).
- Runs engine/rank.py's core function (import it as a library, don't shell out) end-to-end on that
  sample and displays the resulting ranked table in-browser, including the reasoning column.
- Shows a small "compute budget" panel: elapsed time for this run, and a note that the full 100K-scale
  run is benchmarked separately in engine/benchmark_report.txt (link/display its contents).
- Has zero external API calls and works fully offline other than loading the repo's own committed
  model.txt and embedding artifacts.
- Include a requirements.txt scoped to the sandbox (streamlit + engine's deps) and a one-line note in
  the README on how to deploy it to Streamlit Community Cloud (connect repo, set app.py path, deploy —
  no secrets needed since there are no API keys involved).

Keep this app visually simple and functional — it exists to prove reproducibility, not to be the
polished product experience (that's the separate Recruiter Console in app/).
```

---

## PROMPT 9 — Wire the Recruiter Console (your existing Quantum app) to the ranking engine's output

```
In the existing app/ (formerly Quantum-main) React/TypeScript codebase, add a new top-level section
called "Candidate Intelligence" / "Ranking Console" (new route + nav entry, following the existing
Dashboard.tsx/AdminResumeScanner.tsx patterns and the GlassCard/NeonButton design system in
components/ui/Visuals.tsx).

Data contract: this new UI reads a static JSON file (e.g. public/data/ranked_candidates.json) produced
by a small export step you add to engine/rank.py (a `--export-ui-json` flag that, alongside submission.csv,
also writes a richer JSON including the full per-candidate feature breakdown — title_trajectory_score,
production_ml_evidence_score, skill_trust_score, availability_score, honeypot_suspicion_score, etc. —
not just the final CSV columns). This keeps the UI fully decoupled from the compute-constrained engine;
the UI never re-runs the ranking, it only visualizes a precomputed artifact.

Build these views:
1. **Ranked shortlist table**: rank, candidate name (anonymized), current title/company, composite
   score, a compact colored bar showing the 5-6 named feature components side by side per row, notice
   period, availability badge, honeypot-suspicion indicator (should be near-invisible for legitimate
   top candidates).
2. **Candidate detail drawer** (click a row): full profile summary, career history timeline, the
   reasoning string prominently displayed, a radar/bar chart (recharts, already a dependency) breaking
   down every named feature score, and an explicit "concerns" callout list pulled from whichever soft
   penalties fired for that candidate.
3. **"Why not #11-15" contrastive panel**: for the currently-viewed top-10 candidate, show the nearest
   candidates just outside the cutoff and the specific feature(s) that separated them — this is a
   genuinely distinctive explainability feature, make it visually clean.
4. **Compliance / compute footer bar**: displays the measured runtime and memory from
   engine/benchmark_report.txt and a "no external API calls during ranking" badge — sell the
   enterprise/production-readiness angle explicitly in the UI itself.
5. **CSV export button** that re-exports the exact submission.csv format for convenience.

Keep the existing candidate-facing features (voice interview, course ROI, career simulations) exactly
as they are — they're a different product surface and still showcase your team's range, just make sure
none of that code path is anywhere near engine/.

Update README.md to clearly document the two-app structure, and add an architecture diagram (mermaid
or a simple SVG) showing: candidates.jsonl → engine/ (offline precompute + 5-min ranking step) →
submission.csv + ranked_candidates.json → app/ (Recruiter Console, reads JSON, purely presentational).
```

---

## PROMPT 10 — README, submission_metadata.yaml, final packaging

```
Write a top-level README.md with, in this order: project overview and the two-system architecture
diagram from Prompt 9, exact reproduce command (`python engine/rank.py --candidates ./candidates.jsonl
--out ./submission.csv`), setup instructions including the one-time embedding-model download and
training step (clearly marked as OFFLINE, not part of the timed reproduction), the benchmark numbers
from engine/benchmark_report.txt, a methodology summary (≤200 words, reusable directly in the portal
metadata field) covering: feature-based scoring with named interpretable components, weak-supervision
LightGBM ranker, honeypot detection as a downweight multiplier, grounded template-based reasoning
generation, and the two-app architecture rationale. Include a "Known limitations" section (be honest —
e.g. weak labels aren't ground truth, BM25/embedding text representation is truncated, etc.) since
the spec rewards honesty over polish-washing.

Fill out submission_metadata.yaml using the provided submission_metadata_template.yaml structure, with
compute.uses_gpu_for_inference: false, has_network_during_ranking: false, and an honest
ai_usage_summary describing that Antigravity/Claude were used for code generation and architecture
iteration under human direction, with no candidate data ever sent to a hosted LLM as part of the
ranking pipeline.

Finally, run engine/rank.py end-to-end on the full candidates.jsonl, confirm engine/benchmark.py passes
budget, confirm validate_submission.py passes on the output, and commit submission.csv.
```

---

## Stitch MCP prompt — Recruiter Console UI revamp

Use this once Prompt 9's data/functionality is wired up — Stitch is for the visual layer, not logic.

```
Design a distinctive, enterprise-grade "Candidate Intelligence" dashboard for an AI recruiting platform
called Quantum, replacing/upgrading the existing screens. This is reviewed by hiring-platform engineers
judging production-readiness, not consumer app polish — lean serious, data-dense, and trustworthy over
playful.

Direction:
- Dark, high-contrast enterprise theme (deep charcoal/near-black base, one restrained accent color —
  avoid generic purple-gradient SaaS look; consider a cool emerald or amber accent used sparingly for
  score/status only, not decoration).
- Dense information hierarchy: a primary ranked-candidate table (sortable, filterable by score band,
  honeypot flag, notice period) as the main view, not cards — this is a professional tool, not a
  marketing page.
- A right-side slide-in candidate detail drawer showing: profile summary, a horizontal multi-segment
  score-breakdown bar (5-6 named components: Skill Match, Career Trajectory, Production Evidence,
  Availability, Education, with a clearly distinct honeypot-suspicion indicator that's only visually
  loud when triggered), career-history timeline, and the grounded reasoning text in a distinct
  "AI Reasoning" callout block with a small "grounded in profile data — no hallucination" trust badge.
- A "Why not the next 5" contrastive comparison strip beneath the top-10 view — small side-by-side
  mini-cards showing the specific feature deltas that separated a shown candidate from the next
  runner-up.
- A persistent thin footer/status bar: measured compute runtime, memory usage, "0 external API calls
  during ranking" badge, dataset size — treat this like an ops/observability strip, monospace numerals.
- Typography: a technical/monospace accent font for scores, IDs, and metrics; a clean humanist sans
  for prose (candidate summaries, reasoning text) — this contrast reinforces "rigorous system,
  human-readable output."
- Avoid stock AI-dashboard clichés: no glowing gradient orbs, no generic "sparkle" AI iconography, no
  purple-to-blue gradients. Prefer flat, precise, data-tool aesthetics closer to Linear, Vercel
  dashboards, or Bloomberg-terminal-adjacent density than to a typical AI-startup landing page.
- Keep it responsive down to a 13" laptop screen (this will be screen-shared in a Stage 5 interview).
```

---

## Final checklist mapped to the submission spec

- [ ] `engine/rank.py` produces exactly 100 rows, ranks 1-100 each once, scores non-increasing, ties broken by candidate_id ascending
- [ ] `validate_submission.py` passes with zero errors
- [ ] Ranking step: confirmed no network calls, no GPU, under 5 min / 16GB / 5GB disk (see `engine/benchmark_report.txt`)
- [ ] Honeypot rate in top 100 measured and under 10% (`engine/audit_honeypots.py`)
- [ ] Reasoning column present, grounded, non-templated-feeling, rank-consistent (spot check ~10 rows manually before submitting)
- [ ] `submission_metadata.yaml` at repo root, matching portal fields exactly
- [ ] Public/reachable GitHub repo with real, incremental git history (commit as you go through each prompt — don't squash into one dump)
- [ ] Working sandbox link (Streamlit Cloud deploy of `sandbox/streamlit_app.py`)
- [ ] README with the single reproduce command, methodology summary, and honest limitations section
- [ ] Filename for final CSV upload matches your registered participant/team ID exactly
