import os
from PIL import Image

def compress_images(directory):
    # Total space saved tracking
    total_original_size = 0
    total_compressed_size = 0
    compressed_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(root, file)
                
                # Get original size
                original_size = os.path.getsize(filepath)
                total_original_size += original_size
                
                try:
                    with Image.open(filepath) as img:
                        # Convert to RGB if necessary (e.g. PNG with alpha)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                            
                        # Calculate new size while maintaining aspect ratio
                        max_width = 800
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Save the image with high compression
                        # Overwrite the original file
                        img.save(filepath, "JPEG", quality=70, optimize=True)
                        
                    # Get new size
                    compressed_size = os.path.getsize(filepath)
                    total_compressed_size += compressed_size
                    compressed_count += 1
                    
                    print(f"Compressed: {file} ({original_size // 1024}KB -> {compressed_size // 1024}KB)")
                except Exception as e:
                    print(f"Error compressing {file}: {e}")

    print("-" * 30)
    print(f"Total images compressed: {compressed_count}")
    print(f"Original Total Size: {total_original_size // (1024 * 1024)} MB")
    print(f"New Total Size: {total_compressed_size // (1024 * 1024)} MB")
    print(f"Space Saved: {(total_original_size - total_compressed_size) // (1024 * 1024)} MB")

if __name__ == "__main__":
    frontend_images_dir = r"c:\Users\user\Desktop\mytravelproject\frontend\images"
    compress_images(frontend_images_dir)
