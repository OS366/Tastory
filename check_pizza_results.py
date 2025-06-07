#!/usr/bin/env python3
"""
Check Pizza Results - See how many pizza recipes now have images
"""

import os

import pymongo
from dotenv import load_dotenv

load_dotenv()


def main():
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DB_NAME", "tastory")]
    collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Pizza query
    pizza_query = {
        "$or": [
            {"Name": {"$regex": "pizza", "$options": "i"}},
            {"RecipeCategory": {"$regex": "pizza", "$options": "i"}},
            {"Keywords": {"$regex": "pizza", "$options": "i"}},
            {"RecipeIngredientParts": {"$regex": "pizza", "$options": "i"}},
        ]
    }

    # Count total pizza recipes
    total_pizza = collection.count_documents(pizza_query)

    # Count pizza recipes with images
    pizza_with_images = collection.count_documents({"$and": [pizza_query, {"MainImage": {"$exists": True, "$ne": ""}}]})

    # Count newly added by food scavenging
    food_scavenged = collection.count_documents({"$and": [pizza_query, {"UnsplashData.food_scavenging": True}]})

    print(f"📊 PIZZA IMAGE RESULTS:")
    print(f"   Total pizza recipes: {total_pizza}")
    print(f"   With images: {pizza_with_images}")
    print(f"   Added by food scavenging: {food_scavenged}")
    print(f"   Coverage: {(pizza_with_images/total_pizza)*100:.1f}%")

    # Show some examples
    examples = list(collection.find({"$and": [pizza_query, {"UnsplashData.food_scavenging": True}]}).limit(5))

    if examples:
        print(f"\n🍕 Examples of updated recipes:")
        for recipe in examples:
            name = recipe.get("Name", "Unknown")
            keyword = recipe.get("UnsplashData", {}).get("keyword_matched", "N/A")
            print(f"   • {name} -> {keyword}")

    client.close()


if __name__ == "__main__":
    main()
