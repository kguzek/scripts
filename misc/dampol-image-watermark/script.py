"""Script to batch add watermark."""

import os
from PIL import Image


def apply_watermark(input_folder, output_folder, watermark_path):
    """Applies the watermark to all files."""
    # Open the watermark image
    with Image.open(watermark_path).convert("RGBA") as watermark:
        watermark_width, watermark_height = watermark.size

        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Traverse the input folder
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.lower().endswith(".jpg"):
                    input_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, input_folder)
                    output_subfolder = os.path.join(output_folder, relative_path)

                    # Ensure subfolder structure is mirrored in output
                    if not os.path.exists(output_subfolder):
                        os.makedirs(output_subfolder)

                    output_path = os.path.join(output_subfolder, file)

                    # Open the image
                    with Image.open(input_path).convert("RGBA") as img:
                        img_width, img_height = img.size

                        # Scale watermark to fit larger but proportional
                        scale_factor = (
                            min(
                                img_width / watermark_width,
                                img_height / watermark_height,
                            )
                            * 0.5
                        )
                        new_width = int(watermark_width * scale_factor)
                        new_height = int(watermark_height * scale_factor)
                        resized_watermark = watermark.resize(
                            (new_width, new_height), Image.Resampling.LANCZOS
                        )

                        # Calculate position to place the watermark (center)
                        position = (
                            (img_width - new_width) // 2,
                            (img_height - new_height) // 2,
                        )

                        # Create a transparent layer for combining
                        transparent = Image.new("RGBA", img.size, (255, 255, 255, 0))
                        transparent.paste(img, (0, 0))
                        transparent.paste(
                            resized_watermark, position, mask=resized_watermark
                        )

                        # Save the final image
                        transparent.convert("RGB").save(output_path, "JPEG")
                        print(f"Watermarked {input_path} -> {output_path}")


def main():
    """Entry point of the script."""
    input_folder = "."  # Change to your input folder path
    output_folder = "./output_images"  # Change to your desired output folder path
    watermark_path = "./watermark.png"  # Path to your watermark image
    apply_watermark(input_folder, output_folder, watermark_path)


if __name__ == "__main__":
    main()
