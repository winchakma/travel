import os, re

frontend = r"c:\Users\user\Desktop\mygym\frontend"

pattern = re.compile(
    r"import TubesCursor from 'https://cdn\.jsdelivr\.net/npm/threejs-components@0\.0\.19/build/cursors/tubes1\.min\.js';\s*const canvas = document\.getElementById\('tubesCanvas'\);\s*const app = TubesCursor\(canvas, \{\s*tubes: \{\s*colors: \[\"#f967fb\", \"#53bc28\", \"#6958d5\"\],\s*lights: \{\s*intensity: 200,\s*colors: \[\"#83f36e\", \"#fe8a2e\", \"#ff008a\", \"#60aed5\"\]\s*\}\s*\}\s*\}\);\s*// Random color helper\s*const randomColors = \(count\) => \{\s*return new Array\(count\)\s*\.fill\(0\)\s*\.map\(\(\) => \"#\" \+ Math\.floor\(Math\.random\(\) \* 16777215\)\.toString\(16\)\.padStart\(6, '0'\)\);\s*\};\s*// Click anywhere to randomize\s*document\.addEventListener\('click', \(e\) => \{\s*// Allow link clicks to pass through without just randomizing\s*if \(e\.target\.closest\('a'\) \|\| e\.target\.closest\('button'\)\) return;\s*const colors = randomColors\(3\);\s*const lightsColors = randomColors\(4\);\s*app\.tubes\.setColors\(colors\);\s*app\.tubes\.setLightsColors\(lightsColors\);\s*\}\);",
    re.MULTILINE
)

replacement = """import TubesCursor from 'https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js';
    
    const canvas = document.getElementById('tubesCanvas');
    const app = TubesCursor(canvas, {
      tubes: {
        colors: ["#f5e642", "#ffffff", "#c9bc1f"],
        lights: {
          intensity: 150,
          colors: ["#f5e642", "#ffffff", "#e0cf09", "#8a8200"]
        }
      }
    });"""

for fname in os.listdir(frontend):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(frontend, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "TubesCursor" in content:
        new_content, count = pattern.subn(replacement, content)
        if count > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"fixed: {fname}")
        else:
            print(f"pattern not found in: {fname}")
