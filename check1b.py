import json

targets = ['CAND_0066999', 'CAND_0001218', 'CAND_0082913']

with open('data/candidates.jsonl') as f:
    for line in f:
        c = json.loads(line)
        if c['candidate_id'] in targets:
            print('='*50)
            print('ID:', c['candidate_id'])
            print('Title:', c['profile']['current_title'])
            print('YOE:', c['profile']['years_of_experience'])
            print('Skills:', [s['name'] for s in c.get('skills', [])[:5]])
            print('Career:')
            for exp in c.get('career_history', [])[:2]:
                print(f"  - {exp['title']} at {exp['company']} ({exp['duration_months']} mo)")
                print(f"    {exp['description'][:150]}...")
