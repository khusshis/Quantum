import json
data = json.load(open('app/public/ranked_candidates.json'))
print('Top 20 Domain Adjacency Penalty:')
for c in data[:20]:
    print(f"{c['rank']} | {c['candidate_id']} | Penalty: {c['features']['domain_adjacency_penalty']} | Title: {c['title']}")
