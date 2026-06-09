import os
import re

frontend_dir = r"c:\Users\user\Desktop\mygym\frontend"
exclude_files = ['index.html']

video_pattern = re.compile(r'\s*<!-- GLOBAL VIDEO BACKGROUND -->\s*<div class="global-video-container">\s*<video[^>]*>\s*<source[^>]*>\s*</video>\s*<div class="global-video-overlay"></div>\s*</div>\s*', re.IGNORECASE)

tubes_html = """
  <!-- TUBES INTERACTIVE BACKGROUND -->
  <div class="tubes-bg-container">
    <canvas id="tubesCanvas" class="tubes-canvas"></canvas>
    <div class="tubes-bg-overlay"></div>
  </div>
"""

tubes_script = """
  <script type="module">
    import TubesCursor from 'https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js';
    
    const canvas = document.getElementById('tubesCanvas');
    const app = TubesCursor(canvas, {
      tubes: {
        colors: ["#f967fb", "#53bc28", "#6958d5"],
        lights: {
          intensity: 200,
          colors: ["#83f36e", "#fe8a2e", "#ff008a", "#60aed5"]
        }
      }
    });

    // Random color helper
    const randomColors = (count) => {
      return new Array(count)
        .fill(0)
        .map(() => "#" + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0'));
    };

    // Click anywhere to randomize
    document.addEventListener('click', (e) => {
      // Allow link clicks to pass through without just randomizing
      if (e.target.closest('a') || e.target.closest('button')) return;
      
      const colors = randomColors(3);
      const lightsColors = randomColors(4);
      app.tubes.setColors(colors);
      app.tubes.setLightsColors(lightsColors);
    });
  </script>
"""

for filename in os.listdir(frontend_dir):
    if filename.endswith(".html") and filename not in exclude_files:
        filepath = os.path.join(frontend_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                enc = 'utf-8'
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='utf-16') as f:
                content = f.read()
                enc = 'utf-16'

        # 1. Remove video if exists
        content = video_pattern.sub('', content)

        # 2. Add Tubes HTML after body tag if not present
        if 'tubes-bg-container' not in content:
            # Find body tag
            body_match = re.search(r'<body[^>]*>', content)
            if body_match:
                body_tag = body_match.group(0)
                content = content.replace(body_tag, body_tag + tubes_html)

        # 3. Add Tubes script before </body> if not present
        if 'TubesCursor' not in content:
            content = content.replace('</body>', tubes_script + '</body>')

        with open(filepath, 'w', encoding=enc) as f:
            f.write(content)
        print(f"Updated {filename}")
