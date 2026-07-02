limitation_text = '''

## ⚠️ Known Limitations
- **Domain Adjacency Penalty does not scan candidate skills:** The `domain_adjacency_penalty` feature explicitly scans only the `description` and `title` fields within a candidate's `career_history`. It does NOT scan the `candidate.skills` array. This means a candidate can list out-of-domain skills (e.g. "Speech Recognition") in their skills section without triggering the penalty, so long as those keywords do not appear in their actual job descriptions. This was intentionally left as-is late in the development cycle to prevent widespread changes to the feature distribution that would necessitate a risky full model retraining and re-tuning of the carefully balanced monotonic constraints.
'''

with open('README.md', 'a', encoding='utf-8') as f:
    f.write(limitation_text)
