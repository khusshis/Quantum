import json
import pandas as pd
from scipy.stats import spearmanr
import lightgbm as lgb
import os

print('=== 1. Feature Importance ===')
m = lgb.Booster(model_file='engine/model.txt')
imp = m.feature_importance(importance_type='gain')
names = m.feature_name()
total = sum(imp)
for n, i in sorted(zip(names, imp), key=lambda x: -x[1]):
    print(f'{n}: {i:.0f}  ({100*i/total:.1f}%)')
print('\n')

print('=== 2. Feature-vs-Rank Correlation ===')
data = json.load(open('app/public/ranked_candidates.json'))
df = pd.DataFrame([{**c['features'], 'score': c['score'], 'candidate_id': c['candidate_id'], 'rank': c['rank']} for c in data])

print('Correlation of each feature with rank:')
print(df.corr(numeric_only=True)['rank'].sort_values())
print('\n')

print('=== 3. Spearman Correlation with Independent Heuristic ===')
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
print('\n')

print('=== 4. Title Trap Grep (Marketing/Sales/HR/Support/Business Analyst) ===')
trap_keywords = ['marketing', 'sales', 'hr', 'support', 'business analyst']
found_traps = []
for c in data:
    for k in trap_keywords:
        if k in c['title'].lower() or k in c['reasoning'].lower():
            found_traps.append(c)

print(f'Found {len(found_traps)} title traps.')
for t in found_traps:
    print(f"Rank {t['rank']}: {t['title']} - {t['reasoning']}")
print('\n')

print('=== 5. New Top 20 & Bottom 20 Reasoning ===')
df_sub = pd.read_csv('submission.csv')
print('=== TOP 20 ===')
print(df_sub.head(20)[['candidate_id', 'rank', 'score', 'reasoning']].to_string(index=False))
print('\n=== BOTTOM 20 (ranks 81-100) ===')
print(df_sub.tail(20)[['candidate_id', 'rank', 'score', 'reasoning']].to_string(index=False))
