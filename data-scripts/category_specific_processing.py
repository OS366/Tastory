#!/usr/bin/env python3
"""
Category-Specific Food Image Processing
Process specific food categories (pasta, curry, desserts, etc.) individually

Usage examples:
- python category_specific_processing.py pasta
- python category_specific_processing.py curry
- python category_specific_processing.py desserts
"""

import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path setup (required for relative imports)  # noqa: E402
from universal_food_image_scavenging import (  # noqa: E402
    CATEGORY_KEYWORDS,
    connect_to_mongodb,
    find_recipes_without_images,
    process_recipes_batch,
)


def main():
    if len(sys.argv) < 2:
        print("🔧 Category-Specific Food Image Processing")
        print("=" * 50)
        print("Usage: python category_specific_processing.py <category>")
        print("\nAvailable categories:")
        for category in sorted(CATEGORY_KEYWORDS.keys()):
            keywords = ", ".join(CATEGORY_KEYWORDS[category][:3])
            print(f"  {category:<15} - {keywords}...")
        print(f"  all            - Process all categories")
        return

    target_category = sys.argv[1].lower()

    print(f"🎯 Processing '{target_category}' recipes")
    print("=" * 50)

    # Connect to database
    client, db = connect_to_mongodb()
    if db is None:
        return

    try:
        if target_category == "all":
            # Process all categories
            recipes_without_images = find_recipes_without_images(db)
        else:
            # Build category filter
            if target_category in CATEGORY_KEYWORDS:
                keywords = CATEGORY_KEYWORDS[target_category]
                category_filter = "|".join(keywords)
            else:
                category_filter = target_category

            # Find recipes for specific category
            recipes_without_images = find_recipes_without_images(db, category_filter=category_filter)

        if not recipes_without_images:
            print(f"✅ All '{target_category}' recipes already have images!")
            return

        print(f"📋 Found {len(recipes_without_images)} '{target_category}' recipes without images")

        # Process the recipes
        results = process_recipes_batch(db, recipes_without_images, batch_size=25)

        # Summary
        print(f"\n🎉 Completed '{target_category}' processing!")
        print(f"✅ Updated: {results['successful']} recipes")
        if results["successful"] > 0:
            success_rate = (results["successful"] / results["processed"]) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
