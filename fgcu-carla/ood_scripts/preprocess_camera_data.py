import os
import cv2

def preprocess_camera_images(input_folder, output_folder, target_size=(224, 224)):
    """Resize, normalize, rename images, and delete invalid files."""
    total_processed = 0
    level_counts = {}

    for level in range(6):  # Levels 0–5
        level_input = os.path.join(input_folder, f"level_{level}")
        level_output = os.path.join(output_folder, f"level_{level}")
        os.makedirs(level_output, exist_ok=True)

        count = 0
        for file in os.listdir(level_input):
            if file.endswith(".png"):
                img_path = os.path.join(level_input, file)
                output_file = os.path.join(level_output, f"level_{level}_{count + 1}.png")  # Renamed file

                # Skip if the file already exists
                if os.path.exists(output_file):
                    print(f"File already exists, skipping: {output_file}")
                    continue

                img = cv2.imread(img_path)
                if img is None:
                    # Delete corrupted or invalid images
                    print(f"Invalid or corrupted image detected and deleted: {img_path}")
                    os.remove(img_path)
                    continue

                # Resize and normalize the image
                img_resized = cv2.resize(img, target_size) / 255.0
                cv2.imwrite(output_file, (img_resized * 255).astype('uint8'))
                print(f"Processed and renamed: {output_file}")

                count += 1
                total_processed += 1

        level_counts[level] = count
        print(f"Processed {count} new images for level_{level}")

    print("\nPreprocessing Summary:")
    for level, count in level_counts.items():
        print(f"Level {level}: {count} new images")
    print(f"Total new processed images: {total_processed}")

if __name__ == "__main__":
    preprocess_camera_images(
        "C:/carla_env/fgcu-carla/scripts/output/camera",
        "C:/carla_env/fgcu-carla/scripts/preprocessed/camera"
    )
