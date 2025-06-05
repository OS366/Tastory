import json
import os
import pickle
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pymongo
from dotenv import load_dotenv
from pymongo import UpdateOne
from tqdm import tqdm


class UploadTracker:
    def __init__(self, filename="upload_progress.pkl"):
        self.filename = filename
        self.processed_recipes = set()
        self.processed_reviews = set()
        self.load_progress()

    def load_progress(self):
        """Load previously saved progress."""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "rb") as f:
                    data = pickle.load(f)
                    self.processed_recipes = data.get("recipes", set())
                    self.processed_reviews = data.get("reviews", set())
                print(
                    f"Loaded progress: {len(self.processed_recipes)} recipes and {len(self.processed_reviews)} reviews processed"
                )
            else:
                print("No existing progress file found. Starting fresh.")
        except Exception as e:
            print(f"Could not load progress: {str(e)}. Starting fresh.")
            self.processed_recipes = set()
            self.processed_reviews = set()

    def save_progress(self):
        """Save current progress."""
        try:
            with open(self.filename, "wb") as f:
                pickle.dump({"recipes": self.processed_recipes, "reviews": self.processed_reviews}, f)
        except Exception as e:
            print(f"Could not save progress: {str(e)}")

    def mark_recipe_processed(self, recipe_id):
        """Mark a recipe as processed."""
        self.processed_recipes.add(recipe_id)

    def mark_review_processed(self, review_id):
        """Mark a review as processed."""
        self.processed_reviews.add(review_id)

    def is_recipe_processed(self, recipe_id):
        """Check if a recipe has been processed."""
        return recipe_id in self.processed_recipes

    def is_review_processed(self, review_id):
        """Check if a review has been processed."""
        return review_id in self.processed_reviews

    def reset_progress(self):
        """Reset progress for a fresh start."""
        self.processed_recipes = set()
        self.processed_reviews = set()
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
                print("Removed existing progress file.")
            except Exception as e:
                print(f"Could not remove progress file: {str(e)}")
        print("Progress tracker reset.")


def connect_to_mongodb():
    """Connect to MongoDB Atlas using credentials from .env file."""
    # Load environment variables
    load_dotenv()

    # Get MongoDB connection string
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MongoDB URI not found in environment variables")

    # Connect to MongoDB
    client = pymongo.MongoClient(mongodb_uri)

    # Get database name from env or use default
    db_name = os.getenv("DB_NAME", "tastory")
    db = client[db_name]

    return client, db


def prepare_recipe_document(recipe):
    """Convert a recipe row to a MongoDB document."""
    # Convert Series to dictionary first
    doc = recipe.to_dict()

    # Convert numpy/pandas types to Python native types
    for key, value in doc.items():
        if pd.isna(value):
            doc[key] = None
        elif isinstance(value, (pd.Timestamp, datetime)):
            doc[key] = value.isoformat()
        elif isinstance(value, np.int64):
            doc[key] = int(value)
        elif isinstance(value, np.floating):
            doc[key] = float(value)
        elif isinstance(value, np.bool_):
            doc[key] = bool(value)
        elif isinstance(value, list):
            # Handle lists (e.g., ingredients, instructions)
            doc[key] = [item.item() if isinstance(item, (np.int64, np.float64)) else item for item in value]

    return doc


def prepare_review_document(review):
    """Convert a review row to a MongoDB document."""
    # Convert Series to dictionary first
    doc = review.to_dict()

    # Convert numpy/pandas types to Python native types
    for key, value in doc.items():
        if pd.isna(value):
            doc[key] = None
        elif isinstance(value, (pd.Timestamp, datetime)):
            doc[key] = value.isoformat()
        elif isinstance(value, np.int64):
            doc[key] = int(value)
        elif isinstance(value, np.floating):
            doc[key] = float(value)
        elif isinstance(value, np.bool_):
            doc[key] = bool(value)
        elif isinstance(value, list):
            # Handle lists
            doc[key] = [item.item() if isinstance(item, (np.int64, np.float64)) else item for item in value]

    return doc


def drop_collections(db):
    """Drop recipes and reviews collections."""
    recipes_collection_name = os.getenv("RECIPES_COLLECTION", "recipes")
    reviews_collection_name = os.getenv("REVIEWS_COLLECTION", "reviews")

    if recipes_collection_name in db.list_collection_names():
        print(f"Dropping collection: {recipes_collection_name}")
        db[recipes_collection_name].drop()
        print(f"Collection {recipes_collection_name} dropped.")
    else:
        print(f"Collection {recipes_collection_name} not found, skipping drop.")

    if reviews_collection_name in db.list_collection_names():
        print(f"Dropping collection: {reviews_collection_name}")
        db[reviews_collection_name].drop()
        print(f"Collection {reviews_collection_name} dropped.")
    else:
        print(f"Collection {reviews_collection_name} not found, skipping drop.")


