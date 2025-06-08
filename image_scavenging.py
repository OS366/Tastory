#!/usr/bin/env python3
"""
Image Scavenging Script for Tastory

Step 1: Filter pizza recipes without images
Step 2: Extract keywords from recipes
Step 3: Use Unsplash API to find matching images
Step 4: Link images back to recipe collection
"""

import json
import os
import re
from collections import Counter
from typing import Any, Dict, List

import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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


def has_valid_image(recipe: Dict[str, Any]) -> bool:
    """Check if recipe has a valid image URL"""
    main_image = recipe.get("MainImage")
    images = recipe.get("Images", [])

    # Check MainImage
    if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
        return True

    # Check Images array
    if images and isinstance(images, list) and len(images) > 0:
        if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
            return True

    return False


def extract_keywords_from_recipe(recipe: Dict[str, Any]) -> List[str]:
    """Extract relevant keywords from recipe for image searching"""
    keywords = []

    # Recipe name
    name = recipe.get("Name", "")
    if name:
        # Clean and split name
        clean_name = re.sub(r"[^\w\s]", " ", name.lower())
        name_words = [word for word in clean_name.split() if len(word) > 2]
        keywords.extend(name_words)

    # Recipe category
    category = recipe.get("RecipeCategory", "")
    if category:
        # Handle both string and list formats
        if isinstance(category, str):
            # Remove brackets and quotes, split by comma
            clean_category = re.sub(r'[\[\]"]', "", category)
            category_words = [word.strip().lower() for word in clean_category.split(",") if word.strip()]
            keywords.extend(category_words)
        elif isinstance(category, list):
            keywords.extend([cat.lower() for cat in category if isinstance(cat, str)])

    # Ingredients (top 3 most relevant)
    ingredients = recipe.get("RecipeIngredientParts", [])
    if ingredients:
        ingredient_keywords = []
        if isinstance(ingredients, list):
            for ingredient in ingredients[:5]:  # Top 5 ingredients
                if isinstance(ingredient, str):
                    # Clean ingredient name
                    clean_ingredient = re.sub(r"[^\w\s]", " ", ingredient.lower())
                    words = [word for word in clean_ingredient.split() if len(word) > 3]
                    ingredient_keywords.extend(words)

        # Get most common ingredient keywords
        if ingredient_keywords:
            common_ingredients = [word for word, count in Counter(ingredient_keywords).most_common(3)]
            keywords.extend(common_ingredients)

    # Remove common cooking words that aren't useful for image search
    stop_words = {
        "recipe",
        "easy",
        "quick",
        "simple",
        "best",
        "homemade",
        "perfect",
        "delicious",
        "minutes",
        "prep",
        "cook",
        "time",
        "serving",
        "serves",
        "ingredients",
        "instructions",
        "step",
        "add",
        "mix",
        "cook",
        "bake",
    }

    # Filter and deduplicate keywords
    filtered_keywords = []
    seen = set()
    for keyword in keywords:
        clean_keyword = keyword.strip().lower()
        if (
            clean_keyword not in stop_words
            and len(clean_keyword) > 2
            and clean_keyword not in seen
            and clean_keyword.isalpha()
        ):
            filtered_keywords.append(clean_keyword)
            seen.add(clean_keyword)

    return filtered_keywords[:5]  # Return top 5 keywords


def find_pizza_recipes_without_images(db, limit: int = 100) -> List[Dict[str, Any]]:
    """Find pizza recipes that don't have images"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Search for pizza recipes
    pizza_query = {
        "$or": [
            {"Name": {"$regex": "pizza", "$options": "i"}},
            {"RecipeCategory": {"$regex": "pizza", "$options": "i"}},
            {"Keywords": {"$regex": "pizza", "$options": "i"}},
            {"RecipeIngredientParts": {"$regex": "pizza", "$options": "i"}},
        ]
    }

    print(f"🔍 Searching for pizza recipes...")
    all_pizza_recipes = list(recipes_collection.find(pizza_query).limit(500))  # Get more to filter
    print(f"📊 Found {len(all_pizza_recipes)} total pizza recipes")

    # Filter out recipes that already have images
    recipes_without_images = []
    recipes_with_images = 0

    for recipe in all_pizza_recipes:
        if has_valid_image(recipe):
            recipes_with_images += 1
        else:
            recipes_without_images.append(recipe)
            if len(recipes_without_images) >= limit:
                break

    print(f"📈 Pizza recipes with images: {recipes_with_images}")
    print(f"📉 Pizza recipes without images: {len(recipes_without_images)}")

    return recipes_without_images


def analyze_keywords(recipes: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze and count keywords across all recipes"""
    all_keywords = []

    for recipe in recipes:
        keywords = extract_keywords_from_recipe(recipe)
        all_keywords.extend(keywords)

    # Count keyword frequency
    keyword_counts = Counter(all_keywords)
    return dict(keyword_counts.most_common(20))


def main():
    """Main function to run the image scavenging analysis"""
    print("🚀 Starting Image Scavenging Analysis...")
    print("=" * 50)

    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return

    try:
        # Step 1: Find pizza recipes without images
        print("\n📋 Step 1: Finding pizza recipes without images...")
        pizza_recipes = find_pizza_recipes_without_images(db, limit=100)

        if not pizza_recipes:
            print("❌ No pizza recipes without images found!")
            return

        print(f"✅ Found {len(pizza_recipes)} pizza recipes without images")

        # Step 2: Analyze keywords
        print("\n🔍 Step 2: Extracting and analyzing keywords...")
        keyword_stats = analyze_keywords(pizza_recipes)

        print(f"\n📊 Top Keywords Found (across {len(pizza_recipes)} recipes):")
        print("-" * 40)
        for keyword, count in keyword_stats.items():
            print(f"  {keyword:<15} : {count:>3} times")

        # Step 3: Save sample data for inspection
        print(f"\n💾 Step 3: Saving sample data for inspection...")

        # Save first 10 recipes with their extracted keywords
        sample_data = []
        for i, recipe in enumerate(pizza_recipes[:10]):
            keywords = extract_keywords_from_recipe(recipe)
            sample_data.append(
                {
                    "recipe_id": recipe.get("RecipeId"),
                    "name": recipe.get("Name"),
                    "category": recipe.get("RecipeCategory"),
                    "extracted_keywords": keywords,
                    "top_search_term": keywords[0] if keywords else "pizza",
                }
            )

        # Save to JSON file
        with open("pizza_recipes_sample.json", "w") as f:
            json.dump(sample_data, f, indent=2)

        print(f"✅ Saved sample data to 'pizza_recipes_sample.json'")

        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"  • Total pizza recipes analyzed: {len(pizza_recipes)}")
        print(f"  • Unique keywords extracted: {len(keyword_stats)}")
        print(f"  • Most common keyword: '{list(keyword_stats.keys())[0]}' ({list(keyword_stats.values())[0]} times)")
        print(f"  • Ready for Unsplash API integration!")

        print("\n🎯 Next Steps:")
        print("  1. ✅ Data extraction complete")
        print("  2. 🔄 Set up Unsplash API integration")
        print("  3. 🔄 Image matching and downloading")
        print("  4. 🔄 Database updates with image URLs")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
