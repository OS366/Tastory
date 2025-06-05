#!/usr/bin/env python3
"""
Demo Image Scavenging Script - Simulates Unsplash Integration

This script demonstrates the image scavenging process without requiring Unsplash API keys.
It uses placeholder images to test the database update functionality.
"""

import os
import json
import time
from typing import List, Dict, Any
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

def generate_demo_image_data(query: str) -> Dict[str, Any]:
    """Generate demo image data for testing"""
    # Using placeholder image services for demo
    image_id = f"demo_{query.replace(' ', '_')}"
    
    return {
        "id": image_id,
        "url": f"https://picsum.photos/1080/720?random={abs(hash(query)) % 1000}",
        "small_url": f"https://picsum.photos/400/267?random={abs(hash(query)) % 1000}",
        "thumb_url": f"https://picsum.photos/200/133?random={abs(hash(query)) % 1000}",
        "alt_description": f"Delicious {query}",
        "photographer": "Demo Photographer",
        "photographer_url": "https://unsplash.com",
        "download_url": f"https://api.unsplash.com/photos/{image_id}/download",
        "unsplash_url": f"https://unsplash.com/photos/{image_id}"
    }

def update_recipe_with_demo_image(db, recipe_id: int, image_data: Dict[str, Any]) -> bool:
    """Update recipe in database with demo image data"""
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
                "demo_mode": True  # Flag to indicate this is demo data
            }
        }
        
        result = recipes_collection.update_one(
            {"RecipeId": recipe_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✅ Updated recipe {recipe_id} with demo image")
            return True
        else:
            print(f"❌ Failed to update recipe {recipe_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating recipe {recipe_id}: {e}")
        return False

def demo_process_recipes(limit: int = 5) -> Dict[str, int]:
    """Demo process recipes with simulated image search"""
    
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
        print(f"🧪 DEMO MODE: Processing {min(limit, len(recipes_data))} recipes...")
        print("=" * 60)
        print("📝 Note: Using placeholder images for demonstration")
        print("=" * 60)
        
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
            
            # Generate demo image data
            print(f"🔍 Simulating search for: '{top_search_term} food'")
            image_data = generate_demo_image_data(top_search_term)
            
            print(f"   🖼️  Generated demo image by: {image_data['photographer']}")
            print(f"   📎 Demo URL: {image_data['url']}")
            
            # Update the database
            if update_recipe_with_demo_image(db, recipe_id, image_data):
                stats["successful"] += 1
                print(f"   ✅ Successfully updated recipe {recipe_id}")
            else:
                stats["failed"] += 1
                print(f"   ❌ Failed to update recipe {recipe_id}")
            
            # Small delay for demo effect
            if i < min(limit, len(recipes_data)) - 1:
                print(f"   ⏳ Processing next recipe...")
                time.sleep(0.5)
        
        return stats
        
    except Exception as e:
        print(f"❌ Error during demo processing: {e}")
        return stats
    finally:
        if client:
            client.close()

def verify_image_updates(limit: int = 5):
    """Verify that the recipes were updated with images"""
    
    # Load the sample data
    try:
        with open("pizza_recipes_sample.json", "r") as f:
            recipes_data = json.load(f)
    except FileNotFoundError:
        print("❌ pizza_recipes_sample.json not found!")
        return
    
    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return
    
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
    
    try:
        print(f"\n🔍 Verifying image updates for {min(limit, len(recipes_data))} recipes...")
        print("=" * 50)
        
        updated_count = 0
        
        for i, recipe_data in enumerate(recipes_data[:limit]):
            recipe_id = recipe_data["recipe_id"]
            recipe_name = recipe_data["name"]
            
            # Find the recipe in database
            recipe = recipes_collection.find_one({"RecipeId": recipe_id})
            
            if recipe:
                main_image = recipe.get("MainImage")
                unsplash_data = recipe.get("UnsplashData")
                
                print(f"\n📋 Recipe {i+1}: {recipe_name}")
                print(f"   Recipe ID: {recipe_id}")
                
                if main_image and main_image.startswith("http"):
                    print(f"   ✅ Has MainImage: {main_image}")
                    updated_count += 1
                    
                    if unsplash_data:
                        print(f"   📝 Photographer: {unsplash_data.get('photographer', 'Unknown')}")
                        print(f"   🔗 Unsplash URL: {unsplash_data.get('unsplash_url', 'N/A')}")
                        if unsplash_data.get("demo_mode"):
                            print(f"   🧪 Demo Mode: True")
                else:
                    print(f"   ❌ No MainImage found")
            else:
                print(f"\n📋 Recipe {i+1}: {recipe_name}")
                print(f"   ❌ Recipe not found in database")
        
        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"   Recipes checked: {min(limit, len(recipes_data))}")
        print(f"   With images: {updated_count}")
        print(f"   Success rate: {(updated_count / min(limit, len(recipes_data))) * 100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    finally:
        if client:
            client.close()

def main():
    """Main function to run demo image scavenging"""
    print("🧪 Demo Image Scavenging for Tastory")
    print("=" * 40)
    print("📝 This demo simulates the Unsplash integration process")
    print("🖼️  Using placeholder images for testing")
    print("=" * 40)
    
    # Process demo recipes
    stats = demo_process_recipes(limit=5)
    
    # Print results
    print(f"\n📊 DEMO RESULTS:")
    print("=" * 30)
    print(f"📋 Recipes processed: {stats['processed']}")
    print(f"✅ Successfully updated: {stats['successful']}")
    print(f"❌ Failed: {stats['failed']}")
    
    if stats['successful'] > 0:
        success_rate = (stats['successful'] / stats['processed']) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Verify the updates
        verify_image_updates(limit=stats['processed'])
        
        print(f"\n🎯 Demo Complete! Next Steps:")
        print(f"  • Check your API to see recipes now have images")
        print(f"  • Set up real Unsplash API key for production")
        print(f"  • Run unsplash_integration.py with real API")
        print(f"  • Scale up to process all 100 pizza recipes")
    else:
        print(f"\n🔧 Demo Issues:")
        print(f"  • Check MongoDB connection")
        print(f"  • Verify sample data exists")

if __name__ == "__main__":
    main() 