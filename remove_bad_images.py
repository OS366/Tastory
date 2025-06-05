#!/usr/bin/env python3
"""
Remove Bad Demo Images - Clear inappropriate images so recipes show no image instead of jellyfish
"""

import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🧹 Removing inappropriate demo images...")
    
    mongodb_uri = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(mongodb_uri)
    db_name = os.getenv("DB_NAME", "tastory")
    db = client[db_name]
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    
    try:
        # Recipe IDs that we know have bad demo images
        bad_image_recipe_ids = [68, 141, 161, 218, 549]
        
        updated_count = 0
        
        for recipe_id in bad_image_recipe_ids:
            # Find the recipe
            recipe = recipes_collection.find_one({"RecipeId": recipe_id})
            if recipe:
                recipe_name = recipe.get("Name", "Unknown")
                current_image = recipe.get("MainImage", "")
                
                print(f"\n📋 Recipe: {recipe_name}")
                print(f"   ID: {recipe_id}")
                print(f"   Removing: {current_image}")
                
                # Remove the MainImage and UnsplashData fields
                result = recipes_collection.update_one(
                    {"RecipeId": recipe_id},
                    {
                        "$unset": {
                            "MainImage": "",
                            "UnsplashData": ""
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f"   ✅ Removed inappropriate image")
                    updated_count += 1
                else:
                    print(f"   ❌ Failed to remove image")
            else:
                print(f"   ❌ Recipe {recipe_id} not found")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Images removed: {updated_count}")
        print(f"   🎯 Recipes now show 'no image found' instead of inappropriate images!")
        print(f"   💡 Next: Set up real Unsplash API key for proper food images")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main() 