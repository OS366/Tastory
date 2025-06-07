#!/usr/bin/env python3
"""
Universal Food Image Scavenging System
Expands the successful pizza image scavenging to ALL food categories

Features:
- Automatic food category detection
- Comprehensive keyword matching for all cuisines
- Batch processing for large-scale operations
- Progress tracking and error handling
- Quality control and broken image detection
"""

import os
import time
import requests
import pymongo
from dotenv import load_dotenv
from collections import Counter, defaultdict
import re
import json

load_dotenv()

# Comprehensive food image library organized by category
FOOD_IMAGE_LIBRARY = {
    # PIZZA & ITALIAN
    'pizza': {
        'margherita': 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1080&h=720&fit=crop&q=80',
        'pepperoni': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=1080&h=720&fit=crop&q=80',
        'cheese': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80',
        'deep': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1080&h=720&fit=crop&q=80'
    },
    'pasta': {
        'spaghetti': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=1080&h=720&fit=crop&q=80',
        'lasagna': 'https://images.unsplash.com/photo-1539906665809-c6b38e6debc9?w=1080&h=720&fit=crop&q=80',
        'carbonara': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=1080&h=720&fit=crop&q=80',
        'alfredo': 'https://images.unsplash.com/photo-1621996346565-e3dbc36d2e8f?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=1080&h=720&fit=crop&q=80'
    },
    
    # ASIAN CUISINE
    'curry': {
        'chicken': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1080&h=720&fit=crop&q=80',
        'thai': 'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=1080&h=720&fit=crop&q=80',
        'indian': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1080&h=720&fit=crop&q=80',
        'coconut': 'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1080&h=720&fit=crop&q=80'
    },
    'stir_fry': {
        'vegetable': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=1080&h=720&fit=crop&q=80',
        'chicken': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=1080&h=720&fit=crop&q=80'
    },
    'rice': {
        'fried': 'https://images.unsplash.com/photo-1563379091339-03246963d551?w=1080&h=720&fit=crop&q=80',
        'biryani': 'https://images.unsplash.com/photo-1563379091339-03246963d551?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1563379091339-03246963d551?w=1080&h=720&fit=crop&q=80'
    },
    
    # MEAT & PROTEIN
    'chicken': {
        'grilled': 'https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=1080&h=720&fit=crop&q=80',
        'fried': 'https://images.unsplash.com/photo-1562967914-608f82629710?w=1080&h=720&fit=crop&q=80',
        'roasted': 'https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=1080&h=720&fit=crop&q=80'
    },
    'beef': {
        'steak': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=1080&h=720&fit=crop&q=80',
        'burger': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=1080&h=720&fit=crop&q=80'
    },
    'pork': {
        'bacon': 'https://images.unsplash.com/photo-1528607929212-2636ec44b3ae?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1528607929212-2636ec44b3ae?w=1080&h=720&fit=crop&q=80'
    },
    'fish': {
        'salmon': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=1080&h=720&fit=crop&q=80',
        'tuna': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=1080&h=720&fit=crop&q=80'
    },
    
    # DESSERTS
    'cake': {
        'chocolate': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&h=720&fit=crop&q=80',
        'vanilla': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&h=720&fit=crop&q=80',
        'birthday': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&h=720&fit=crop&q=80'
    },
    'cookies': {
        'chocolate': 'https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=1080&h=720&fit=crop&q=80'
    },
    'ice_cream': {
        'general': 'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=1080&h=720&fit=crop&q=80'
    },
    
    # BREAKFAST
    'pancakes': {
        'general': 'https://images.unsplash.com/photo-1506717847107-5e71b9242a28?w=1080&h=720&fit=crop&q=80'
    },
    'eggs': {
        'scrambled': 'https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=1080&h=720&fit=crop&q=80'
    },
    
    # VEGETABLES & SALADS
    'salad': {
        'caesar': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=720&fit=crop&q=80'
    },
    'soup': {
        'tomato': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=1080&h=720&fit=crop&q=80',
        'chicken': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=1080&h=720&fit=crop&q=80',
        'general': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=1080&h=720&fit=crop&q=80'
    },
    
    # MEXICAN
    'tacos': {
        'general': 'https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1080&h=720&fit=crop&q=80'
    },
    'burrito': {
        'general': 'https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1080&h=720&fit=crop&q=80'
    },
    
    # FALLBACK GENERAL FOOD
    'general_food': {
        'general': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=1080&h=720&fit=crop&q=80'
    }
}

