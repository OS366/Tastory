import os
from dotenv import load_dotenv
import pymongo
from tqdm import tqdm
import time
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import numpy as np

# Load environment variables
load_dotenv()

# --- Configuration ---
BATCH_SIZE = 100  # Number of documents to update in MongoDB at a time
SOURCE_COLLECTION = 'recipes'  # Source collection name
TARGET_COLLECTION = 'recipes_google_v2'  # Target collection name with version
MAX_TOKENS_PER_REQUEST = 10000  # Much more conservative limit
MAX_CHARS_PER_TEXT = 5000  # Maximum characters per individual text
CHARS_PER_TOKEN = 3  # More conservative estimate (was 4)

# --- Recipes Configuration ---
RECIPE_EMBEDDING_FIELD = 'recipe_embedding_google_vertex'
RECIPE_FIELDS_TO_EMBED = ['Name', 'Description', 'Keywords', 'RecipeIngredientParts', 'RecipeInstructions']

# --- Cost Configuration ---
COST_PER_1K_CHARS = 0.000025  # $0.000025 per 1,000 characters for online requests

def estimate_text_length(text):
    """Estimate the number of characters in the text."""
    if not text:
        return 0
    if isinstance(text, list):
        return sum(len(str(item)) for item in text if item)
    return len(str(text))

def estimate_cost(collection):
    """Estimate the cost of generating embeddings for the collection."""
    print("\n=== Cost Estimation ===")
    
    # Get documents that need embeddings
    query = {
        "$or": [
            {RECIPE_EMBEDDING_FIELD: {"$exists": False}},
            {RECIPE_EMBEDDING_FIELD: []}
        ]
    }
    total_docs = collection.count_documents(query)
    
    if total_docs == 0:
        print("No documents need embeddings.")
        return 0
        
    # Sample 100 documents to estimate average character count
    sample_size = min(100, total_docs)
    sample_docs = collection.find(query).limit(sample_size)
    
    total_chars = 0
    for doc in sample_docs:
        for field in RECIPE_FIELDS_TO_EMBED:
            total_chars += estimate_text_length(doc.get(field))
    
    avg_chars_per_doc = total_chars / sample_size
    total_estimated_chars = avg_chars_per_doc * total_docs
    
    # Calculate cost
    estimated_cost = (total_estimated_chars / 1000) * COST_PER_1K_CHARS
    
    print(f"Estimation based on {sample_size} sample documents:")
    print(f"- Average characters per document: {avg_chars_per_doc:.0f}")
    print(f"- Total documents to process: {total_docs:,}")
    print(f"- Total estimated characters: {total_estimated_chars:,.0f}")
    print(f"- Estimated cost: ${estimated_cost:.2f}")
    
    return estimated_cost

def track_actual_cost(total_chars):
    """Calculate the actual cost based on processed characters."""
    actual_cost = (total_chars / 1000) * COST_PER_1K_CHARS
    return actual_cost

# Initialize Vertex AI
def init_vertex_ai():
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
            
        aiplatform.init(project=project_id, location=location)
        # Use the stable English model
        model = TextEmbeddingModel.from_pretrained("text-embedding-005")
        print("Successfully initialized Vertex AI")
        return model
    except Exception as e:
        print(f"Error initializing Vertex AI: {e}")
        return None

# --- MongoDB Connection Utility ---
def get_mongodb_connection():
    mongodb_uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('DB_NAME', 'tastory')

    if not mongodb_uri:
        print("MongoDB URI not found in .env file.")
        return None, None

    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command('ping')
        db = client[db_name]
        print(f"Successfully connected to MongoDB: {db_name}")
        return client, db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None, None

