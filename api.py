"""
api.py — Lightweight Flask API server for Quantum HR Core.
Bridges the React frontend to the Python ML ranking engine.

Usage:
    python api.py

Endpoints:
    POST /api/rank  — Accepts raw candidate JSON + config, returns ranked results.
    GET  /api/health — Health check.
"""

import os
import sys
import json
import time
import tempfile
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure engine is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.schema import load_candidates, _parse_candidate
from engine.rank import run_pipeline

app = Flask(__name__)
CORS(app)  # Allow requests from localhost:3000 (Vite dev server)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "engine": "Quantum HR Core v1.0"})


@app.route("/api/rank", methods=["POST"])
def rank_candidates():
    """
    Accepts:
    {
        "candidates": [...],          # Array of raw candidate JSON objects
        "shortlist_size": 100,        # How many to shortlist
        "custom_jd_text": "...",      # Optional custom JD narrative for BM25 scoring
    }
    
    Returns:
    {
        "results": [...],             # Ranked candidate array (UI-ready)
        "elapsed_seconds": 12.3,
        "total_processed": 100000,
        "shortlist_size": 100
    }
    """
    start_time = time.time()

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    raw_candidates = data.get("candidates", [])
    shortlist_size = int(data.get("shortlist_size", 100))
    custom_jd_text = data.get("custom_jd_text", None)

    if not raw_candidates:
        return jsonify({"error": "No candidates provided"}), 400

    # Parse raw JSON dicts into engine Candidate dataclass objects
    print(f"[API] Parsing {len(raw_candidates)} candidates...")
    candidates = []
    parse_errors = 0
    for i, raw in enumerate(raw_candidates):
        try:
            c = _parse_candidate(raw)
            candidates.append(c)
        except Exception as e:
            parse_errors += 1
            if parse_errors <= 5:
                print(f"  [WARN] Could not parse candidate {i}: {e}")

    if parse_errors > 5:
        print(f"  [WARN] ... and {parse_errors - 5} more parse errors.")

    if not candidates:
        return jsonify({"error": f"Could not parse any candidates. {parse_errors} parse errors."}), 400

    print(f"[API] Successfully parsed {len(candidates)} candidates ({parse_errors} errors). Running pipeline...")

    try:
        json_export, csv_rows = run_pipeline(
            candidates,
            shortlist_size=shortlist_size,
            custom_jd_text=custom_jd_text if custom_jd_text and custom_jd_text.strip() else None
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Pipeline error: {str(e)}"}), 500

    elapsed = time.time() - start_time
    print(f"[API] Pipeline completed in {elapsed:.2f}s. Returning {len(json_export)} ranked candidates.")

    return jsonify({
        "results": json_export,
        "elapsed_seconds": round(elapsed, 2),
        "total_processed": len(candidates),
        "shortlist_size": shortlist_size,
        "parse_errors": parse_errors
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  Quantum HR Core — API Server")
    print("  Listening on http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
