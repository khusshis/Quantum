import json
data = json.load(open('app/public/ranked_candidates.json'))
trap_keywords = ['marketing', 'sales', 'hr', 'support', 'business analyst']
found_traps = []
for c in data:
    for k in trap_keywords:
        reasoning = c.get('reasoning', '')
        if isinstance(reasoning, dict):
            reasoning = reasoning.get('detailed', '')
        if k in c['title'].lower() or k in reasoning.lower():
            found_traps.append(c)
print(f'Found {len(found_traps)} title traps.')

print('\nTop 20 Domain Adjacency Penalty:')
for c in data[:20]:
    print(f"{c['rank']} | {c['candidate_id']} | Penalty: {c['features']['domain_adjacency_penalty']} | Title: {c['title']}")