def copy_recipes_to_new_collection(db):
    """Copy recipes from source collection to target collection."""
    try:
        print("\n=== Starting Recipe Copy Process ===")
        # Check if target collection exists
        if TARGET_COLLECTION in db.list_collection_names():
            target_count = db[TARGET_COLLECTION].count_documents({})
            print(f"Collection '{TARGET_COLLECTION}' already exists with {target_count} documents.")
            print("Skipping copy process and proceeding with embedding generation.")
            return db[TARGET_COLLECTION]
        
        # Get source collection
        source_collection = db[SOURCE_COLLECTION]
        target_collection = db[TARGET_COLLECTION]
        
        # Copy documents
        docs_to_copy = source_collection.find({})
        total_docs = source_collection.count_documents({})
        
        if total_docs == 0:
            print("No documents found in source collection.")
            return None
            
        print(f"Starting to copy {total_docs} documents from '{SOURCE_COLLECTION}' to '{TARGET_COLLECTION}'...")
        
        # Copy in batches
        operations = []
        copied_count = 0
        for doc in tqdm(docs_to_copy, total=total_docs, desc="Copying recipes"):
            operations.append(pymongo.InsertOne(doc))
            
            if len(operations) >= BATCH_SIZE:
                result = target_collection.bulk_write(operations, ordered=False)
                copied_count += len(operations)
                print(f"\rCopied {copied_count}/{total_docs} documents...", end="")
                operations = []
        
        if operations:
            result = target_collection.bulk_write(operations, ordered=False)
            copied_count += len(operations)
        
        print(f"\nSuccessfully copied {copied_count} documents to '{TARGET_COLLECTION}'")
        
        # Create index on RecipeId
        print("Creating index on RecipeId...")
        target_collection.create_index("RecipeId", unique=True)
        
        print("=== Recipe Copy Process Complete ===\n")
        return target_collection
        
    except Exception as e:
        print(f"Error copying recipes: {e}")
        return None

def truncate_text(text, max_length=MAX_CHARS_PER_TEXT):
    """Truncate text to a maximum length while preserving complete sentences."""
    if not text:
        return text
        
    # First, roughly estimate tokens
    estimated_tokens = len(text) // CHARS_PER_TOKEN
    if estimated_tokens > MAX_TOKENS_PER_REQUEST:
        # If text might exceed token limit, apply stricter truncation
        max_length = min(max_length, MAX_TOKENS_PER_REQUEST * CHARS_PER_TOKEN)
    
    if len(text) <= max_length:
        return text
        
    # Try to truncate at the last sentence before max_length
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    if last_period > 0:
        return truncated[:last_period + 1]
    return truncated

def generate_text_for_recipe_embedding(recipe_doc):
    """Generate text for embedding with length limits."""
    texts_to_join = []
    total_length = 0
    
    # Process each field with limits
    for field in RECIPE_FIELDS_TO_EMBED:
        content = recipe_doc.get(field)
        if content:
            if isinstance(content, list):
                # For lists, join items and truncate the result
                text = " . ".join(str(item) for item in content if item)
                truncated = truncate_text(text)
            elif isinstance(content, str):
                truncated = truncate_text(content)
            else:
                continue
                
            # Check if adding this field would exceed limits
            if total_length + len(truncated) > MAX_CHARS_PER_TEXT:
                # If it would exceed, skip this field
                continue
                
            texts_to_join.append(truncated)
            total_length += len(truncated)
    
    # Join all fields
    full_text = " . ".join(texts_to_join).strip()
    
    # Final safety truncation
    return truncate_text(full_text)

def estimate_tokens(text):
    """Estimate the number of tokens in a text."""
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN + 1  # Add 1 for safety