def upload_recipes(db, tracker, batch_size=1000):
    """Upload recipes to MongoDB Atlas."""
    print("Loading recipes data...")
    recipes_df = pd.read_parquet("recipes_cleaned.parquet")

    collection_name = os.getenv("RECIPES_COLLECTION", "recipes")
    collection = db[collection_name]

    # Create index on RecipeId
    print("Creating index on RecipeId...")
    collection.create_index("RecipeId", unique=True)

    # Filter out already processed recipes
    total_recipes = len(recipes_df)
    recipes_to_process = recipes_df[~recipes_df["RecipeId"].isin(tracker.processed_recipes)]
    print(f"Found {len(recipes_to_process)} recipes to process out of {total_recipes} total recipes")

    if len(recipes_to_process) == 0:
        print("All recipes have been processed!")
        return

    print(f"Uploading {len(recipes_to_process)} recipes...")
    operations = []
    for _, recipe in tqdm(recipes_to_process.iterrows(), total=len(recipes_to_process), desc="Uploading Recipes"):
        doc = prepare_recipe_document(recipe)
        recipe_id = doc["RecipeId"]

        operations.append(UpdateOne({"RecipeId": recipe_id}, {"$set": doc}, upsert=True))

        if len(operations) >= batch_size:
            collection.bulk_write(operations)
            for op in operations:
                recipe_id_processed = op._filter["RecipeId"]
                tracker.mark_recipe_processed(recipe_id_processed)
            tracker.save_progress()
            operations = []

    if operations:
        collection.bulk_write(operations)
        for op in operations:
            recipe_id_processed = op._filter["RecipeId"]
            tracker.mark_recipe_processed(recipe_id_processed)
        tracker.save_progress()

    print("Recipes upload complete!")


def upload_reviews(db, tracker, batch_size=1000):
    """Upload reviews to MongoDB Atlas."""
    print("Loading reviews data...")
    reviews_df = pd.read_parquet("reviews_cleaned.parquet")

    collection_name = os.getenv("REVIEWS_COLLECTION", "reviews")
    collection = db[collection_name]

    # Create indexes
    print("Creating indexes...")
    collection.create_index("ReviewId", unique=True)
    collection.create_index("RecipeId")
    collection.create_index("AuthorId")

    # Filter out already processed reviews
    total_reviews = len(reviews_df)
    reviews_to_process = reviews_df[~reviews_df["ReviewId"].isin(tracker.processed_reviews)]
    print(f"Found {len(reviews_to_process)} reviews to process out of {total_reviews} total reviews")

    if len(reviews_to_process) == 0:
        print("All reviews have been processed!")
        return

    print(f"Uploading {len(reviews_to_process)} reviews...")
    operations = []
    for _, review in tqdm(reviews_to_process.iterrows(), total=len(reviews_to_process), desc="Uploading Reviews"):
        doc = prepare_review_document(review)
        review_id = doc["ReviewId"]

        operations.append(UpdateOne({"ReviewId": review_id}, {"$set": doc}, upsert=True))

        if len(operations) >= batch_size:
            collection.bulk_write(operations)
            for op in operations:
                review_id_processed = op._filter["ReviewId"]
                tracker.mark_review_processed(review_id_processed)
            tracker.save_progress()
            operations = []

    if operations:
        collection.bulk_write(operations)
        for op in operations:
            review_id_processed = op._filter["ReviewId"]
            tracker.mark_review_processed(review_id_processed)
        tracker.save_progress()

    print("Reviews upload complete!")


def main():
    start_time = time.time()

    # Ask user if they want to drop collections and reset progress
    user_choice = input("Do you want to drop existing collections and start afresh? (yes/no): ").strip().lower()
    should_drop_collections = user_choice == "yes"

    try:
        tracker = UploadTracker()
        if should_drop_collections:
            tracker.reset_progress()

        print("Connecting to MongoDB Atlas...")
        client, db = connect_to_mongodb()

        if should_drop_collections:
            drop_collections(db)

        upload_recipes(db, tracker)
        upload_reviews(db, tracker)

        elapsed_time = time.time() - start_time
        print(f"\nUpload completed successfully in {elapsed_time:.2f} seconds!")

        recipes_count = db[os.getenv("RECIPES_COLLECTION", "recipes")].count_documents({})
        reviews_count = db[os.getenv("REVIEWS_COLLECTION", "reviews")].count_documents({})
        print(f"\nDatabase Statistics:")
        print(f"Recipes uploaded: {recipes_count}")
        print(f"Reviews uploaded: {reviews_count}")
        print(f"Recipes marked as processed: {len(tracker.processed_recipes)}")
        print(f"Reviews marked as processed: {len(tracker.processed_reviews)}")

    except Exception as e:
        print(f"Error during upload: {str(e)}")
    finally:
        # Close the MongoDB connection
        if "client" in locals():
            client.close()
            print("\nMongoDB connection closed.")


if __name__ == "__main__":
    main()
