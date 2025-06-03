import pymongo
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import time

# --- Configuration ---
MODEL_NAME = 'all-MiniLM-L6-v2'
BATCH_SIZE = 100  # Number of documents to update in MongoDB at a time

# --- Recipes Configuration ---
RECIPE_EMBEDDING_FIELD = 'recipe_embedding_all_MiniLM_L6_v2'
RECIPE_FIELDS_TO_EMBED = ['Name', 'Description', 'Keywords', 'RecipeIngredientParts', 'RecipeInstructions']

# --- Reviews Configuration ---
REVIEW_EMBEDDING_FIELD = 'review_embedding_all_MiniLM_L6_v2'
REVIEW_FIELDS_TO_EMBED = ['Review'] # Primarily the review text itself

# --- Load Embedding Model ---
e_model = None
try:
    print(f"Loading sentence-transformer model: {MODEL_NAME}...")
    e_model = SentenceTransformer(MODEL_NAME)
    print(f"Model {MODEL_NAME} loaded successfully.")
except Exception as e:
    print(f"Error loading sentence-transformer model: {e}")
    exit()

# --- MongoDB Connection Utility ---
def get_mongodb_collection(collection_env_var, default_collection_name):
    load_dotenv()
    mongodb_uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('DB_NAME', 'tastory')
    # Use the provided environment variable for collection name, or default
    collection_name_to_use = os.getenv(collection_env_var, default_collection_name)

    if not mongodb_uri:
        print("MongoDB URI not found in .env file.")
        return None

    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command('ping')
        db = client[db_name]
        collection = db[collection_name_to_use]
        print(f"Successfully connected to MongoDB: {db_name}/{collection_name_to_use}")
        return collection
    except Exception as e:
        print(f"Error connecting to MongoDB for {collection_name_to_use}: {e}")
        return None

# --- Text Generation Functions ---
def generate_text_for_recipe_embedding(recipe_doc):
    texts_to_join = []
    for field in RECIPE_FIELDS_TO_EMBED:
        content = recipe_doc.get(field)
        if content:
            if isinstance(content, list):
                texts_to_join.append(" ".join(str(item) for item in content if item))
            elif isinstance(content, str):
                texts_to_join.append(content)
    return " . ".join(texts_to_join).strip()

def generate_text_for_review_embedding(review_doc):
    texts_to_join = []
    for field in REVIEW_FIELDS_TO_EMBED:
        content = review_doc.get(field)
        if content and isinstance(content, str):
            texts_to_join.append(content)
    return " . ".join(texts_to_join).strip()

# --- Generic Embedding Upload Function ---
def process_collection_embeddings(
    collection, 
    embedding_field_name, 
    text_generation_func, 
    collection_desc # For tqdm description
):
    if e_model is None:
        print("Embedding model not loaded. Skipping collection.")
        return
    if collection is None:
        print(f"MongoDB collection for {collection_desc} not available. Skipping.")
        return

    query = {embedding_field_name: {"$exists": False}}
    total_docs_to_process = collection.count_documents(query)

    if total_docs_to_process == 0:
        print(f"No {collection_desc} found needing embeddings for field '{embedding_field_name}'. All set!")
        return

    print(f"Found {total_docs_to_process} {collection_desc} to embed for field '{embedding_field_name}'.")
    doc_cursor = collection.find(query)
    operations = []
    processed_count = 0
    start_time = time.time()

    for doc in tqdm(doc_cursor, total=total_docs_to_process, desc=f"Generating {collection_desc} Embeddings"):
        doc_id = doc.get('_id')
        if not doc_id:
            print(f"Skipping {collection_desc} document with no _id.")
            continue

        text_to_embed = text_generation_func(doc)
        embedding_vector = []
        if text_to_embed:
            try:
                embedding_vector = e_model.encode(text_to_embed).tolist()
            except Exception as e:
                print(f"Error encoding text for {collection_desc} _id {doc_id}: {e}")
        
        operations.append(
            pymongo.UpdateOne({"_id": doc_id}, {"$set": {embedding_field_name: embedding_vector}})
        )

        if len(operations) >= BATCH_SIZE:
            try:
                collection.bulk_write(operations)
                processed_count += len(operations)
                operations = []
            except pymongo.errors.BulkWriteError as bwe:
                print(f"MongoDB Bulk Write Error for {collection_desc}: {bwe.details}")
            except Exception as e:
                print(f"Error during bulk write for {collection_desc}: {e}")

    if operations:
        try:
            collection.bulk_write(operations)
            processed_count += len(operations)
        except pymongo.errors.BulkWriteError as bwe:
            print(f"MongoDB Bulk Write Error for {collection_desc} (final): {bwe.details}")
        except Exception as e:
            print(f"Error during final bulk write for {collection_desc}: {e}")

    end_time = time.time()
    print(f"\n{collection_desc} embedding generation complete.")
    print(f"Processed and updated {processed_count} {collection_desc} in {end_time - start_time:.2f} seconds.")

    print(f"\nVerifying a few {collection_desc} embeddings...")
    sample_embedded_docs = collection.find({embedding_field_name: {"$exists": True, "$ne": []}}).limit(3)
    for r_doc in sample_embedded_docs:
        id_val = r_doc.get('RecipeId') if collection_desc == "Recipes" else r_doc.get('ReviewId', r_doc.get('_id'))
        name_val = r_doc.get('Name') if collection_desc == "Recipes" else r_doc.get('Review', '')[:50] + '...'
        print(f"{collection_desc[:-1]} ID: {id_val}, Preview: {name_val}, Embedding (first 3 dims): {r_doc.get(embedding_field_name, [])[:3]}...")

# --- Main Execution ---
def main():
    # Process Recipes
    recipes_collection = get_mongodb_collection('RECIPES_COLLECTION', 'recipes')
    process_collection_embeddings(
        recipes_collection, 
        RECIPE_EMBEDDING_FIELD, 
        generate_text_for_recipe_embedding, 
        "Recipes"
    )

    print("\n" + "-"*50 + "\n") # Separator

    # Process Reviews
    reviews_collection = get_mongodb_collection('REVIEWS_COLLECTION', 'reviews')
    process_collection_embeddings(
        reviews_collection, 
        REVIEW_EMBEDDING_FIELD, 
        generate_text_for_review_embedding,
        "Reviews"
    )

if __name__ == "__main__":
    main() 