import os
import re

base_dir = r"c:\Users\user\Desktop\mygym\frontend"
files_to_keep = ['classes.html', 'index.html']

pattern = re.compile(r'\s*<!-- GLOBAL VIDEO BACKGROUND -->\s*<div class="global-video-container">\s*<video[^>]*>\s*<source[^>]*>\s*</video>\s*<div class="global-video-overlay"></div>\s*</div>\s*', re.IGNORECASE)

for filename in os.listdir(base_dir):
    if filename.endswith(".html") and filename not in files_to_keep:
        path = os.path.join(base_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content, count = pattern.subn('', content)
        
        if count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Removed video from {filename}")
