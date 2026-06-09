"""
inject_premium.py
Injects <script src="js/premium.js"></script> into every HTML page
right before </body>, skipping index.html.
"""
import os, re

frontend = r"c:\Users\user\Desktop\mygym\frontend"
skip = {"index.html"}

SCRIPT_TAG = '  <script src="js/premium.js"></script>'
CLOSE_BODY = "</body>"

for fname in os.listdir(frontend):
    if not fname.endswith(".html") or fname in skip:
        continue
    path = os.path.join(frontend, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "premium.js" in content:
        print(f"  already done: {fname}")
        continue

    if CLOSE_BODY not in content:
        print(f"  no </body>: {fname}")
        continue

    # Insert before the last </body>
    idx = content.rfind(CLOSE_BODY)
    content = content[:idx] + SCRIPT_TAG + "\n" + content[idx:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  injected: {fname}")

print("Done.")
