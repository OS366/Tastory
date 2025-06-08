#!/usr/bin/env python3
"""
Image System Monitor
Track the overall status of the food image scavenging system

Features:
- Overall statistics and coverage
- Category breakdown
- Broken image detection
- Progress tracking over time
"""

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime

import pymongo
import requests
from dotenv import load_dotenv

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
        return client, db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None, None


def get_overall_stats(db):
    """Get overall image statistics"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Total recipes
    total_recipes = recipes_collection.count_documents({})

    # Recipes with images
    recipes_with_images = recipes_collection.count_documents(
        {"MainImage": {"$exists": True, "$nin": [None, ""], "$not": {"$regex": "^\\s*$"}}}
    )

    # Recipes without images
    recipes_without_images = total_recipes - recipes_with_images

    # Recipes added by our scavenging system
    scavenged_recipes = recipes_collection.count_documents({"UnsplashData.food_scavenging": True})

    # Universal system recipes
    universal_system_recipes = recipes_collection.count_documents({"UnsplashData.universal_system": True})

    return {
        "total": total_recipes,
        "with_images": recipes_with_images,
        "without_images": recipes_without_images,
        "scavenged": scavenged_recipes,
        "universal_system": universal_system_recipes,
        "coverage_percentage": (recipes_with_images / total_recipes * 100) if total_recipes > 0 else 0,
    }


def get_category_breakdown(db):
    """Get breakdown by food categories"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Get scavenged recipes with category data
    scavenged_recipes = recipes_collection.find(
        {"UnsplashData.food_scavenging": True, "UnsplashData.category": {"$exists": True}}, {"UnsplashData.category": 1}
    )

    category_stats = Counter()
    for recipe in scavenged_recipes:
        category = recipe.get("UnsplashData", {}).get("category", "unknown")
        category_stats[category] += 1

    return dict(category_stats)


def check_broken_images_sample(db, sample_size=50):
    """Check a sample of images for accessibility"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Get a sample of recipes with images
    recipes_with_images = list(
        recipes_collection.find(
            {"MainImage": {"$exists": True, "$nin": [None, ""]}}, {"RecipeId": 1, "Name": 1, "MainImage": 1}
        ).limit(sample_size)
    )

    broken_count = 0
    working_count = 0
    broken_examples = []

    print(f"🔍 Testing {len(recipes_with_images)} image URLs...")

    for i, recipe in enumerate(recipes_with_images):
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(recipes_with_images)}")

        url = recipe.get("MainImage", "")
        if url:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    working_count += 1
                else:
                    broken_count += 1
                    if len(broken_examples) < 5:
                        broken_examples.append(
                            {
                                "name": recipe.get("Name", ""),
                                "url": url[:100] + "..." if len(url) > 100 else url,
                                "status": response.status_code,
                            }
                        )
            except Exception as e:
                broken_count += 1
                if len(broken_examples) < 5:
                    broken_examples.append(
                        {
                            "name": recipe.get("Name", ""),
                            "url": url[:100] + "..." if len(url) > 100 else url,
                            "error": str(e)[:50],
                        }
                    )

    return {
        "total_tested": len(recipes_with_images),
        "working": working_count,
        "broken": broken_count,
        "broken_percentage": (broken_count / len(recipes_with_images) * 100) if recipes_with_images else 0,
        "broken_examples": broken_examples,
    }


def get_recent_activity(db, days=7):
    """Get recent scavenging activity"""
    recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

    # Calculate timestamp for N days ago
    days_ago = time.time() - (days * 24 * 60 * 60)

    recent_scavenged = recipes_collection.count_documents({"UnsplashData.added_at": {"$gte": days_ago}})

    return {"days": days, "recent_additions": recent_scavenged}


def main():
    """Main monitoring function"""
    print("📊 Tastory Image System Monitor")
    print("=" * 50)
    print(f"🕒 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return

    try:
        # Overall statistics
        print("\n📈 OVERALL STATISTICS")
        print("-" * 30)
        stats = get_overall_stats(db)

        print(f"📋 Total recipes: {stats['total']:,}")
        print(f"🖼️  With images: {stats['with_images']:,}")
        print(f"❌ Without images: {stats['without_images']:,}")
        print(f"🎯 Coverage: {stats['coverage_percentage']:.1f}%")
        print(f"🤖 Scavenged by system: {stats['scavenged']:,}")
        print(f"🌍 Universal system: {stats['universal_system']:,}")

        # Coverage bar
        coverage = stats["coverage_percentage"]
        bar_length = 30
        filled = int(coverage / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"📊 Progress: [{bar}] {coverage:.1f}%")

        # Category breakdown
        print(f"\n🍽️  CATEGORY BREAKDOWN")
        print("-" * 30)
        category_stats = get_category_breakdown(db)

        if category_stats:
            total_categorized = sum(category_stats.values())
            print(f"📋 Total categorized: {total_categorized:,}")

            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_categorized * 100) if total_categorized > 0 else 0
                print(f"   {category:<15} : {count:>4} ({percentage:>4.1f}%)")
        else:
            print("   No categorized recipes found")

        # Recent activity
        print(f"\n🕒 RECENT ACTIVITY")
        print("-" * 30)
        recent = get_recent_activity(db, days=7)
        print(f"📅 Last 7 days: {recent['recent_additions']} new images added")

        # Image health check
        print(f"\n🔍 IMAGE HEALTH CHECK")
        print("-" * 30)
        health = check_broken_images_sample(db, sample_size=100)

        print(f"📋 Tested: {health['total_tested']} random images")
        print(f"✅ Working: {health['working']} ({100-health['broken_percentage']:.1f}%)")
        print(f"❌ Broken: {health['broken']} ({health['broken_percentage']:.1f}%)")

        if health["broken_examples"]:
            print(f"\n🚨 Broken image examples:")
            for i, example in enumerate(health["broken_examples"][:3], 1):
                print(f"   {i}. {example['name'][:40]}...")
                print(f"      URL: {example['url']}")
                if "status" in example:
                    print(f"      Status: {example['status']}")
                if "error" in example:
                    print(f"      Error: {example['error']}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 30)

        if stats["without_images"] > 0:
            print(f"🎯 Add images to {stats['without_images']:,} recipes")
            print(f"   Run: python universal_food_image_scavenging.py")

        if health["broken_percentage"] > 5:
            print(f"🔧 Fix {health['broken']} broken images ({health['broken_percentage']:.1f}%)")
            print(f"   Run: python fix_broken_images.py")

        if stats["coverage_percentage"] > 90:
            print(f"🎉 Excellent coverage! System is working well.")
        elif stats["coverage_percentage"] > 70:
            print(f"👍 Good coverage, keep adding images for remaining recipes.")
        else:
            print(f"⚠️  Low coverage, prioritize running image scavenging.")

        print(f"\n✅ Monitoring complete!")

    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
