import json
import re

aspirational_phrases = ["interested in", "hoping to", "want to move into", "transitioning to", "looking to move into", "aspiring to"]

cv_speech_keywords = ["computer vision", "cv", "speech", "robotics", "object detection", "asr"]
nlp_ir_keywords = ["nlp", "ir", "information retrieval", "natural language", "text"]

def has_aspirational(text):
    text_lower = text.lower()
    return any(p in text_lower for p in aspirational_phrases)

def strip_aspirational_sentences(text):
    # simple sentence splitting by . ! ?
    sentences = re.split(r'(?<=[.!?])\s+', text)
    valid_sentences = []
    for s in sentences:
        if not has_aspirational(s):
            valid_sentences.append(s)
    return " ".join(valid_sentences)

flipped_count = 0

with open('data/candidates.jsonl') as f:
    for line in f:
        c = json.loads(line)
        
        # Original logic
        orig_nlp_ir_count = 0
        for entry in c.get('career_history', []):
            desc_lower = entry.get('description', '').lower()
            title_lower = entry.get('title', '').lower()
            if any(k in desc_lower or k in title_lower for k in nlp_ir_keywords):
                orig_nlp_ir_count += 1
                
        # New logic
        new_nlp_ir_count = 0
        for entry in c.get('career_history', []):
            desc = entry.get('description', '')
            title = entry.get('title', '')
            
            # strip aspirational sentences from description
            desc_clean = strip_aspirational_sentences(desc).lower()
            title_lower = title.lower()
            
            if any(k in desc_clean or k in title_lower for k in nlp_ir_keywords):
                new_nlp_ir_count += 1
                
        if orig_nlp_ir_count > 0 and new_nlp_ir_count == 0:
            flipped_count += 1
            if c['candidate_id'] == 'CAND_0058412':
                print("CAND_0058412 flipped!")
                
print(f"Total candidates flipped from >0 to 0: {flipped_count}")
