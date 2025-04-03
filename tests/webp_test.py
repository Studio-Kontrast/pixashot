import os
from PIL import Image
import io

def create_dummy_png(filename="dummy_input.png", width=100, height=50, color="red"):
    """Creates a simple PNG file."""
    img = Image.new('RGB', (width, height), color=color)
    img.save(filename, "PNG")
    print(f"Created dummy PNG: {filename}")
    return filename

def convert_png_to_webp(png_path, webp_path="output.webp", quality=80):
    """Converts a PNG image to WebP using Pillow."""
    try:
        with Image.open(png_path) as img:
            # Ensure image has an alpha channel if needed for transparency,
            # otherwise convert to RGB for broader compatibility.
            if img.mode == 'RGBA' or 'transparency' in img.info:
                 # Keep RGBA if transparency exists
                 pass
            elif img.mode != 'RGB':
                 img = img.convert('RGB')

            img.save(webp_path, "WEBP", quality=quality)
            print(f"Converted {png_path} to {webp_path} with quality {quality}")
            return webp_path
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

def verify_webp_file(webp_path):
    """Verifies if the file is a valid WebP by checking magic bytes."""
    if not os.path.exists(webp_path):
        print(f"Verification failed: File {webp_path} does not exist.")
        return False

    try:
        with open(webp_path, 'rb') as f:
            header = f.read(12) # Read the first 12 bytes

        # WebP files start with 'RIFF' (4 bytes), then file size (4 bytes), then 'WEBP' (4 bytes)
        if header[0:4] == b'RIFF' and header[8:12] == b'WEBP':
            print(f"Verification successful: {webp_path} appears to be a valid WebP file.")
            return True
        else:
            print(f"Verification failed: {webp_path} does not have the correct WebP signature.")
            print(f"  Expected RIFF....WEBP, Got: {header}")
            return False
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def cleanup_files(*filenames):
    """Removes the specified files."""
    for filename in filenames:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Cleaned up: {filename}")

if __name__ == "__main__":
    png_file = "test_input.png"
    webp_file = "test_output.webp"

    # 1. Create a dummy PNG
    create_dummy_png(png_file)

    # 2. Convert PNG to WebP
    converted_path = convert_png_to_webp(png_file, webp_file, quality=85)

    # 3. Verify the output
    if converted_path:
        verify_webp_file(converted_path)
    else:
        print("Skipping verification due to conversion error.")

    # 4. Clean up
    cleanup_files(png_file, webp_file) 