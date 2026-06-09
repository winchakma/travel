"""
Fix: replace 'bg-[#080808]' Tailwind class on body tags.
"""
import os

frontend = r"c:\Users\user\Desktop\mygym\frontend"
skip = {"index.html"}

# Simple string replacement on the body opening tag
OLD = 'bg-[#080808] text-white'
NEW = 'text-white'

for fname in os.listdir(frontend):
    if not fname.endswith(".html") or fname in skip:
        continue
    path = os.path.join(frontend, fname)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            enc = "utf-8"
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-16") as f:
            content = f.read()
            enc = "utf-16"

    if OLD in content:
        new_content = content.replace(OLD, NEW)
        with open(path, "w", encoding=enc) as f:
            f.write(new_content)
        print(f"  fixed: {fname}")

print("Done.")
