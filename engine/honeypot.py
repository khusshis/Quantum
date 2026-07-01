from typing import Tuple, List
from datetime import datetime
from engine.schema import Candidate

def is_honeypot(candidate: Candidate) -> Tuple[float, bool, List[str]]:
    reasons = []
    suspicion_score = 0.0

    # 1. Tenure-sum mismatch
    total_months = sum(entry.duration_months for entry in candidate.career_history if entry.duration_months)
    expected_months = candidate.profile.years_of_experience * 12
    if expected_months > 0 and total_months > 0:
        ratio = total_months / expected_months
        if ratio > 1.5 or ratio < 0.5:
            reasons.append(f"Tenure mismatch: sum of roles is {total_months} months, but profile says {candidate.profile.years_of_experience} years.")
            suspicion_score += 0.3

    # 2. Skill-duration impossibility
    for skill in candidate.skills:
        if skill.proficiency.lower() == "expert":
            if (skill.duration_months == 0) or (skill.duration_months is None and skill.endorsements > 100):
                reasons.append(f"Skill impossibility: Expert in {skill.name} with 0 duration or impossible endorsements.")
                suspicion_score += 0.4
                break

    # 3. Overlapping-impossible-tenure
    # Simple check: Sort by start date and check overlaps
    overlaps = 0
    date_ranges = []
    for entry in candidate.career_history:
        try:
            start = datetime.strptime(entry.start_date, "%Y-%m-%d")
            end = datetime.strptime(entry.end_date, "%Y-%m-%d") if entry.end_date else datetime.now()
            date_ranges.append((start, end))
        except:
            pass
            
    date_ranges.sort(key=lambda x: x[0])
    for i in range(len(date_ranges) - 1):
        if date_ranges[i][1] > date_ranges[i+1][0]:
            overlap_days = (date_ranges[i][1] - date_ranges[i+1][0]).days
            if overlap_days > 180:  # > 6 months overlap
                overlaps += 1

    if overlaps > 1:
        reasons.append(f"Overlapping tenure: {overlaps} significant overlapping non-current roles.")
        suspicion_score += 0.2

    # 4. Skill-count vs seniority implausibility
    expert_skills = sum(1 for s in candidate.skills if s.proficiency.lower() == "expert")
    if expert_skills >= 10 and candidate.profile.years_of_experience < 2:
        reasons.append(f"Skill/Seniority mismatch: {expert_skills} expert skills but only {candidate.profile.years_of_experience} YOE.")
        suspicion_score += 0.5

    # 5. Signal implausibility
    summary_words = len(candidate.profile.summary.split()) if candidate.profile.summary else 0
    if candidate.redrob_signals.profile_completeness_score == 100.0 and summary_words < 5:
        reasons.append(f"Signal implausibility: 100% completeness but summary is only {summary_words} words.")
        suspicion_score += 0.2

    # 6. Education date impossibility
    for edu in candidate.education:
        if edu.start_year > edu.end_year or edu.end_year > 2030:
            reasons.append(f"Education date impossibility: start {edu.start_year}, end {edu.end_year}")
            suspicion_score += 0.3
            break
        if not edu.field_of_study.strip() or not edu.degree.strip():
            reasons.append("Education parsing failure: empty degree or field of study.")
            suspicion_score += 0.1
            break

    suspicion_score = min(1.0, suspicion_score)
    is_hp = suspicion_score > 0.6

    return suspicion_score, is_hp, reasons
