import sys
import argparse
from engine.schema import load_candidates
from engine.honeypot import is_honeypot

def main():
    parser = argparse.ArgumentParser(description="Audit candidates.jsonl for honeypots.")
    parser.add_argument("--candidates", type=str, default="../data/candidates.jsonl", help="Path to candidates.jsonl")
    args = parser.parse_args()

    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    
    total = len(candidates)
    if total == 0:
        print("No valid candidates loaded.")
        return

    honeypot_count = 0
    score_bands = {
        "0.0 - 0.2": 0,
        "0.2 - 0.4": 0,
        "0.4 - 0.6": 0,
        "0.6 - 0.8": 0,
        "0.8 - 1.0": 0
    }

    for cand in candidates:
        score, is_hp, reasons = is_honeypot(cand)
        if is_hp:
            honeypot_count += 1
            
        if score <= 0.2:
            score_bands["0.0 - 0.2"] += 1
        elif score <= 0.4:
            score_bands["0.2 - 0.4"] += 1
        elif score <= 0.6:
            score_bands["0.4 - 0.6"] += 1
        elif score <= 0.8:
            score_bands["0.6 - 0.8"] += 1
        else:
            score_bands["0.8 - 1.0"] += 1

    print(f"\nAudit complete for {total} candidates.")
    print(f"Total flagged as honeypot (score > 0.6): {honeypot_count} ({honeypot_count/total*100:.2f}%)")
    print("\nSuspicion Score Distribution:")
    for band, count in score_bands.items():
        print(f"  {band}: {count} ({count/total*100:.2f}%)")

if __name__ == "__main__":
    main()
