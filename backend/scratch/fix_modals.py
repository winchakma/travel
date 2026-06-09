import os
import re

frontend_dir = r"c:\Users\user\Desktop\mytravelproject\frontend"

for filename in os.listdir(frontend_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regex to find <!-- AUTH MODAL --> up to just before the next <script
        # We ensure it matches up to the closing </div> of the modal by looking ahead for <script
        new_content = re.sub(r'<!-- AUTH MODAL -->[\s\S]*?(?=<script)', '', content)
        
        if content != new_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {filename}")
