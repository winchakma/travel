import os
import re

files_and_videos = {
    'about.html': 'about.mp4',
    'activity.html': 'activity.mp4',
    'classes.html': 'classes.mp4',
    'dashboard.html': 'dashboard.mp4',
    'demo.html': 'demo hud.mp4',
    'membership.html': 'membership.mp4',
    'profile.html': 'profile.mp4',
    'shop.html': 'shop.mp4',
    'studio.html': 'studio.mp4'
}

base_dir = r"c:\Users\user\Desktop\mygym\frontend"

for html_file, video_file in files_and_videos.items():
    path = os.path.join(base_dir, html_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'class="global-video-container"' in content:
            print(f"Skipping {html_file}, already has video")
            continue
            
        video_block = f"""
  <!-- GLOBAL VIDEO BACKGROUND -->
  <div class="global-video-container">
    <video class="global-video-bg" autoplay muted loop playsinline>
      <source src="videos/{video_file}" type="video/mp4">
    </video>
    <div class="global-video-overlay"></div>
  </div>
"""
        
        # Insert right after <body>
        content = re.sub(r'(<body[^>]*>)', r'\1' + video_block, content, count=1, flags=re.IGNORECASE)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added video to {html_file}")