# --- Embedding Generation Function ---
def process_recipes_embeddings(collection, model):
    if model is None:
        print("Vertex AI model not initialized. Skipping collection.")
        return
    if collection is None:
        print("MongoDB collection not available. Skipping.")
        return

    # Estimate cost before processing
    estimated_cost = estimate_cost(collection)
    if estimated_cost > 10:  # Add a warning for costs over $10
        proceed = input(f"\nWarning: Estimated cost is ${estimated_cost:.2f}. Do you want to proceed? (y/n): ")
        if proceed.lower() != 'y':
            print("Operation cancelled by user.")
            return

    print("\n=== Starting Embedding Generation Process ===")
    query = {
        "$or": [
            {RECIPE_EMBEDDING_FIELD: {"$exists": False}},
            {RECIPE_EMBEDDING_FIELD: []}
        ]
    }
    total_docs_to_process = collection.count_documents(query)

    if total_docs_to_process == 0:
        print(f"No recipes found needing embeddings for field '{RECIPE_EMBEDDING_FIELD}'. All set!")
        return

    print(f"Found {total_docs_to_process} recipes that need embeddings.")
    doc_cursor = collection.find(query)
    operations = []
    processed_count = 0
    error_count = 0
    start_time = time.time()
    total_chars_processed = 0
    
    # Process in batches
    batch_docs = []
    batch_texts = []
    current_batch_tokens = 0
    
    for doc in tqdm(doc_cursor, total=total_docs_to_process, desc="Processing Recipes"):
        doc_id = doc.get('_id')
        if not doc_id:
            continue

        text_to_embed = generate_text_for_recipe_embedding(doc)
        if not text_to_embed:
            continue
            
        # Estimate tokens
        estimated_tokens = estimate_tokens(text_to_embed)
        
        # If this single text exceeds token limit, skip it
        if estimated_tokens > MAX_TOKENS_PER_REQUEST:
            print(f"\nSkipping document {doc_id} - text too long ({estimated_tokens} estimated tokens)")
            continue
        
        # If adding this text would exceed token limit, process current batch first
        if current_batch_tokens + estimated_tokens > MAX_TOKENS_PER_REQUEST and batch_texts:
            try:
                # Process current batch
                responses = model.get_embeddings(batch_texts)
                
                # Handle responses and create operations
                for idx, response in enumerate(responses):
                    if hasattr(response, 'values') and response.values:
                        doc = batch_docs[idx]
                        operations.append(
                            pymongo.UpdateOne(
                                {"_id": doc['_id']},
                                {"$set": {RECIPE_EMBEDDING_FIELD: response.values}},
                                upsert=False
                            )
                        )
                    else:
                        error_count += 1
                
                # Write to database
                if operations:
                    result = collection.bulk_write(operations)
                    processed_count += result.modified_count
                    current_cost = track_actual_cost(total_chars_processed)
                    print(f"\rProcessed {processed_count}/{total_docs_to_process} recipes. Cost so far: ${current_cost:.2f}", end="")
                
                # Clear batches
                batch_docs = []
                batch_texts = []
                operations = []
                current_batch_tokens = 0
                
            except Exception as e:
                error_count += len(batch_texts)
                print(f"\nError processing batch: {e}")
                if error_count >= 50:  # Stop if too many errors
                    print("\nToo many errors encountered. Stopping embedding generation.")
                    break
                # Clear batches on error
                batch_docs = []
                batch_texts = []
                operations = []
                current_batch_tokens = 0
        
        # Add document to current batch
        total_chars_processed += len(text_to_embed)
        batch_docs.append(doc)
        batch_texts.append(text_to_embed)
        current_batch_tokens += estimated_tokens
        
        # If batch is full by count, process it
        if len(batch_texts) >= BATCH_SIZE:
            try:
                # Process current batch
                responses = model.get_embeddings(batch_texts)
                
                # Handle responses and create operations
                for idx, response in enumerate(responses):
                    if hasattr(response, 'values') and response.values:
                        doc = batch_docs[idx]
                        operations.append(
                            pymongo.UpdateOne(
                                {"_id": doc['_id']},
                                {"$set": {RECIPE_EMBEDDING_FIELD: response.values}},
                                upsert=False
                            )
                        )
                    else:
                        error_count += 1
                
                # Write to database
                if operations:
                    result = collection.bulk_write(operations)
                    processed_count += result.modified_count
                    current_cost = track_actual_cost(total_chars_processed)
                    print(f"\rProcessed {processed_count}/{total_docs_to_process} recipes. Cost so far: ${current_cost:.2f}", end="")
                
                # Clear batches
                batch_docs = []
                batch_texts = []
                operations = []
                current_batch_tokens = 0
                
            except Exception as e:
                error_count += len(batch_texts)
                print(f"\nError processing batch: {e}")
                if error_count >= 50:
                    print("\nToo many errors encountered. Stopping embedding generation.")
                    break
                batch_docs = []
                batch_texts = []
                operations = []
                current_batch_tokens = 0

    # Process final batch
    if batch_texts:
        try:
            # Final safety check on token count
            total_tokens = sum(estimate_tokens(text) for text in batch_texts)
            if total_tokens > MAX_TOKENS_PER_REQUEST:
                print("\nSkipping final batch - total tokens too high")
            else:
                responses = model.get_embeddings(batch_texts)
                
                for idx, response in enumerate(responses):
                    if hasattr(response, 'values') and response.values:
                        doc = batch_docs[idx]
                        operations.append(
                            pymongo.UpdateOne(
                                {"_id": doc['_id']},
                                {"$set": {RECIPE_EMBEDDING_FIELD: response.values}},
                                upsert=False
                            )
                        )
                    else:
                        error_count += 1
                
                if operations:
                    result = collection.bulk_write(operations)
                    processed_count += result.modified_count
                    print(f"\nFinal batch: processed {result.modified_count} documents")
            
        except Exception as e:
            error_count += len(batch_texts)
            print(f"\nError processing final batch: {e}")

    end_time = time.time()
    duration = end_time - start_time
    final_cost = track_actual_cost(total_chars_processed)
    
    print(f"\n\nEmbedding generation complete:")
    print(f"- Processed {processed_count} recipes in {duration:.2f} seconds")
    avg_time = duration/processed_count if processed_count > 0 else 0
    print(f"- Average time per recipe: {avg_time:.2f} seconds")
    print(f"- Average time per batch: {(duration/processed_count * BATCH_SIZE):.2f} seconds")
    print(f"- Total characters processed: {total_chars_processed:,}")
    print(f"- Final cost: ${final_cost:.2f}")
    print(f"- Encountered {error_count} errors")

    print("\nVerifying a few recipe embeddings...")
    sample_embedded_docs = collection.find({
        RECIPE_EMBEDDING_FIELD: {"$exists": True, "$ne": []}
    }).limit(3)
    
    for doc in sample_embedded_docs:
        embedding = doc.get(RECIPE_EMBEDDING_FIELD, [])
        print(f"\nRecipe ID: {doc.get('RecipeId')}")
        print(f"Name: {doc.get('Name')}")
        print(f"Embedding length: {len(embedding)}")

    print("\n=== Embedding Generation Process Complete ===\n")

