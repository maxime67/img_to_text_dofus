import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI

# Create folders if they don't exist
INPUT_FOLDER = "./images"
OUTPUT_FOLDER = "./responses"
prompt = (
    "Voici un texte mal formaté contenant des informations sur des ressources. "
    "Chaque ressource possède les attributs suivants : "
    "- Nom "
    "- Catégorie (identique pour toutes les ressources, déductible du texte) "
    "- Prix (sans symboles ou caractères inutiles après le prix, comme €, *, 4€, etc.). "
    "\n\n"
    "Instructions de traitement :\n"
    "1. Reformatez et triez ces informations dans un tableau organisé avec les colonnes suivantes : "
    "- Nom "
    "- Catégorie "
    "- Prix "
    "\n\n"
    "2. Règles et contraintes : "
    "- Ignorez les informations inutiles ou redondantes (par exemple, les répétitions de la catégorie ou les éléments qui n’appartiennent pas aux champs ci-dessus). "
    "- Chaque ligne du texte correspond à une valeur unique et ne doit pas être associée à plusieurs noms ou prix. "
    "- Si un prix est suivi de caractères inutiles (par exemple, '*', '€', '4€', ou tout autre caractère ou suite sans signification), ces caractères doivent être ignorés. "
    " Il est très improbable qu'un prix soit un multiple de 10, si tu considère cela, c'est une erreur "
    "\n\n"
    "3. Sortie attendue : "
    "- Fournissez un objet JSON distinct pour chaque ressource avec les champs : "
    '{ "Nom": "<Nom de la ressource>", "Catégorie": "<Catégorie de la ressource>", "Prix": <Prix de la ressource> } '
    "- Les objets JSON doivent être prêts à être insérés dans une base MongoDB. "
    "\n\n"
    "4. Attention : "
    "- Vous n’avez pas besoin de traiter ou inclure le niveau (Level) de chaque ressource. "
    "\n\n"
    "Correspondance des informations : "
    "- Le premier 'Nom' correspond au premier 'Prix', et ainsi de suite. "
    "- La catégorie est déduite une seule fois (puisqu'elle est identique pour toutes les ressources). "
    "\n\n"
    "Exemple de traitement : "
    "Entrée :\n"
    "Nom: Ressource1\n"
    "Catégorie: TypeA\n"
    "Prix: 1200€\n"
    "Level: 5\n"
    "*texte inutile*\n"
    "Nom: Ressource2\n"
    "Prix: 950 *\n"
    "Catégorie: TypeA\n"
    "Level: 3\n"
    "Nom: Ressource3\n"
    "Prix: 1500€\n"
    "\n"
    "Sortie JSON : "
    "[ "
    '{ "Nom": "Ressource1", "Catégorie": "TypeA", "Prix": 1200 }, '
    '{ "Nom": "Ressource3", "Catégorie": "TypeA", "Prix": 1500 } '
    "]"
)


# prompt = ("I give you a text with values inside, this values are ressources, category, level and price, extract name, category and value, the category is redondant value, remove currency logo if found ")
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable")

client = OpenAI(api_key=api_key)


class FileProcessor(FileSystemEventHandler):
    def on_created(self, event):
        # Skip if it's a directory or not a text file
        if event.is_directory or not event.src_path.endswith('.txt'):
            return

        try:
            # Wait briefly to ensure file is completely written
            time.sleep(1)
            print(f"[OPENAI] Processing new file: {event.src_path}")

            # Read the file
            with open(event.src_path, 'r') as file:
                content = file.read()

            # Analyze the content using OpenAI
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": prompt},
                    {"role": "user", "content": content}
                ]
            )

            # Save the analysis
            filename = os.path.basename(event.src_path)
            output_path = os.path.join(OUTPUT_FOLDER, f"{filename}_analysis.txt")
            with open(output_path, 'w') as file:
                file.write(response.choices[0].message.content)

            # Delete original file after processing
            # os.remove(event.src_path)
            print(f"[OPENAI] Analysis saved to: {output_path}")

        except Exception as error:
            print(f"[OPENAI] Error processing file: {str(error)}")


def start_monitoring():
    # Create and start the file monitor
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