import subprocess
import os

print("--- Checking git objects ---")
objects = subprocess.check_output(['git', 'rev-list', '--objects', '--all']).decode('utf-8', errors='ignore').splitlines()

sizes = []
for line in objects:
    parts = line.split(maxsplit=1)
    if len(parts) == 2:
        hash_val, path = parts
        try:
            size_out = subprocess.check_output(['git', 'cat-file', '-s', hash_val], stderr=subprocess.DEVNULL)
            size = int(size_out.strip())
            sizes.append((size, hash_val, path))
        except:
            pass

sizes.sort(reverse=True)
for s, h, p in sizes[:20]:
    print(f"{s} {p}")

print("\n--- Checking .git folder size ---")
git_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk('.git') for f in files)
print(f"Size: {git_size / (1024*1024):.2f} MB")