def verify_embeddings(collection):
    """Verify that embeddings are being saved correctly."""
    print("\n=== Verifying Embeddings ===")
    
    # Check total documents
    total_docs = collection.count_documents({})
    print(f"Total documents in collection: {total_docs}")
    
    # Check documents with embeddings
    docs_with_embeddings = collection.count_documents({
        RECIPE_EMBEDDING_FIELD: {"$exists": True, "$ne": []}
    })
    print(f"Documents with embeddings: {docs_with_embeddings}")
    
    # Check a few random documents with embeddings
    print("\nSample documents with embeddings:")
    sample_docs = collection.find({
        RECIPE_EMBEDDING_FIELD: {"$exists": True, "$ne": []}
    }).limit(3)
    
    for doc in sample_docs:
        embedding = doc.get(RECIPE_EMBEDDING_FIELD, [])
        print(f"\nRecipe ID: {doc.get('RecipeId')}")
        print(f"Name: {doc.get('Name')}")
        print(f"Embedding length: {len(embedding)}")
    
    print("\n=== Verification Complete ===")

def main():
    # Initialize Vertex AI
    model = init_vertex_ai()
    if model is None:
        print("Failed to initialize Vertex AI. Exiting.")
        return

    # Connect to MongoDB
    client, db = get_mongodb_connection()
    if db is None:
        print("Failed to connect to MongoDB. Exiting.")
        return

    # Copy recipes to new collection
    target_collection = copy_recipes_to_new_collection(db)
    if target_collection is None:
        print("Failed to prepare target collection. Exiting.")
        return

    # Process Recipes
    process_recipes_embeddings(target_collection, model)
    
    # Verify embeddings
    verify_embeddings(target_collection)

    # Close MongoDB connection
    client.close()

if __name__ == "__main__":
    main() 