#!/usr/bin/env python3
"""
Category Attack System - Systematically Process All Food Categories
Attack recipes by categories with verified working image URLs

This script processes recipes category by category, ensuring high success rates
by using verified, working image URLs from our curated collection.
"""

import os
import time
import requests
import pymongo
from dotenv import load_dotenv
from collections import defaultdict
import sys

load_dotenv()

# VERIFIED WORKING FOOD IMAGE LIBRARY
# All URLs tested and confirmed working as of June 2025
VERIFIED_FOOD_IMAGES = {
    # PASTA & ITALIAN
    'pasta': {
        'general': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=1080&h=720&fit=crop&q=80',
        'lasagna': 'https://images.unsplash.com/photo-1574894709920-11b28e7367e3?w=1080&h=720&fit=crop&q=80',
        'spaghetti': 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=1080&h=720&fit=crop&q=80',
        'alfredo': 'https://images.unsplash.com/photo-1621996346565-e3dbc36d2e8f?w=1080&h=720&fit=crop&q=80'
    },
    
    # PIZZA
    'pizza': {
        'general': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1080&h=720&fit=crop&q=80',
        'pepperoni': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=1080&h=720&fit=crop&q=80',
        'margherita': 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1080&h=720&fit=crop&q=80'
    },
    
    # ASIAN CUISINE
    'curry': {
        'general': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1080&h=720&fit=crop&q=80',
        'chicken': 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=1080&h=720&fit=crop&q=80',
        'thai': 'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=1080&h=720&fit=crop&q=80'
    },
    
    'stir_fry': {
        'general': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=1080&h=720&fit=crop&q=80'
    },
    
    'rice': {
        'general': 'https://images.unsplash.com/photo-1563379091339-03246963d551?w=1080&h=720&fit=crop&q=80',
        'fried': 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=1080&h=720&fit=crop&q=80'
    },
    
    # MEAT & PROTEIN
    'chicken': {
        'general': 'https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=1080&h=720&fit=crop&q=80',
        'grilled': 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=1080&h=720&fit=crop&q=80',
        'fried': 'https://images.unsplash.com/photo-1562967914-608f82629710?w=1080&h=720&fit=crop&q=80'
    },
    
    'beef': {
        'general': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=1080&h=720&fit=crop&q=80',
        'steak': 'https://images.unsplash.com/photo-1558030006-450675393462?w=1080&h=720&fit=crop&q=80',
        'burger': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080&h=720&fit=crop&q=80'
    },
    
    'pork': {
        'general': 'https://images.unsplash.com/photo-1528607929212-2636ec44b3ae?w=1080&h=720&fit=crop&q=80'
    },
    
    'fish': {
        'general': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=1080&h=720&fit=crop&q=80',
        'salmon': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=1080&h=720&fit=crop&q=80'
    },
    
    # DESSERTS
    'cake': {
        'general': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&h=720&fit=crop&q=80',
        'chocolate': 'https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=1080&h=720&fit=crop&q=80'
    },
    
    'cookies': {
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
        'general': 'https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=1080&h=720&fit=crop&q=80'
    },
    
    # SALADS & VEGETABLES
    'salad': {
        'general': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=720&fit=crop&q=80'
    },
    
    'soup': {
        'general': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=1080&h=720&fit=crop&q=80'
    },
    
    # MEXICAN
    'tacos': {
        'general': 'https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1080&h=720&fit=crop&q=80'
    },
    
    'burrito': {
        'general': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=1080&h=720&fit=crop&q=80'
    },
    
    # GENERAL FALLBACK
    'general_food': {
        'general': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=1080&h=720&fit=crop&q=80'
    }
}

