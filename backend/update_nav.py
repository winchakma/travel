import os

frontend = r"c:\Users\user\Desktop\mygym\frontend"

for fname in os.listdir(frontend):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(frontend, fname)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    changed = False
    
    for line in lines:
        if 'href="challenge.html"' in line or 'href="company.html"' in line:
            changed = True
            continue
            
        new_lines.append(line)
        
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"fixed: {fname}")
