#!/usr/bin/env python3
"""
Quick Pizza Test - Process just 10 pizza recipes to verify the approach works
"""

import os
import time

import pymongo
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🧪 Quick Pizza Test - Processing 10 recipes...")

    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DB_NAME", "tastory")]
    collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Pizza query
    pizza_query = {
        "$or": [
            {"Name": {"$regex": "pizza", "$options": "i"}},
            {"RecipeCategory": {"$regex": "pizza", "$options": "i"}},
        ]
    }

    # Find pizza recipes without images
    recipes = list(collection.find({"$and": [pizza_query, {"MainImage": {"$exists": False}}]}).limit(10))

    print(f"Found {len(recipes)} pizza recipes to update")

    success_count = 0

    for i, recipe in enumerate(recipes):
        recipe_id = recipe.get("RecipeId")
        recipe_name = recipe.get("Name", "Unknown")

        print(f"\n{i+1}. {recipe_name} (ID: {recipe_id})")

        # Simple image assignment
        image_url = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80"

        # Update recipe
        result = collection.update_one(
            {"RecipeId": recipe_id},
            {
                "$set": {
                    "MainImage": image_url,
                    "UnsplashData": {"food_scavenging": True, "quick_test": True, "added_at": time.time()},
                }
            },
        )

        if result.modified_count > 0:
            print(f"   ✅ Updated successfully!")
            success_count += 1
        else:
            print(f"   ❌ Failed to update")

    print(f"\n📊 Results: {success_count}/{len(recipes)} updated successfully")
    client.close()


if __name__ == "__main__":
    main()
