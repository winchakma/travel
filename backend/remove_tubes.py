import os, re

frontend = r"c:\Users\user\Desktop\mygym\frontend"

html_pattern = re.compile(
    r"\s*<!-- TUBES INTERACTIVE BACKGROUND -->\s*<div class=\"tubes-bg-container\">\s*<canvas id=\"tubesCanvas\" class=\"tubes-canvas\"></canvas>\s*<div class=\"tubes-bg-overlay\"></div>\s*</div>",
    re.MULTILINE
)

# Remove the script block
script_pattern = re.compile(
    r"\s*<script type=\"module\">\s*import TubesCursor from 'https://cdn\.jsdelivr\.net/npm/threejs-components@0\.0\.19/build/cursors/tubes1\.min\.js';[\s\S]*?</script>",
    re.MULTILINE
)

for fname in os.listdir(frontend):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(frontend, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = html_pattern.sub("", content)
    new_content = script_pattern.sub("", new_content)

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"fixed: {fname}")
