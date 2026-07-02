import json

with open('data/candidates.jsonl') as f:
    for line in f:
        c = json.loads(line)
        if c['candidate_id'] == 'CAND_0058412':
            cv_speech_keywords = ["computer vision", "cv", "speech", "robotics", "object detection", "asr"]
            nlp_ir_keywords = ["nlp", "ir", "information retrieval", "natural language", "text"]
            
            cv_speech_count = 0
            nlp_ir_count = 0
            
            print("Checking candidate:", c['candidate_id'])
            
            for entry in c.get('career_history', []):
                desc_lower = entry['description'].lower() if 'description' in entry else ""
                title_lower = entry['title'].lower() if 'title' in entry else ""
                
                cv_matches = [k for k in cv_speech_keywords if k in desc_lower or k in title_lower]
                nlp_matches = [k for k in nlp_ir_keywords if k in desc_lower or k in title_lower]
                
                if cv_matches:
                    print(f"  [{entry['title']}] CV/Speech matched: {cv_matches}")
                    cv_speech_count += 1
                if nlp_matches:
                    print(f"  [{entry['title']}] NLP/IR matched: {nlp_matches}")
                    nlp_ir_count += 1
                    
            print(f"Final CV/Speech Count: {cv_speech_count}")
            print(f"Final NLP/IR Count: {nlp_ir_count}")
            print(f"Skills array: {[s['name'] for s in c.get('skills', [])]}")
