import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

CLOUDINARY_URL_PROVIDED = False
if os.getenv("CLOUDINARY_CLOUD_NAME") and os.getenv("CLOUDINARY_API_KEY") and os.getenv("CLOUDINARY_API_SECRET"):
    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key = os.getenv("CLOUDINARY_API_KEY"),
        api_secret = os.getenv("CLOUDINARY_API_SECRET"),
        secure = True
    )
    CLOUDINARY_URL_PROVIDED = True

def upload_image(file_path: str, folder_name: str = "elite_gym") -> str:
    """Uploads an image to Cloudinary and returns the secure URL. 
    Falls back to returning local path if Cloudinary is not configured."""
    if not CLOUDINARY_URL_PROVIDED:
        print("[WARNING] Cloudinary not configured. Keeping local file.")
        return file_path
    
    try:
        response = cloudinary.uploader.upload(file_path, folder=folder_name)
        return response.get("secure_url", file_path)
    except Exception as e:
        print(f"[ERROR] Cloudinary upload failed: {e}")
        return file_path
