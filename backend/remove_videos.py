import os
import re

files_to_remove = [
    'profile.html',
    'about.html',
    'membership.html',
    'demo.html',
    'activity.html'
]

base_dir = r"c:\Users\user\Desktop\mygym\frontend"

pattern = re.compile(r'\s*<!-- GLOBAL VIDEO BACKGROUND -->\s*<div class="global-video-container">\s*<video[^>]*>\s*<source[^>]*>\s*</video>\s*<div class="global-video-overlay"></div>\s*</div>\s*', re.IGNORECASE)

for html_file in files_to_remove:
    path = os.path.join(base_dir, html_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content, count = pattern.subn('', content)
        
        if count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Removed video from {html_file}")
        else:
            print(f"No video block found in {html_file}")
