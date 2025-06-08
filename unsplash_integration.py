#!/usr/bin/env python3
"""
Unsplash Integration Script for Tastory Image Scavenging

Step 3: Use Unsplash API to find images based on extracted keywords
Step 4: Update recipe collection with image URLs
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import pymongo
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Unsplash API configuration
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_BASE_URL = "https://api.unsplash.com"


def connect_to_mongodb():
    """Connect to MongoDB database"""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MongoDB URI not found in environment variables")
        return None, None

    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command("ping")
        db_name = os.getenv("DB_NAME", "tastory")
        db = client[db_name]
        print(f"✅ Successfully connected to MongoDB database: {db_name}")
        return client, db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None, None


def search_unsplash_image(query: str, per_page: int = 1) -> Optional[Dict[str, Any]]:
    """Search for food images on Unsplash"""
    if not UNSPLASH_ACCESS_KEY:
        print("❌ Unsplash Access Key not found in environment variables")
        print("💡 Please add UNSPLASH_ACCESS_KEY to your .env file")
        return None

    # Add food context to improve results
    food_query = f"{query} food"

    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    params = {
        "query": food_query,
        "per_page": per_page,
        "orientation": "landscape",  # Better for recipe cards
        "category": "food",  # Focus on food images
        "order_by": "relevant",  # Most relevant first
    }

    try:
        print(f"🔍 Searching Unsplash for: '{food_query}'")
        response = requests.get(f"{UNSPLASH_BASE_URL}/search/photos", headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                # Get the first (most relevant) image
                image = data["results"][0]

                return {
                    "id": image["id"],
                    "url": image["urls"]["regular"],  # 1080px width
                    "small_url": image["urls"]["small"],  # 400px width
                    "thumb_url": image["urls"]["thumb"],  # 200px width
                    "alt_description": image.get("alt_description", ""),
                    "photographer": image["user"]["name"],
                    "photographer_url": image["user"]["links"]["html"],
                    "download_url": image["links"]["download_location"],
                    "unsplash_url": image["links"]["html"],
                }
            else:
                print(f"   No images found for '{food_query}'")
                return None
        else:
            print(f"❌ Unsplash API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error searching Unsplash: {e}")
        return None


def trigger_unsplash_download(download_url: str) -> bool:
    """Trigger download tracking for Unsplash (required by API terms)"""
    if not UNSPLASH_ACCESS_KEY:
        return False

    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    try:
        response = requests.get(download_url, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Warning: Could not trigger download tracking: {e}")
        return False


def update_recipe_with_image(db, recipe_id: int, image_data: Dict[str, Any]) -> bool:
    """Update recipe in database with Unsplash image data"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    try:
        # Update the recipe with the new image data
        update_data = {
            "MainImage": image_data["url"],
            "UnsplashData": {
                "image_id": image_data["id"],
                "small_url": image_data["small_url"],
                "thumb_url": image_data["thumb_url"],
                "alt_description": image_data["alt_description"],
                "photographer": image_data["photographer"],
                "photographer_url": image_data["photographer_url"],
                "unsplash_url": image_data["unsplash_url"],
                "added_at": time.time(),
            },
        }

        result = recipes_collection.update_one({"RecipeId": recipe_id}, {"$set": update_data})

        if result.modified_count > 0:
            print(f"✅ Updated recipe {recipe_id} with image")

            # Trigger download tracking (required by Unsplash API terms)
            trigger_unsplash_download(image_data["download_url"])

            return True
        else:
            print(f"❌ Failed to update recipe {recipe_id}")
            return False

    except Exception as e:
        print(f"❌ Error updating recipe {recipe_id}: {e}")
        return False


def process_recipes_with_unsplash(limit: int = 10, delay: float = 1.0) -> Dict[str, int]:
    """Process recipes and find Unsplash images for them"""

    # Load the sample data
    try:
        with open("pizza_recipes_sample.json", "r") as f:
            recipes_data = json.load(f)
    except FileNotFoundError:
        print("❌ pizza_recipes_sample.json not found!")
        print("💡 Please run image_scavenging.py first to generate the sample data")
        return {"processed": 0, "successful": 0, "failed": 0}

    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return {"processed": 0, "successful": 0, "failed": 0}

    stats = {"processed": 0, "successful": 0, "failed": 0}

    try:
        print(f"🚀 Processing {min(limit, len(recipes_data))} recipes...")
        print("=" * 50)

        for i, recipe_data in enumerate(recipes_data[:limit]):
            stats["processed"] += 1

            recipe_id = recipe_data["recipe_id"]
            recipe_name = recipe_data["name"]
            keywords = recipe_data["extracted_keywords"]
            top_search_term = recipe_data["top_search_term"]

            print(f"\n📋 Recipe {i+1}/{min(limit, len(recipes_data))}: {recipe_name}")
            print(f"   Recipe ID: {recipe_id}")
            print(f"   Keywords: {', '.join(keywords)}")
            print(f"   Search term: {top_search_term}")

            # Search for image using the top search term
            image_data = search_unsplash_image(top_search_term)

            if image_data:
                print(f"   🖼️  Found image by: {image_data['photographer']}")
                print(f"   📎 URL: {image_data['url']}")

                # Update the database
                if update_recipe_with_image(db, recipe_id, image_data):
                    stats["successful"] += 1
                    print(f"   ✅ Successfully updated recipe {recipe_id}")
                else:
                    stats["failed"] += 1
                    print(f"   ❌ Failed to update recipe {recipe_id}")
            else:
                stats["failed"] += 1
                print(f"   ❌ No image found for '{top_search_term}'")

            # Rate limiting - be respectful to Unsplash API
            if i < len(recipes_data) - 1:  # Don't delay after the last item
                print(f"   ⏳ Waiting {delay} seconds (rate limiting)...")
                time.sleep(delay)

        return stats

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return stats
    finally:
        if client:
            client.close()


def main():
    """Main function to run Unsplash integration"""
    print("🎨 Starting Unsplash Integration for Image Scavenging...")
    print("=" * 60)

    # Check if Unsplash API key is configured
    if not UNSPLASH_ACCESS_KEY:
        print("\n❌ UNSPLASH_ACCESS_KEY not found in environment variables!")
        print("\n🔧 Setup Instructions:")
        print("1. Go to https://unsplash.com/developers")
        print("2. Create a new application")
        print("3. Get your Access Key")
        print("4. Add it to your .env file:")
        print("   UNSPLASH_ACCESS_KEY=your_access_key_here")
        print("\n💡 After setup, run this script again!")
        return

    print(f"✅ Unsplash API key found")
    print(f"🔍 Ready to search for images...")

    # Process a small batch first (10 recipes)
    print(f"\n🧪 Testing with 10 recipes first...")
    stats = process_recipes_with_unsplash(limit=10, delay=1.0)

    # Print results
    print(f"\n📊 RESULTS SUMMARY:")
    print("=" * 30)
    print(f"📋 Recipes processed: {stats['processed']}")
    print(f"✅ Successfully updated: {stats['successful']}")
    print(f"❌ Failed: {stats['failed']}")

    if stats["successful"] > 0:
        success_rate = (stats["successful"] / stats["processed"]) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")

        print(f"\n🎯 Next Steps:")
        print(f"  • Test the updated recipes in your app")
        print(f"  • If results look good, process more recipes")
        print(f"  • Consider running: process_recipes_with_unsplash(limit=100)")
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"  • Check your Unsplash API key")
        print(f"  • Verify internet connection")
        print(f"  • Check API rate limits")


if __name__ == "__main__":
    main()
