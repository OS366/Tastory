#!/usr/bin/env python3
"""
Fix Broken Images - Replace broken pizza images with working alternatives
"""

import os
import time

import pymongo
import requests
from dotenv import load_dotenv

load_dotenv()

# Working image URLs for pizza recipes (tested and verified)
WORKING_PIZZA_IMAGES = {
    "margherita": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1080&h=720&fit=crop&q=80",
    "pepperoni": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=1080&h=720&fit=crop&q=80",
    "cheese": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80",
    "chicken": "https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=1080&h=720&fit=crop&q=80",
    "veggie": "https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?w=1080&h=720&fit=crop&q=80",
    "meat": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=1080&h=720&fit=crop&q=80",
    "hawaiian": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1080&h=720&fit=crop&q=80",
    "chocolate": "https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=1080&h=720&fit=crop&q=80",
    "dessert": "https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=1080&h=720&fit=crop&q=80",
    "deep": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80",
    "general": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1080&h=720&fit=crop&q=80",
}


def test_image_url(url):
    """Test if an image URL is accessible"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False


def get_replacement_image(recipe_name, recipe_id):
    """Get a working replacement image for a recipe"""
    recipe_lower = recipe_name.lower()

    # Try to match keywords
    for keyword, url in WORKING_PIZZA_IMAGES.items():
        if keyword in recipe_lower:
            return url

    # Use variety based on recipe ID for general cases
    image_list = list(WORKING_PIZZA_IMAGES.values())
    image_index = recipe_id % len(image_list)
    return image_list[image_index]


def main():
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DB_NAME", "tastory")]
    collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Get pizza recipes with images
    pizzas = list(
        collection.find(
            {"$and": [{"Name": {"$regex": "pizza", "$options": "i"}}, {"MainImage": {"$exists": True, "$ne": ""}}]}
        )
    )

    print(f"🔧 Checking and fixing {len(pizzas)} pizza images...")
    print("=" * 50)

    fixed_count = 0
    working_count = 0
    failed_count = 0

    for pizza in pizzas:
        name = pizza.get("Name", "Unknown")
        image_url = pizza.get("MainImage", "")
        recipe_id = pizza.get("RecipeId")

        print(f"\n📋 {name} (ID: {recipe_id})")
        print(f"   Current: {image_url}")

        # Test if current image works
        if test_image_url(image_url):
            print(f"   ✅ Working - no change needed")
            working_count += 1
        else:
            print(f"   ❌ BROKEN - finding replacement...")

            # Get replacement image
            new_image_url = get_replacement_image(name, recipe_id)

            # Test replacement image
            if test_image_url(new_image_url):
                print(f"   🔄 New image: {new_image_url}")

                # Update database
                result = collection.update_one(
                    {"RecipeId": recipe_id},
                    {
                        "$set": {
                            "MainImage": new_image_url,
                            "UnsplashData.fixed_broken_image": True,
                            "UnsplashData.fix_timestamp": time.time(),
                            "UnsplashData.previous_broken_url": image_url,
                        }
                    },
                )

                if result.modified_count > 0:
                    print(f"   ✅ FIXED - Updated database")
                    fixed_count += 1
                else:
                    print(f"   ❌ Failed to update database")
                    failed_count += 1
            else:
                print(f"   ❌ Replacement image also broken!")
                failed_count += 1

    print(f"\n📊 FINAL RESULTS:")
    print(f"   Already working: {working_count}")
    print(f"   Successfully fixed: {fixed_count}")
    print(f"   Failed to fix: {failed_count}")
    print(f"   Total processed: {len(pizzas)}")

    if fixed_count > 0:
        print(f"\n🎉 Fixed {fixed_count} broken images!")
        print(f"🧪 Test your pizza search to see the improvements!")

    client.close()


if __name__ == "__main__":
    main()
