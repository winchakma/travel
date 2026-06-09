"""
Remove premium.js script tag from all HTML pages.
"""
import os, re

frontend = r"c:\Users\user\Desktop\mygym\frontend"

PATTERN = re.compile(r'\s*<script src="js/premium\.js"></script>\n?', re.IGNORECASE)

for fname in os.listdir(frontend):
    if not fname.endswith(".html"):
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

    if "premium.js" not in content:
        continue

    new_content = PATTERN.sub('', content)
    with open(path, "w", encoding=enc) as f:
        f.write(new_content)
    print(f"  removed from: {fname}")

print("Done.")
