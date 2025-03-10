import os
import numpy as np
from PIL import Image, ImageFile

# Fix for truncated PNG images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Paths
RAW_CAMERA_FOLDER = "C:/carla_env/fgcu-carla/scripts/preprocessed/camera"
PROCESSED_CAMERA_FOLDER = "C:/carla_env/fgcu-carla/scripts/preprocessed/camera_npy"
TARGET_SIZE = (128, 128)  # Ensure consistent image size

def preprocess_camera_image(image_path):
    """Load, resize, and normalize camera image, skipping corrupt files."""
    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize(TARGET_SIZE)
        image_array = np.array(image) / 255.0  # Normalize pixel values (0-1)
        return image_array
    except Exception as e:
        print(f"⚠️ Skipping corrupt image: {image_path} ({e})")
        return None  # Return None for bad images

def process_and_save_images():
    """Convert all camera images to .npy format, skipping existing & corrupt files."""
    os.makedirs(PROCESSED_CAMERA_FOLDER, exist_ok=True)

    for level in range(6):  # Levels 0-5
        level_input_folder = os.path.join(RAW_CAMERA_FOLDER, f"level_{level}")
        level_output_folder = os.path.join(PROCESSED_CAMERA_FOLDER, f"level_{level}")
        os.makedirs(level_output_folder, exist_ok=True)

        image_files = [f for f in os.listdir(level_input_folder) if f.endswith(".png")]
        total_processed = 0
        total_skipped = 0
        total_corrupt = 0

        for image_file in image_files:
            output_path = os.path.join(level_output_folder, f"{os.path.splitext(image_file)[0]}.npy")

            # Skip if already processed
            if os.path.exists(output_path):
                total_skipped += 1
                continue

            # Process only new images
            image_path = os.path.join(level_input_folder, image_file)
            processed_image = preprocess_camera_image(image_path)

            # Skip corrupt images
            if processed_image is None:
                total_corrupt += 1
                continue

            np.save(output_path, processed_image)
            total_processed += 1

        print(f"✅ Processed {total_processed} new images for Level {level}. Skipped {total_skipped} existing ones. Skipped {total_corrupt} corrupt images.")

if __name__ == "__main__":
    process_and_save_images()
