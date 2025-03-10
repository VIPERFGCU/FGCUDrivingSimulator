import os
import numpy as np
from PIL import Image
from tqdm import tqdm

# Paths
RAW_CAMERA_FOLDER = "C:/carla_env/fgcu-carla/scripts/preprocessed/camera"
PROCESSED_CAMERA_FOLDER = "C:/carla_env/fgcu-carla/scripts/preprocessed/camera_npy"
TARGET_SIZE = (128, 128)  # Resize all images

def preprocess_camera_image(image_path):
    """Convert PNG to NPY, resize, and normalize."""
    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize(TARGET_SIZE)
        image_array = np.array(image) / 255.0  # Normalize to [0,1]
        return image_array
    except Exception as e:
        print(f"⚠️ Error processing {image_path}: {e}")
        return None

def process_and_save_images():
    """Process all raw images and save them as NPY files."""
    if not os.path.exists(PROCESSED_CAMERA_FOLDER):
        os.makedirs(PROCESSED_CAMERA_FOLDER)

    for level in range(6):  # Levels 0-5
        level_input_folder = os.path.join(RAW_CAMERA_FOLDER, f"level_{level}")
        level_output_folder = os.path.join(PROCESSED_CAMERA_FOLDER, f"level_{level}")
        os.makedirs(level_output_folder, exist_ok=True)

        image_files = [f for f in os.listdir(level_input_folder) if f.endswith(".png")]
        total_images = len(image_files)
        
        print(f"📂 Processing {total_images} images in Level {level}...")

        for image_file in tqdm(image_files, desc=f"Processing Level {level}"):
            image_path = os.path.join(level_input_folder, image_file)
            processed_image = preprocess_camera_image(image_path)
            
            if processed_image is not None:
                output_file = os.path.join(level_output_folder, image_file.replace(".png", ".npy"))
                np.save(output_file, processed_image)

        print(f"✅ Processed {total_images} images for Level {level}.\n")

if __name__ == "__main__":
    process_and_save_images()
