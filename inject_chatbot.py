import glob
import os

scripts_to_inject = """
<script src="js/config.js"></script>
<script src="js/chatbot.js"></script>
<script src="js/support_widget.js"></script>
"""

def inject_chatbot_scripts():
    html_files = glob.glob('c:/Users/user/Desktop/mytravelproject/*.html')
    for f in html_files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if 'chatbot.js' not in content:
            # Inject before </body>
            content = content.replace('</body>', scripts_to_inject + '\n</body>')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Injected into {os.path.basename(f)}")

if __name__ == "__main__":
    inject_chatbot_scripts()
    print("Injection complete!")
