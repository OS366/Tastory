import os
from dotenv import load_dotenv
import pymongo

# Load environment variables
load_dotenv()

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

def verify_embeddings():
    """Verify the current state of embeddings in the database."""
    client, db = get_mongodb_connection()
    if db is None:
        return
        
    collection = db['recipes_google_v2']
    
    # Get total counts
    total_docs = collection.count_documents({})
    docs_with_google_embeddings = collection.count_documents({
        'recipe_embedding_google_vertex': {"$exists": True, "$ne": []}
    })
    docs_with_minilm_embeddings = collection.count_documents({
        'recipe_embedding_all_MiniLM_L6_v2': {"$exists": True, "$ne": []}
    })
    
    print("\n=== Embedding Statistics ===")
    print(f"Total documents: {total_docs}")
    print(f"Documents with Google embeddings: {docs_with_google_embeddings}")
    print(f"Documents with MiniLM embeddings: {docs_with_minilm_embeddings}")
    
    # Check a sample document with both embeddings
    print("\n=== Sample Document ===")
    sample_doc = collection.find_one({
        'recipe_embedding_google_vertex': {"$exists": True},
        'recipe_embedding_all_MiniLM_L6_v2': {"$exists": True}
    })
    
    if sample_doc:
        print(f"Recipe ID: {sample_doc.get('RecipeId')}")
        print(f"Name: {sample_doc.get('Name')}")
        google_embedding = sample_doc.get('recipe_embedding_google_vertex', [])
        minilm_embedding = sample_doc.get('recipe_embedding_all_MiniLM_L6_v2', [])
        print(f"Google embedding length: {len(google_embedding)}")
        print(f"MiniLM embedding length: {len(minilm_embedding)}")
        if google_embedding:
            print(f"Google embedding first 3 dims: {google_embedding[:3]}")
        if minilm_embedding:
            print(f"MiniLM embedding first 3 dims: {minilm_embedding[:3]}")
    else:
        print("No document found with both embeddings")
    
    client.close()

if __name__ == "__main__":
    verify_embeddings() 