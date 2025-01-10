import time
import os
import cv2
import pytesseract
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import numpy as np  # Added for color detection

# Create folder if it doesn't exist
INPUT_FOLDER = "./images"
os.makedirs(INPUT_FOLDER, exist_ok=True)

# Set up Tesseract path (for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ImageProcessor(FileSystemEventHandler):
    def display_step(self, image, title, wait_time=2000):
        """Display an image processing step"""
        cv2.imshow(title, image)
        cv2.waitKey(wait_time)  # Wait for 2 seconds

    def process_image(self, image_path):
        try:
            # Load and show original image
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Failed to load image")

            self.display_step(image, "1. Original Image")

            # Convert to grayscale and show
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.display_step(gray, "3. Grayscale Image")

            # Convert to black and white and show
            _, bw_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            self.display_step(bw_image, "4. Black & White Image")

            # Remove noise and show
            clean_image = cv2.fastNlMeansDenoising(bw_image)
            self.display_step(clean_image, "5. Cleaned Image")

            # Close all windows after processing
            cv2.waitKey(3000)  # Wait for 3 seconds on final image
            cv2.destroyAllWindows()

            # Extract text from image
            text = pytesseract.image_to_string(clean_image)

            # Save extracted text
            output_path = f"{image_path}_ocr.txt"
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text)

            print(f"[OCR] Text extracted and saved to: {output_path}")
            return True

        except Exception as error:
            print(f"[OCR] Error processing image: {str(error)}")
            return False

    def on_created(self, event):
        # Skip if it's a directory or not an image
        if event.is_directory:
            return

        # Check if file is an image
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        if not event.src_path.lower().endswith(image_extensions):
            return

        try:
            # Wait briefly to ensure file is completely written
            time.sleep(1)

            # Get the original file path and extension
            original_path = event.src_path
            file_extension = os.path.splitext(original_path)[1]

            # Create new filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            new_filename = f"image_{timestamp}{file_extension}"

            # Create new file path
            directory = os.path.dirname(original_path)
            new_path = os.path.join(directory, new_filename)

            # Rename the file
            os.rename(original_path, new_path)
            print(f"[OCR] Renamed file to: {new_filename}")

            # Process the renamed image
            if self.process_image(new_path):
                # Delete renamed image after successful processing
                os.remove(new_path)
                print(f"[OCR] Deleted processed image: {new_filename}")

        except Exception as error:
            print(f"[OCR] Error handling file: {str(error)}")


def start_monitoring():
    # Create and start the image monitor
    image_handler = ImageProcessor()
    observer = Observer()
    observer.schedule(image_handler, INPUT_FOLDER, recursive=False)
    observer.start()

    print(f"[OCR] Started monitoring folder: {INPUT_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    start_monitoring()
