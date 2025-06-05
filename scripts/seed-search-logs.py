#!/usr/bin/env python3
"""
Seed search logs with sample data for testing trending searches
"""

import os
import random
import uuid
from datetime import datetime, timedelta

import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Popular search queries for seeding
SAMPLE_QUERIES = [
    "chocolate chip cookies",
    "pasta recipes",
    "healthy breakfast",
    "chicken dinner",
    "vegan meals",
    "quick desserts",
    "pizza dough",
    "salad ideas",
    "soup recipes",
    "smoothie bowl",
    "grilled cheese",
    "tacos",
    "curry recipes",
    "baked salmon",
    "vegetarian dinner",
    "chocolate cake",
    "homemade bread",
    "ice cream",
    "stir fry",
    "pancakes",
]


def connect_to_mongodb():
    """Connect to MongoDB"""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("MongoDB URI not found. Please set it in your .env file.")
        return None, None

    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command("ping")
        db_name = os.getenv("DB_NAME", "tastory")
        db = client[db_name]
        print(f"Successfully connected to MongoDB database: {db_name}")
        return client, db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None, None


def seed_search_logs(db, num_entries=1000):
    """Seed search logs with sample data"""
    search_logs = db.search_logs

    # Clear existing logs
    print("Clearing existing search logs...")
    search_logs.delete_many({})

    # Generate logs
    entries = []
    now = datetime.utcnow()

    print(f"Generating {num_entries} search log entries...")

    for i in range(num_entries):
        # Random time within last 24 hours
        hours_ago = random.uniform(0, 24)
        timestamp = now - timedelta(hours=hours_ago)

        # Weight popular queries
        if random.random() < 0.7:  # 70% chance of popular query
            query = random.choice(SAMPLE_QUERIES[:10])  # Top 10 queries
        else:
            query = random.choice(SAMPLE_QUERIES)

        # Add some trending queries in recent time
        if hours_ago < 2 and random.random() < 0.5:
            query = random.choice(["chocolate chip cookies", "pasta recipes", "healthy breakfast"])

        entry = {
            "query": query.lower(),
            "timestamp": timestamp,
            "session_id": str(uuid.uuid4()),
            "results_count": random.randint(5, 100),
        }

        entries.append(entry)

    # Insert all entries
    print("Inserting search logs...")
    result = search_logs.insert_many(entries)
    print(f"Inserted {len(result.inserted_ids)} search log entries")

    # Create index on timestamp for better query performance
    print("Creating indexes...")
    search_logs.create_index([("timestamp", -1)])
    search_logs.create_index([("query", 1)])
    print("Indexes created")

    # Show sample trending calculation
    print("\nSample trending searches:")
    pipeline = [
        {"$match": {"timestamp": {"$gte": now - timedelta(hours=24)}}},
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]

    trending = list(search_logs.aggregate(pipeline))
    for idx, item in enumerate(trending, 1):
        print(f"{idx}. {item['_id']} - {item['count']} searches")


def main():
    """Main function"""
    client, db = connect_to_mongodb()
    if db is None:
        return

    try:
        seed_search_logs(db, num_entries=1000)
        print("\nSearch logs seeded successfully!")
    except Exception as e:
        print(f"Error seeding search logs: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
