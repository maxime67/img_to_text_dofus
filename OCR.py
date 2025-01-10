import time
import os
import cv2
import pytesseract
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# Folder contain screenshoot
INPUT_FOLDER = "./images"
os.makedirs(INPUT_FOLDER, exist_ok=True)
# Require if tesseract not in PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ImageProcessor(FileSystemEventHandler):
    # Function to display image during processing
    def display_step(self, image, title, wait_time=2000):
        cv2.imshow(title, image)
        cv2.waitKey(wait_time)

    def process_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Failed to load image")
            # Image processing to get text more readable
            self.display_step(image, "1. Original Image")
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.display_step(gray, "3. Grayscale Image")
            _, bw_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            self.display_step(bw_image, "4. Black & White Image")
            clean_image = cv2.fastNlMeansDenoising(bw_image)
            self.display_step(clean_image, "5. Cleaned Image")
            # Stop display images after 3s
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
            # Get the text from the modify image
            text = pytesseract.image_to_string(clean_image)

            output_path = f"{image_path}_ocr.txt"

            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text)
            print(f"[OCR] Text extracted and saved to: {output_path}")
            return True
        except Exception as error:
            print(f"[OCR] Error processing image: {str(error)}")
            return False

    def on_created(self, event):
        if event.is_directory:
            return
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        if not event.src_path.lower().endswith(image_extensions):
            return
        try:
            time.sleep(1)
            original_path = event.src_path
            file_extension = os.path.splitext(original_path)[1]
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            new_filename = f"image_{timestamp}{file_extension}"
            directory = os.path.dirname(original_path)
            new_path = os.path.join(directory, new_filename)
            os.rename(original_path, new_path)
            print(f"[OCR] Renamed file to: {new_filename}")
            if self.process_image(new_path):
                os.remove(new_path)
                print(f"[OCR] Deleted processed image: {new_filename}")
        except Exception as error:
            print(f"[OCR] Error handling file: {str(error)}")


def start_monitoring():
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
