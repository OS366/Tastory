#!/usr/bin/env python3
"""
Check Data Structure - Understand the structure of pizza recipes
"""

import os

import pymongo
from dotenv import load_dotenv

load_dotenv()


def main():
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DB_NAME", "tastory")]
    collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Get a sample pizza recipe to see the structure
    pizza = collection.find_one({"Name": {"$regex": "pizza", "$options": "i"}})

    if pizza:
        print("🍕 Sample pizza recipe structure:")
        print(f'   Name: {pizza.get("Name")}')
        print(f'   RecipeId: {pizza.get("RecipeId")}')
        print(f'   MainImage field exists: {"MainImage" in pizza}')
        print(f'   MainImage value: {repr(pizza.get("MainImage"))}')
        print(f'   Images field: {pizza.get("Images", "Not found")}')

        # Check how many pizza recipes have various image states
        total_pizza = collection.count_documents({"Name": {"$regex": "pizza", "$options": "i"}})

        # Recipes with MainImage field that is null/empty
        empty_mainimage = collection.count_documents(
            {
                "Name": {"$regex": "pizza", "$options": "i"},
                "$or": [
                    {"MainImage": {"$exists": False}},
                    {"MainImage": None},
                    {"MainImage": ""},
                    {"MainImage": {"$regex": "^\\s*$"}},
                ],
            }
        )

        # Recipes with valid MainImage
        valid_mainimage = collection.count_documents(
            {"Name": {"$regex": "pizza", "$options": "i"}, "MainImage": {"$regex": "^https?://", "$options": "i"}}
        )

        print(f"\n📊 Pizza Recipe Image Status:")
        print(f"   Total pizza recipes: {total_pizza}")
        print(f"   Without valid images: {empty_mainimage}")
        print(f"   With valid images: {valid_mainimage}")

        # Show some examples without images
        print(f"\n📋 Examples without images:")
        examples = list(
            collection.find(
                {
                    "Name": {"$regex": "pizza", "$options": "i"},
                    "$or": [
                        {"MainImage": {"$exists": False}},
                        {"MainImage": None},
                        {"MainImage": ""},
                        {"MainImage": {"$regex": "^\\s*$"}},
                    ],
                }
            ).limit(5)
        )

        for recipe in examples:
            print(f'   • {recipe.get("Name")} (ID: {recipe.get("RecipeId")})')
    else:
        print("❌ No pizza recipes found")

    client.close()


if __name__ == "__main__":
    main()
