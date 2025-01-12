import base64
import json
import os
import logging
import sys
import asyncio
from pymongo import MongoClient
from typing import List, Dict
from openai import OpenAI
from datetime import datetime
from bson.objectid import ObjectId
import motor.motor_asyncio  # For asynchronous MongoDB operations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self, openai_api_key: str, mongodb_uri: str, database_name: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.db = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)[database_name]
        self.items_collection = self.db["items"]
        self.prices_collection = self.db["prices"]

    @staticmethod
    def encode_image(image_path: str) -> str:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise

    def process_image(self, image_path: str, prompt: str) -> List[Dict]:
        try:
            base64_image = self.encode_image(image_path)
            system_prompt = {
                "role": "system",
                "content": "You are a JSON-only response bot. Always respond with valid JSON array without any additional text or explanation."
            }

            user_prompt = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_prompt, user_prompt],
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            logger.info(f"Response text: {response_text}")
            data = json.loads(response_text)['data']
            return data
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return []

    async def check_and_create_items(self, data: List[Dict]):
        for item in data:
            name = item["Nom"]
            prices = item["Prix"]
            if name:
                try:
                    # Check if the item already exists
                    existing_item = await self.items_collection.find_one({"name": name})
                    if existing_item:
                        item_id = existing_item["_id"]
                    else:
                        # Insert the new item
                        result = await self.items_collection.insert_one({
                            "name": name,
                            "createdAt": datetime.now()
                        })
                        item_id = result.inserted_id
                        logger.info(f"Created new item: {name}")

                    # Add prices to the database
                    await self.add_price(item_id, prices)
                except Exception as e:
                    logger.error(f"Error processing item '{name}': {e}")

    async def add_price(self, item_id: ObjectId, price: int):
        try:
            # Insert the price associated with the item
            await self.prices_collection.insert_one({
                "itemId": item_id,
                "value": price,
                "dateTime": datetime.now()
            })
            logger.info(f"Added price {price} for item {item_id}")
        except Exception as e:
            logger.error(f"Error adding price {price} for item {item_id}: {e}")

    async def save_to_mongodb(self, data: List[Dict]):
        if data:
            try:
                for record in data:
                    await self.prices_collection.insert_one(record)
                logger.info(f"Saved {len(data)} records to MongoDB")
            except Exception as e:
                logger.error(f"Error saving to MongoDB: {e}")

    async def process_and_save(self, image_path: str, prompt: str):
        try:
            data = self.process_image(image_path, prompt)
            await self.check_and_create_items(data)
        except Exception as e:
            logger.error(f"Error in process_and_save: {e}")


# Main function
def main():
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    processor = ImageProcessor(
        openai_api_key=,
        mongodb_uri=mongodb_uri,
        database_name="price_tracker"
    )
    prompt = (
        "Voici une image contenant des informations sur des ressources. "
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
        "- Ignorez les informations inutiles ou redondantes. "
        "- Chaque ligne correspond à une valeur unique. "
        "- Si un prix est suivi de caractères inutiles (par exemple, '*', '€'), ignorez-les."
        "\n\n"
        "Sortie JSON attendue : "
        "{'data': [{'Nom': 'Alliage Ivre', 'Catégorie': 'Alliage', 'Prix': 700361}, {'Nom': 'Ardonite', 'Catégorie': 'Alliage', 'Prix': 21449}, {'Nom': 'Pyrite', 'Catégorie': 'Alliage', 'Prix': 14862}, {'Nom': 'Plaque d'acier', 'Catégorie': 'Alliage', 'Prix': 14524}, {'Nom': 'Kryptonite', 'Catégorie': 'Alliage', 'Prix': 12345}, {'Nom': 'Rutile', 'Catégorie': 'Alliage', 'Prix': 10493}, {'Nom': 'Kouartz', 'Catégorie': 'Alliage', 'Prix': 9272}, {'Nom': 'Bakélélite', 'Catégorie': 'Alliage', 'Prix': 7305}, {'Nom': 'Kobalite', 'Catégorie': 'Alliage', 'Prix': 6402}, {'Nom': 'Magnésite', 'Catégorie': 'Alliage', 'Prix': 4008}, {'Nom': 'Ébonite', 'Catégorie': 'Alliage', 'Prix': 2459}, {'Nom': 'Aluminite', 'Catégorie': 'Alliage', 'Prix': 270}]}"
    )
    asyncio.run(processor.process_and_save("./images/img.png", prompt))


if __name__ == "__main__":
    main()
