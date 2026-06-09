import os
import re

frontend_dir = r'c:\Users\user\Desktop\mygym\frontend'

for fname in os.listdir(frontend_dir):
    if not fname.endswith('.html'):
        continue
    filepath = os.path.join(frontend_dir, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already added
    if 'href="company.html"' not in content:
        # We find `<a href="about.html">About</a>` and prepend the new links, preserving whitespace.
        # This will match the nav-links, mobile menu, and footer links
        # Using regex to preserve leading spaces
        content = re.sub(
            r'([ \t]*)<a href="about.html">About</a>',
            r'\1<a href="challenge.html">Challenge</a>\n\1<a href="company.html">Company</a>\n\1<a href="about.html">About</a>',
            content
        )
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {fname}')