# Category keywords for detection
CATEGORY_KEYWORDS = {
    'pasta': ['pasta', 'spaghetti', 'lasagna', 'linguine', 'fettuccine', 'penne', 'carbonara', 'alfredo'],
    'pizza': ['pizza', 'pizzas', 'margherita', 'pepperoni'],
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

# Priority order for processing categories
CATEGORY_PRIORITY = [
    'pasta',      # High search volume (seen in logs)
    'pizza',      # Already proven successful 
    'chicken',    # Very common protein
    'curry',      # Popular cuisine
    'beef',       # Common protein
    'cake',       # Popular dessert
    'salad',      # Healthy option
    'soup',       # Common dish type
    'rice',       # Staple food
    'fish',       # Healthy protein
    'stir_fry',   # Popular cooking method
    'eggs',       # Breakfast staple
    'pancakes',   # Breakfast favorite
    'cookies',    # Popular dessert
    'ice_cream',  # Popular dessert
    'tacos',      # Popular Mexican
    'burrito',    # Popular Mexican
    'pork'        # Protein option
]

def connect_to_mongodb():
    """Connect to MongoDB database"""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ Error: MongoDB URI not found in environment variables")
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

def test_image_url(url, timeout=5):
    """Test if an image URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False

def find_recipes_by_category(db, category, limit=None):
    """Find recipes without images for a specific category"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    
    # Build category filter
    if category in CATEGORY_KEYWORDS:
        keywords = CATEGORY_KEYWORDS[category]
        category_filter = "|".join(keywords)
    else:
        category_filter = category
    
    # Query for recipes without images in this category
    query = {
        "$and": [
            {
                "$or": [
                    {"MainImage": {"$exists": False}},
                    {"MainImage": None},
                    {"MainImage": ""},
                    {"MainImage": {"$regex": "^\\s*$"}}
                ]
            },
            {
                "$or": [
                    {"Name": {"$regex": category_filter, "$options": "i"}},
                    {"RecipeCategory": {"$regex": category_filter, "$options": "i"}},
                    {"Keywords": {"$regex": category_filter, "$options": "i"}},
                ]
            }
        ]
    }
    
    cursor = recipes_collection.find(query)
    if limit:
        cursor = cursor.limit(limit)
    
    recipes = list(cursor)
    return recipes

def get_best_image_for_recipe(recipe_name, category):
    """Get the best image URL for a recipe in a category"""
    recipe_lower = recipe_name.lower()
    
    if category not in VERIFIED_FOOD_IMAGES:
        category = 'general_food'
    
    category_images = VERIFIED_FOOD_IMAGES[category]
    
    # Try to find specific match first
    for subcategory, url in category_images.items():
        if subcategory != 'general' and subcategory in recipe_lower:
            return url
    
    # Return general image for category
    return category_images.get('general', VERIFIED_FOOD_IMAGES['general_food']['general'])

def process_category(db, category, max_recipes=50):
    """Process a specific food category"""
    print(f"\n🎯 ATTACKING CATEGORY: {category.upper()}")
    print("=" * 50)
    
    # Find recipes for this category
    recipes = find_recipes_by_category(db, category, limit=max_recipes)
    
    if not recipes:
        print(f"✅ No recipes found without images for '{category}' category")
        return {'processed': 0, 'successful': 0, 'failed': 0}
    
    print(f"📋 Found {len(recipes)} '{category}' recipes without images")
    
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    processed = 0
    successful = 0
    failed = 0
    
    for i, recipe in enumerate(recipes, 1):
        recipe_id = recipe.get("RecipeId")
        recipe_name = recipe.get("Name", "Unknown Recipe")
        
        print(f"\n  {i:2d}. {recipe_name[:60]}... (ID: {recipe_id})")
        
        # Get appropriate image for this category
        image_url = get_best_image_for_recipe(recipe_name, category)
        
        # Test if image URL works
        if test_image_url(image_url):
            # Update database
            update_data = {
                "MainImage": image_url,
                "UnsplashData": {
                    "food_scavenging": True,
                    "category_attack": True,
                    "category": category,
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
                print(f"      ✅ Added {category} image")
            else:
                failed += 1
                print(f"      ❌ Database update failed")
        else:
            failed += 1
            print(f"      ❌ Image URL not accessible: {image_url}")
        
        processed += 1
        
        # Brief pause to avoid overwhelming the system
        if i % 10 == 0:
            time.sleep(0.5)
    
    success_rate = (successful / processed * 100) if processed > 0 else 0
    print(f"\n📊 {category.upper()} CATEGORY RESULTS:")
    print(f"   Processed: {processed}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {success_rate:.1f}%")
    
    return {
        'processed': processed,
        'successful': successful,
        'failed': failed,
        'success_rate': success_rate
    }

def attack_all_categories(db, max_per_category=25):
    """Attack all categories in priority order"""
    print("🚀 CATEGORY ATTACK SYSTEM ENGAGED!")
    print("=" * 60)
    print("🎯 Processing all food categories in priority order")
    print("=" * 60)
    
    total_stats = {
        'categories_processed': 0,
        'total_recipes': 0,
        'total_successful': 0,
        'category_results': {}
    }
    
    for category in CATEGORY_PRIORITY:
        try:
            results = process_category(db, category, max_per_category)
            
            total_stats['categories_processed'] += 1
            total_stats['total_recipes'] += results['processed']
            total_stats['total_successful'] += results['successful']
            total_stats['category_results'][category] = results
            
            # Brief pause between categories
            if results['processed'] > 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Error processing {category}: {e}")
    
    # Final summary
    print(f"\n🎉 CATEGORY ATTACK COMPLETE!")
    print("=" * 50)
    print(f"📋 Categories processed: {total_stats['categories_processed']}")
    print(f"📋 Total recipes processed: {total_stats['total_recipes']}")
    print(f"✅ Total successful updates: {total_stats['total_successful']}")
    
    if total_stats['total_recipes'] > 0:
        overall_success = (total_stats['total_successful'] / total_stats['total_recipes'] * 100)
        print(f"📈 Overall success rate: {overall_success:.1f}%")
    
    print(f"\n📊 CATEGORY BREAKDOWN:")
    for category, results in total_stats['category_results'].items():
        if results['processed'] > 0:
            print(f"   {category:<12} : {results['successful']:>3} / {results['processed']:>3} ({results['success_rate']:>5.1f}%)")
    
    return total_stats

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🎯 Category Attack System")
        print("=" * 30)
        print("Usage:")
        print("  python category_attack_system.py <category>  - Process specific category")
        print("  python category_attack_system.py all         - Attack all categories")
        print("  python category_attack_system.py priority    - Process in priority order")
        print("\nAvailable categories:")
        for category in CATEGORY_PRIORITY:
            print(f"  {category}")
        return
    
    target = sys.argv[1].lower()
    
    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return
    
    try:
        if target == "all" or target == "priority":
            # Attack all categories in priority order
            attack_all_categories(db, max_per_category=50)
        elif target in CATEGORY_PRIORITY:
            # Process specific category
            process_category(db, target, max_recipes=100)
        else:
            print(f"❌ Unknown category: {target}")
            print(f"Available categories: {', '.join(CATEGORY_PRIORITY)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main() 