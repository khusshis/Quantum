import time
import os
import sys
import psutil
import subprocess
from pathlib import Path

def main():
    print("Running benchmark for rank.py...")
    start_time = time.time()
    
    # We will use psutil to track peak memory if we can, or just track at start/end.
    # A cleaner way is to run subprocess and poll memory.
    proc = subprocess.Popen(
        [sys.executable, "engine/rank.py", "--candidates", "data/candidates.jsonl"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    peak_memory = 0
    try:
        p = psutil.Process(proc.pid)
        while proc.poll() is None:
            try:
                mem = p.memory_info().rss
                if mem > peak_memory:
                    peak_memory = mem
            except psutil.NoSuchProcess:
                break
            time.sleep(0.1)
    except Exception as e:
        print(f"Could not track memory: {e}")
        
    stdout, stderr = proc.communicate()
    end_time = time.time()
    
    elapsed = end_time - start_time
    peak_mb = peak_memory / (1024 * 1024)
    
    report = []
    report.append("=== Benchmark Report ===")
    report.append(f"Wall-clock time: {elapsed:.2f} seconds")
    report.append(f"Peak memory: {peak_mb:.2f} MB")
    if elapsed < 300:
        report.append("Time constraint (5 min): PASS")
    else:
        report.append("Time constraint (5 min): FAIL")
        
    if peak_mb < 16000:
        report.append("Memory constraint (16 GB): PASS")
    else:
        report.append("Memory constraint (16 GB): FAIL")
        
    report.append("\n=== Stdout ===")
    report.append(stdout)
    if stderr:
        report.append("\n=== Stderr ===")
        report.append(stderr)
        
    report_text = "\n".join(report)
    print(report_text)
    
    with open("engine/benchmark_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

if __name__ == "__main__":
    main()
