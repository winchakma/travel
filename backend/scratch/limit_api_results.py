import os
import glob

routes_dir = r"c:\Users\user\Desktop\mytravelproject\backend\app\routes"

files_to_check = glob.glob(os.path.join(routes_dir, "*.py"))

for filepath in files_to_check:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    # Replace common slicing and ranges used for limiting results
    content = content.replace("[:20]", "[:4]")
    content = content.replace("range(20)", "range(4)")
    # Also in case there's [:10] or range(10)
    content = content.replace("[:10]", "[:4]")
    content = content.replace("range(10)", "range(4)")
    
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated limits in {os.path.basename(filepath)}")

print("All limits successfully updated to 4 items!")
