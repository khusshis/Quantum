# Fix the Keyword-Matching Trap (Non-Tech Titles)

## Goal
The current ranking system heavily overfits to keyword and semantic matching, placing completely irrelevant roles (e.g., "Marketing Manager", "Customer Support") in the top 10 simply because they have AI keywords stuffed into their profile. This triggers the explicit trap outlined in the JD. Furthermore, the scores are highly compressed with exact ties at the top, indicating that career-fit features aren't properly differentiating candidates. 

We will fix this by rewriting the feature extractors to aggressively penalize non-technical titles and restructuring the weak label generator so that penalties correctly wipe out superficial skill-match scores.

## Proposed Changes

### 1. `engine/features.py`
- **[MODIFY] `title_trajectory_score`**: Currently, this is a no-op for bad titles (it only penalizes managers who don't code). We will update it to check the candidate's `current_title` against a list of valid technical terms (`engineer`, `developer`, `scientist`, `data`, `machine learning`, `researcher`). If the title is fundamentally non-technical (like Marketing, Sales, Support), the score will be crushed to `0.0`.
- **[MODIFY] `production_ml_evidence_score`**: Currently, it grants points for keywords like "production" and "retrieval" anywhere in the description. We will gate this: evidence is only counted if the associated role title is technical. A Marketing Manager will no longer get credit for "deploying retrieval systems".

### 2. `engine/weak_labels.py`
- **[MODIFY] `generate_weak_label()`**: The current formula adds career-fit penalties *before* adding the skill/embedding score. This allows perfect keyword matches to bypass career penalties. We will change the formula so that `title_trajectory_score` and `domain_adjacency_penalty` are **multipliers** against the *entire* score (including the skill score). If a candidate is a Marketing Manager, their final weak label will be forced to `0`.

### 3. `engine/reasoning.py`
- **[MODIFY] `generate_reasoning()`**: Once the scoring is fixed, non-tech roles shouldn't make the top 100. However, we will also add a guardrail in the reasoning text to stop it from combining non-tech titles with tech achievements in a single sentence if they do slip through.

## Verification Plan

### Automated Tests
- Run `python -c "..."` to print the new LightGBM `feature_importances_`. `title_trajectory_score` should become one of the most important features.
- Test a synthetic candidate ("Marketing Manager" with perfect AI skills) through `features.py` to ensure `title_trajectory_score == 0.0`.

### Manual Verification
- Re-run `train_ranker.py` and `rank.py`.
- Dump the top 10 rows of `submission.csv` to confirm that **zero** "Marketing Managers" or "Customer Support" roles are present.
- Check the score distribution in the top 10 to ensure the exact 4-way ties at `0.2841` are resolved by better feature differentiation.