# Keyword mapping to categories
CATEGORY_KEYWORDS = {
    'pizza': ['pizza', 'pizzas', 'margherita', 'pepperoni'],
    'pasta': ['pasta', 'spaghetti', 'lasagna', 'linguine', 'fettuccine', 'penne', 'carbonara', 'alfredo'],
    'curry': ['curry', 'curries', 'thai', 'indian', 'masala', 'tikka'],
    'stir_fry': ['stir fry', 'stirfry', 'wok'],
    'rice': ['rice', 'biryani', 'fried rice', 'risotto'],
    'chicken': ['chicken', 'poultry'],
    'beef': ['beef', 'steak', 'burger', 'hamburger'],
    'pork': ['pork', 'bacon', 'ham'],
    'fish': ['fish', 'salmon', 'tuna', 'cod', 'seafood'],
    'cake': ['cake', 'cakes'],
    'cookies': ['cookie', 'cookies', 'biscuit'],
    'ice_cream': ['ice cream', 'gelato', 'sorbet'],
    'pancakes': ['pancake', 'pancakes'],
    'eggs': ['egg', 'eggs', 'omelet', 'omelette'],
    'salad': ['salad', 'salads'],
    'soup': ['soup', 'soups', 'broth'],
    'tacos': ['taco', 'tacos'],
    'burrito': ['burrito', 'burritos']
}

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

def detect_food_category(recipe_name, recipe_category="", ingredients=[]):
    """Automatically detect the food category of a recipe"""
    text_to_analyze = f"{recipe_name} {recipe_category} {' '.join(ingredients)}".lower()
    
    # Score each category based on keyword matches
    category_scores = defaultdict(int)
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_to_analyze:
                category_scores[category] += len(keyword)  # Longer matches score higher
    
    # Return the highest scoring category, or 'general_food' if no matches
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    else:
        return 'general_food'

def get_image_for_recipe(recipe_name, recipe_category="", ingredients=[], recipe_id=0):
    """Get the best matching image for a recipe"""
    # Detect the main food category
    main_category = detect_food_category(recipe_name, recipe_category, ingredients)
    
    # Get subcategory images
    if main_category not in FOOD_IMAGE_LIBRARY:
        main_category = 'general_food'
    
    category_images = FOOD_IMAGE_LIBRARY[main_category]
    recipe_lower = recipe_name.lower()
    
    # Try to find specific subcategory match
    for subcategory, url in category_images.items():
        if subcategory != 'general' and subcategory in recipe_lower:
            return {
                'url': url,
                'category': main_category,
                'subcategory': subcategory,
                'match_type': 'specific'
            }
    
    # Use general image for the category with variety
    general_images = list(category_images.values())
    image_index = recipe_id % len(general_images)
    selected_url = general_images[image_index]
    
    return {
        'url': selected_url,
        'category': main_category,
        'subcategory': 'general',
        'match_type': 'category_general'
    }

def test_image_url(url, timeout=10):
    """Test if an image URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False

def find_recipes_without_images(db, limit=None, category_filter=None):
    """Find all recipes without valid images"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    
    # Build query
    query = {
        "$or": [
            {"MainImage": {"$exists": False}},
            {"MainImage": None},
            {"MainImage": ""},
            {"MainImage": {"$regex": "^\\s*$"}}
        ]
    }
    
    # Add category filter if specified
    if category_filter:
        category_query = {"$or": [
            {"Name": {"$regex": category_filter, "$options": "i"}},
            {"RecipeCategory": {"$regex": category_filter, "$options": "i"}},
            {"Keywords": {"$regex": category_filter, "$options": "i"}},
        ]}
        query = {"$and": [query, category_query]}
    
    print(f"🔍 Searching for recipes without images...")
    if category_filter:
        print(f"   Category filter: {category_filter}")
    
    cursor = recipes_collection.find(query)
    if limit:
        cursor = cursor.limit(limit)
    
    recipes = list(cursor)
    print(f"📊 Found {len(recipes)} recipes without images")
    
    return recipes

