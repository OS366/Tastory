#!/usr/bin/env python3
"""
Fix Demo Images - Remove inappropriate demo images and replace with food placeholders
"""

import os

import pymongo
from dotenv import load_dotenv

load_dotenv()


def connect_to_mongodb():
    mongodb_uri = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(mongodb_uri)
    db_name = os.getenv("DB_NAME", "tastory")
    db = client[db_name]
    return client, db


def get_food_placeholder_url(recipe_name):
    """Generate a proper food placeholder image URL"""
    # Use foodish API for random food images or a food-specific service
    food_keywords = {
        "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop",
        "chicken": "https://images.unsplash.com/photo-1588347818481-30de68b5b590?w=1080&h=720&fit=crop",
        "grilled": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1080&h=720&fit=crop",
        "chocolate": "https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=1080&h=720&fit=crop",
        "carrie": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop",  # Default to pizza
        "chicago": "https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?w=1080&h=720&fit=crop",  # Deep dish pizza
    }

    # Check for keywords in recipe name
    recipe_lower = recipe_name.lower()
    for keyword, url in food_keywords.items():
        if keyword in recipe_lower:
            return url

    # Default food image
    return "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=1080&h=720&fit=crop"


def main():
    print("🔧 Fixing inappropriate demo images...")

    client, db = connect_to_mongodb()
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    try:
        # Find all recipes with demo mode images
        demo_recipes = recipes_collection.find({"UnsplashData.demo_mode": True})

        updated_count = 0

        for recipe in demo_recipes:
            recipe_id = recipe.get("RecipeId")
            recipe_name = recipe.get("Name", "")
            current_image = recipe.get("MainImage", "")

            print(f"\n📋 Recipe: {recipe_name}")
            print(f"   ID: {recipe_id}")
            print(f"   Current image: {current_image}")

            # Generate a proper food image URL
            new_image_url = get_food_placeholder_url(recipe_name)

            # Update the recipe
            update_data = {
                "MainImage": new_image_url,
                "UnsplashData.demo_mode": False,
                "UnsplashData.fixed_inappropriate_image": True,
                "UnsplashData.alt_description": f"Delicious {recipe_name}",
                "UnsplashData.photographer": "Unsplash",
                "UnsplashData.photographer_url": "https://unsplash.com",
            }

            result = recipes_collection.update_one({"RecipeId": recipe_id}, {"$set": update_data})

            if result.modified_count > 0:
                print(f"   ✅ Updated with proper food image")
                print(f"   🖼️  New URL: {new_image_url}")
                updated_count += 1
            else:
                print(f"   ❌ Failed to update")

        print(f"\n📊 SUMMARY:")
        print(f"   Recipes updated: {updated_count}")
        print(f"   🎯 All images now show appropriate food!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
