import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI

#  Folder contain txt render by OCR
INPUT_FOLDER = "./images"
# Folder contain txt responses
OUTPUT_FOLDER = "./responses"


# Create folders if not exists
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Get API_KEY on os env var
api_key = ""
if not api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable")

client = OpenAI(api_key=api_key)


class FileProcessor(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.txt'):
            return

        try:
            time.sleep(1)
            print(f"[OPENAI] Processing new file: {event.src_path}")

            with open(event.src_path, 'r') as file:
                content = file.read()
            import base64
            from openai import OpenAI

            client = OpenAI()

            # Path to your image
            image_path = "path_to_your_image.jpg"

            # Getting the base64 string
            base64_image = encode_image(image_path)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
            )

            filename = os.path.basename(event.src_path)
            output_path = os.path.join(OUTPUT_FOLDER, f"{filename}_analysis.txt")
            with open(output_path, 'w') as file:
                file.write(response.choices[0].message.content)

            print(f"[OPENAI] Analysis saved to: {output_path}")

        except Exception as error:
            print(f"[OPENAI] Error processing file: {str(error)}")


def start_monitoring():
    file_handler = FileProcessor()
    observer = Observer()
    observer.schedule(file_handler, INPUT_FOLDER, recursive=False)
    observer.start()

    print(f"[OPENAI] Started monitoring folder: {INPUT_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    start_monitoring()