def process_recipes_batch(db, recipes, batch_size=50):
    """Process recipes in batches with progress tracking"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    
    total_recipes = len(recipes)
    processed = 0
    successful = 0
    failed = 0
    category_stats = defaultdict(int)
    
    print(f"🚀 Processing {total_recipes} recipes in batches of {batch_size}...")
    print("=" * 60)
    
    for i in range(0, total_recipes, batch_size):
        batch = recipes[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_recipes + batch_size - 1) // batch_size
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} recipes)")
        print("-" * 40)
        
        for j, recipe in enumerate(batch):
            processed += 1
            recipe_id = recipe.get("RecipeId")
            recipe_name = recipe.get("Name", "Unknown Recipe")
            recipe_category = recipe.get("RecipeCategory", "")
            ingredients = recipe.get("RecipeIngredientParts", [])
            
            # Convert ingredients to list of strings if needed
            if isinstance(ingredients, str):
                try:
                    ingredients = json.loads(ingredients) if ingredients.startswith('[') else [ingredients]
                except:
                    ingredients = [ingredients]
            elif not isinstance(ingredients, list):
                ingredients = []
            
            # Clean ingredients
            ingredients = [str(ing).strip() for ing in ingredients[:5] if ing]  # Top 5 ingredients
            
            print(f"\n  {j+1:2d}. {recipe_name[:50]}... (ID: {recipe_id})")
            
            # Get appropriate image
            image_info = get_image_for_recipe(recipe_name, recipe_category, ingredients, recipe_id)
            
            # Test if image URL works
            if test_image_url(image_info['url']):
                # Update database
                update_data = {
                    "MainImage": image_info['url'],
                    "UnsplashData": {
                        "food_scavenging": True,
                        "universal_system": True,
                        "category": image_info['category'],
                        "subcategory": image_info['subcategory'],
                        "match_type": image_info['match_type'],
                        "added_at": time.time(),
                        "recipe_name": recipe_name
                    }
                }
                
                result = recipes_collection.update_one(
                    {"RecipeId": recipe_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    successful += 1
                    category_stats[image_info['category']] += 1
                    print(f"      ✅ {image_info['category']}.{image_info['subcategory']} ({image_info['match_type']})")
                else:
                    failed += 1
                    print(f"      ❌ Database update failed")
            else:
                failed += 1
                print(f"      ❌ Image URL not accessible")
        
        # Progress summary for this batch
        batch_success_rate = ((successful / processed) * 100) if processed > 0 else 0
        print(f"\n  📊 Batch {batch_num} complete:")
        print(f"      Processed: {len(batch)}, Success: {len([r for r in batch if test_image_url(get_image_for_recipe(r.get('Name', ''), '', [], r.get('RecipeId', 0))['url'])])}")
        print(f"      Overall progress: {processed}/{total_recipes} ({(processed/total_recipes)*100:.1f}%)")
        print(f"      Success rate: {batch_success_rate:.1f}%")
        
        # Small delay between batches
        if i + batch_size < total_recipes:
            print(f"      ⏳ Brief pause before next batch...")
            time.sleep(1)
    
    return {
        'processed': processed,
        'successful': successful,
        'failed': failed,
        'category_stats': dict(category_stats)
    }

def main():
    """Main function to run universal food image scavenging"""
    print("🌍 Universal Food Image Scavenging System")
    print("=" * 50)
    print("🚀 Scaling up from pizza success to ALL food categories!")
    print("=" * 50)
    
    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return
    
    try:
        # Configuration options
        print("\n🔧 Configuration Options:")
        print("1. Process ALL recipes without images")
        print("2. Process specific category (e.g., 'pasta', 'curry')")
        print("3. Test with small sample (100 recipes)")
        
        # For demo purposes, let's start with a manageable number
        print("\n🧪 Starting with 100 recipes for testing...")
        
        # Find recipes without images
        recipes_without_images = find_recipes_without_images(db, limit=100)
        
        if not recipes_without_images:
            print("✅ All recipes already have images!")
            return
        
        # Analyze what we found
        print(f"\n📋 Analysis of {len(recipes_without_images)} recipes:")
        category_preview = defaultdict(int)
        for recipe in recipes_without_images[:20]:  # Sample analysis
            category = detect_food_category(
                recipe.get("Name", ""),
                recipe.get("RecipeCategory", ""),
                recipe.get("RecipeIngredientParts", [])
            )
            category_preview[category] += 1
        
        print("   Top categories found:")
        for category, count in sorted(category_preview.items(), key=lambda x: x[1], reverse=True):
            print(f"      {category:<15} : {count} recipes")
        
        # Process the recipes
        results = process_recipes_batch(db, recipes_without_images, batch_size=25)
        
        # Final summary
        print(f"\n📊 FINAL RESULTS:")
        print("=" * 40)
        print(f"📋 Total processed: {results['processed']}")
        print(f"✅ Successfully updated: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        
        if results['successful'] > 0:
            success_rate = (results['successful'] / results['processed']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
            
            print(f"\n🎯 Images added by category:")
            for category, count in sorted(results['category_stats'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {category:<15} : {count:>3} recipes")
            
            print(f"\n🎉 SUCCESS! {results['successful']} recipes now have images!")
            print(f"🧪 Test searches like 'pasta', 'curry', 'chicken' to see results!")
            
            print(f"\n🚀 Next steps:")
            print(f"   • Test the updated recipes in your app")
            print(f"   • Scale up to process more recipes")
            print(f"   • Run category-specific updates")
            print(f"   • Monitor and fix any broken images")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main() 