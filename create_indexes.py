import os
import pymongo
from dotenv import load_dotenv

def create_indexes():
    """Create indexes to improve search performance"""
    load_dotenv()
    
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("MongoDB URI not found. Please set it in your .env file.")
        return
    
    try:
        client = pymongo.MongoClient(mongodb_uri)
        db_name = os.getenv('DB_NAME', 'tastory')
        db = client[db_name]
        recipes_collection = db[os.getenv('RECIPES_COLLECTION', 'recipes')]
        
        print(f"Connected to MongoDB database: {db_name}")
        
        # Create text index on Name field for fast text search
        print("Creating text index on Name field...")
        recipes_collection.create_index([("Name", "text")], name="idx_name_text")
        print("✓ Text index created on Name field")
        
        # Create compound index for sorting (optional but helps with performance)
        print("Creating compound index for sorting...")
        recipes_collection.create_index([
            ("AggregatedRating", -1),
            ("ReviewCount", -1)
        ], name="idx_rating_reviews")
        print("✓ Compound index created for rating and reviews")
        
        # List all indexes
        print("\nAll indexes on recipes collection:")
        for index in recipes_collection.list_indexes():
            print(f"  - {index['name']}: {index['key']}")
        
        print("\nIndexes created successfully!")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    create_indexes() 