#!/usr/bin/env python3
"""
Check Broken Images - Test which pizza image URLs are working
"""

import os
import requests
import pymongo
from dotenv import load_dotenv

load_dotenv()

def test_image_url(url):
    """Test if an image URL is accessible"""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

def main():
    client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME', 'tastory')]
    collection = db[os.getenv('RECIPES_COLLECTION', 'recipes')]

    # Get pizza recipes with images
    pizzas = list(collection.find({
        "$and": [
            {"Name": {"$regex": "pizza", "$options": "i"}},
            {"MainImage": {"$exists": True, "$ne": ""}}
        ]
    }))

    print(f'🍕 Testing {len(pizzas)} pizza image URLs...')
    print("=" * 50)

    working_count = 0
    broken_count = 0

    for pizza in pizzas:
        name = pizza.get('Name', 'Unknown')
        image_url = pizza.get('MainImage', '')
        recipe_id = pizza.get('RecipeId')
        
        if image_url:
            print(f"\n📋 {name} (ID: {recipe_id})")
            print(f"   URL: {image_url}")
            
            is_working = test_image_url(image_url)
            if is_working:
                print(f"   ✅ Working")
                working_count += 1
            else:
                print(f"   ❌ BROKEN")
                broken_count += 1
        else:
            print(f"\n📋 {name} (ID: {recipe_id})")
            print(f"   ❌ No image URL")
            broken_count += 1

    print(f"\n📊 RESULTS:")
    print(f"   Working images: {working_count}")
    print(f"   Broken images: {broken_count}")
    print(f"   Success rate: {(working_count/(working_count+broken_count)*100):.1f}%")

    client.close()

if __name__ == "__main__":
    main() 