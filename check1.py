import json
import pandas as pd
from scipy.stats import spearmanr

data = json.load(open('app/public/ranked_candidates.json'))
df = pd.DataFrame([{**c['features'], 'candidate_id': c['candidate_id'], 'rank': c['rank']} for c in data])

simple_score = (
    df['role_relevance_score'] +
    df['production_ml_evidence_score'] +
    df['skill_semantic_match'] +
    df['years_experience_fit'] +
    df['consulting_only_penalty']
) / 5

df['simple_rank'] = simple_score.rank(ascending=False)
corr, p = spearmanr(df['rank'], df['simple_rank'])
print('Spearman correlation:', corr)

targets = ['CAND_0066999', 'CAND_0061175', 'CAND_0051486', 'CAND_0044262']
print('\nTarget Candidates:')
print(df[df['candidate_id'].isin(targets)][['candidate_id', 'rank', 'simple_rank']])

print('\nDisagreements > 30 positions:')
disagree = df[abs(df['rank'] - df['simple_rank']) > 30]
print(disagree[['candidate_id','rank','simple_rank']].sort_values('rank').to_string(index=False))
