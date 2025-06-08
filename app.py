import json
import logging
import math
import os
import re
import urllib.parse
import uuid
from datetime import datetime, timedelta

import pymongo
import requests
import stripe
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import our nutritional database
try:
    from nutritional_database import calculate_recipe_calories

    NUTRITIONAL_DB_AVAILABLE = True
except ImportError:
    print("Warning: nutritional_database module not available. Calorie calculation will be disabled.")
    NUTRITIONAL_DB_AVAILABLE = False

    def calculate_recipe_calories(*args, **kwargs):
        return None

# Google Vertex AI imports for embeddings
try:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("Warning: Vertex AI not available. Install with: pip install google-cloud-aiplatform vertexai")


app = Flask(__name__)
CORS(app)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# --- Vertex AI Configuration ---
vertex_model = None

def init_vertex_ai():
    """Initialize Vertex AI for embeddings"""
    global vertex_model
    if not VERTEX_AI_AVAILABLE:
        return None
    
    try:
        load_dotenv()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "tastory-404614")
        location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Load the text embedding model
        vertex_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        print("Successfully initialized Vertex AI with textembedding-gecko@003")
        return vertex_model
    except Exception as e:
        print(f"Error initializing Vertex AI: {e}")
        return None

def generate_query_embedding(query_text):
    """Generate embedding for search query using Vertex AI"""
    global vertex_model
    
    if not vertex_model:
        vertex_model = init_vertex_ai()
    
    if not vertex_model:
        return None
        
    try:
        # Generate embedding
        embeddings = vertex_model.get_embeddings([query_text])
        if embeddings and len(embeddings) > 0:
            return embeddings[0].values
        return None
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None


# --- MongoDB Connection ---
def connect_to_mongodb():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("MongoDB URI not found. Please set it in your .env file.")
        return None, None
    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command("ping")
        db_name = os.getenv("DB_NAME", "tastory")
        db = client[db_name]
        print("Successfully connected to MongoDB and pinged the server.")
        return client, db
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB connection: {e}")
        return None, None


# MongoDB connection - will be established lazily when needed
client, db = None, None


def ensure_mongodb_connection():
    """Ensure MongoDB connection is established, connecting if needed"""
    global client, db
    if db is None:
        client, db = connect_to_mongodb()
    return client, db

def vector_search_recipes(query_embedding, limit=30):
    """Perform vector similarity search using Vertex AI embeddings"""
    client, db = ensure_mongodb_connection()
    if db is None or not query_embedding:
        return []
    
    try:
        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
        
        # MongoDB Atlas Vector Search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "recipe_embedding_index",  # Vector search index name
                    "path": "recipe_embedding_google_vertex",  # Field containing embeddings
                    "queryVector": query_embedding,
                    "numCandidates": 100,  # Number of candidates to consider
                    "limit": limit
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "RecipeId": 1,
                    "Name": 1,
                    "Description": 1,
                    "RecipeIngredientParts": 1,
                    "RecipeIngredientQuantities": 1,
                    "RecipeInstructions": 1,
                    "Images": 1,
                    "MainImage": 1,
                    "Calories": 1,
                    "AuthorName": 1,
                    "DatePublished": 1,
                    "RecipeServings": 1,
                    "RecipeYield": 1,
                    "PrepTime": 1,
                    "RecipeCategory": 1,
                    "FatContent": 1,
                    "SaturatedFatContent": 1,
                    "CholesterolContent": 1,
                    "SodiumContent": 1,
                    "CarbohydrateContent": 1,
                    "FiberContent": 1,
                    "SugarContent": 1,
                    "ProteinContent": 1,
                    "AggregatedRating": 1,
                    "ReviewCount": 1,
                    "score": {"$meta": "vectorSearchScore"}  # Include similarity score
                }
            }
        ]
        
        results = list(recipes_collection.aggregate(pipeline))
        print(f"Vector search found {len(results)} results")
        return results
        
    except Exception as e:
        print(f"Error in vector search: {e}")
        # Fallback to empty results rather than crashing
        return []


# --- Helper function to create a URL slug ---
def slugify(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\\s+", "-", text)
    text = re.sub(r"[^a-z0-9\\-]", "", text)
    text = re.sub(r"--+", "-", text)
    text = text.strip("-")
    return text


# --- Helper function to generate star rating HTML ---
def generate_star_rating(rating):
    """Generate HTML for star rating display"""
    if rating is None:
        return '<span class="text-sm text-gray-400">No rating</span>'

    try:
        rating_float = float(rating)
    except (ValueError, TypeError):
        return '<span class="text-sm text-gray-400">No rating</span>'

    # Ensure rating is between 0 and 5
    rating_float = max(0, min(5, rating_float))

    # Calculate filled and half stars
    full_stars = int(rating_float)
    has_half_star = (rating_float - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

    stars_html = '<span class="inline-flex items-center">'

    # Add full stars
    for _ in range(full_stars):
        stars_html += '<i class="fas fa-star text-gold-500"></i>'

    # Add half star if needed
    if has_half_star:
        stars_html += '<i class="fas fa-star-half-alt text-gold-500"></i>'

    # Add empty stars
    for _ in range(empty_stars):
        stars_html += '<i class="far fa-star text-gold-500/50"></i>'

    stars_html += "</span>"
    return stars_html


# --- Helper function to estimate serving sizes for recipes with missing data ---
def estimate_serving_size(recipe_name):
    """Estimate reasonable serving size based on recipe name patterns"""
    if not recipe_name:
        return 4

    recipe_name_lower = recipe_name.lower()

    if any(word in recipe_name_lower for word in ["fondue", "soup", "stew", "casserole", "dip"]):
        return 6  # Party/sharing dishes typically serve 6
    elif any(word in recipe_name_lower for word in ["cake", "pie", "bread", "loaf"]):
        return 8  # Baked goods typically serve 8
    elif any(word in recipe_name_lower for word in ["salad", "side"]):
        return 4  # Side dishes typically serve 4
    else:
        return 4  # Default conservative estimate


def safe_get_servings(recipe):
    """Safely extract servings count from recipe, handling string/int conversion"""
    servings = recipe.get("RecipeServings") or recipe.get("RecipeYield") or estimate_serving_size(recipe.get("Name"))
    # Convert to int and ensure at least 1 serving
    try:
        return max(1, int(servings))
    except (ValueError, TypeError):
        return estimate_serving_size(recipe.get("Name"))


def get_top_review(reviews_collection, recipe_id):
    """Get the top-rated review for a recipe"""
    try:
        # Convert recipe_id to int for matching (reviews collection uses int RecipeId)
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            print(f"Invalid recipe_id format: {recipe_id}")
            return None

        # Find reviews for this recipe, sorted by rating (desc), then by review length (desc) for quality
        top_review = reviews_collection.find_one(
            {"RecipeId": recipe_id_int, "Rating": {"$exists": True}, "Review": {"$exists": True, "$ne": ""}},
            sort=[("Rating", -1), ("ReviewLength", -1)],
        )

        if top_review:
            return {
                "rating": top_review.get("Rating"),
                "text": top_review.get("Review"),
                "author": top_review.get("AuthorName", "Anonymous"),
                "date": top_review.get("DateSubmitted", "").split("T")[0] if top_review.get("DateSubmitted") else None,
            }
        return None
    except Exception as e:
        print(f"Error fetching top review for recipe {recipe_id}: {e}")
        return None


# --- Helper function to log search queries ---
def log_search_query(query, session_id, results_count=None):
    """Log search queries for trending calculation"""
    client, db = ensure_mongodb_connection()
    if db is None:
        return

    try:
        search_logs = db.search_logs
        log_entry = {
            "query": query.lower().strip(),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "results_count": results_count,
        }
        search_logs.insert_one(log_entry)
    except Exception as e:
        print(f"Error logging search query: {e}")


# --- Helper function to calculate trending searches ---
def calculate_trending_searches():
    """Calculate trending searches based on recent activity"""
    client, db = ensure_mongodb_connection()
    if db is None:
        return []

    try:
        search_logs = db.search_logs

        # Time windows
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        six_hours_ago = now - timedelta(hours=6)
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Aggregation pipeline
        pipeline = [
            {"$match": {"timestamp": {"$gte": twenty_four_hours_ago}}},
            {
                "$group": {
                    "_id": "$query",
                    "total_count": {"$sum": 1},
                    "recent_count": {"$sum": {"$cond": [{"$gte": ["$timestamp", one_hour_ago]}, 1, 0]}},
                    "medium_count": {"$sum": {"$cond": [{"$gte": ["$timestamp", six_hours_ago]}, 1, 0]}},
                }
            },
            {"$match": {"total_count": {"$gte": 2}}},  # Lowered from 5 to 2 searches to qualify
            {
                "$addFields": {
                    "score": {
                        "$divide": [
                            {
                                "$add": [
                                    {"$multiply": ["$recent_count", 3]},
                                    {"$multiply": ["$medium_count", 2]},
                                    "$total_count",
                                ]
                            },
                            2,  # time decay factor
                        ]
                    }
                }
            },
            {"$sort": {"score": -1}},
            {"$limit": 10},
            {"$project": {"_id": 0, "query": "$_id", "count": "$total_count", "score": 1}},
        ]

        trending = list(search_logs.aggregate(pipeline))

        # If no trending searches, fallback to most recent unique searches
        if not trending:
            fallback_pipeline = [
                {"$match": {"timestamp": {"$gte": twenty_four_hours_ago}}},
                {"$group": {"_id": "$query", "count": {"$sum": 1}, "latest": {"$max": "$timestamp"}}},
                {"$sort": {"count": -1, "latest": -1}},
                {"$limit": 5},
                {"$project": {"_id": 0, "query": "$_id", "count": "$count", "score": "$count"}},
            ]
            trending = list(search_logs.aggregate(fallback_pipeline))

        # Calculate trend direction
        for item in trending:
            # This is simplified - in production, you'd compare with previous period
            if item.get("score", 0) > 5:  # Lowered threshold
                item["trend"] = "up"
            else:
                item["trend"] = "stable"
            item["percentChange"] = 0  # Placeholder

        return trending

    except Exception as e:
        print(f"Error calculating trending searches: {e}")
        return []


@app.route("/")
def index():
    return jsonify(
        {
            "name": "Tastory API",
            "tagline": "The Food Search Engine",
            "version": "1.1.0",
            "endpoints": {
                "/chat": "Search for recipes using natural language",
                "/suggest": "Get search suggestions as you type",
                "/trending": "Get trending recipe searches",
                "/health": "Health check endpoint",
            },
            "stats": {"total_recipes": "230,000+", "response_time": "<2s", "languages_supported": 6},
        }
    )


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 200

    # Get the user message and pagination info
    data = request.get_json()
    user_message = data.get("message") or data.get("query", "")  # Handle both formats
    user_message = user_message.strip()
    page = data.get("page", 1)
    per_page = 12  # Fixed at 12 for 4x3 grid

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Log the search query
    try:
        session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
        log_search_query(user_message, session_id, results_count=None)
    except Exception as e:
        print(f"Failed to log search query: {e}")

    # Ensure database connection
    client, db = ensure_mongodb_connection()
    if db is None:
        return jsonify({"reply": "Error: Could not connect to the database. Please check server logs."}), 500

    try:
        # Check for spell corrections
        spell_check = spell_correct_query(user_message)
        original_query = spell_check["original"]
        corrected_query = spell_check["corrected"]
        has_corrections = spell_check["has_corrections"]

        # Try exact text search first
        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
        reviews_collection = db[os.getenv("REVIEWS_COLLECTION", "reviews")]

        # Use corrected query if available, otherwise use original
        search_query_text = corrected_query if has_corrections else user_message

        # Split the query into words for exact matching
        search_terms = search_query_text.lower().split()

        # Define cuisine categories and their related terms
        cuisine_categories = {
            "indian": [
                "indian",
                "chole",
                "puri",
                "curry",
                "masala",
                "naan",
                "roti",
                "biryani",
                "samosa",
                "pav bhaji",
                "bhaji",
                "pav",
                "dal",
                "tandoori",
                "tikka",
                "paneer",
                "dosa",
                "idli",
                "vada",
                "uttapam",
                "rajma",
                "palak",
                "saag",
                "aloo",
                "gobi",
                "matar",
                "jeera",
                "garam masala",
                "turmeric",
                "cumin",
                "cardamom",
                "coriander",
                "fenugreek",
                "chapati",
                "paratha",
                "kulcha",
                "bhatura",
                "rasam",
                "sambar",
                "chutney",
                "lassi",
                "kulfi",
                "gulab jamun",
                "rasgulla",
                "kheer",
                "halwa",
            ],
            "italian": ["italian", "pasta", "pizza", "risotto", "lasagna", "spaghetti", "marinara", "pesto"],
            "dessert": ["dessert", "ice cream", "cake", "pie", "cookie", "chocolate", "sweet", "pudding"],
            "chinese": ["chinese", "noodles", "fried rice", "dimsum", "spring roll", "wonton", "chow mein"],
            "mexican": ["mexican", "taco", "burrito", "enchilada", "quesadilla", "salsa", "guacamole"],
        }

        # Detect cuisine from query - improved logic for multi-word terms
        query_terms = user_message.lower().split()
        detected_cuisine = None
        original_query_lower = user_message.lower()

        for cuisine, terms in cuisine_categories.items():
            # Check both individual words and the full query for multi-word terms
            cuisine_match = False

            # Check if any cuisine term appears in the original query
            for term in terms:
                if term in original_query_lower:
                    cuisine_match = True
                break

            # Also check if any search term matches any cuisine term
            if not cuisine_match:
                for search_term in query_terms:
                    if any(search_term in term.lower() for term in terms):
                        cuisine_match = True
                        break

            if cuisine_match:
                detected_cuisine = cuisine
                break

        # Try Vector Search first (if Vertex AI is available)
        results = []
        use_vertex_search = os.getenv("USE_VERTEX_SEARCH", "true").lower() == "true"
        
        if use_vertex_search and VERTEX_AI_AVAILABLE:
            print(f"Attempting Vertex AI vector search for: '{search_query_text}'")
            query_embedding = generate_query_embedding(search_query_text)
            
            if query_embedding:
                results = vector_search_recipes(query_embedding, limit=30)
                print(f"Vector search returned {len(results)} results")
            else:
                print("Failed to generate query embedding, falling back to text search")
        
        # Fallback to regex-based text search if vector search fails or is disabled
        if not results:
            print("Using fallback text search")
            # Build search conditions that work for any query
            search_conditions = []

            # For each term in the user's query, search across multiple fields
            for term in search_terms:
                term_conditions = {
                    "$or": [
                        {"Name": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                        {"RecipeCategory": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                        {"Keywords": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                        {"RecipeIngredientParts": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                        {"Description": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                    ]
                }
                search_conditions.append(term_conditions)

            # Create final search query - must match at least one term
            if search_conditions:
                search_query = {"$or": search_conditions}
            else:
                # Fallback for empty search
                search_query = {}

            # Execute fallback search
            results = list(
                recipes_collection.find(
                    search_query,
                    {
                        "_id": 0,
                        "RecipeId": 1,
                        "Name": 1,
                        "Description": 1,
                        "RecipeIngredientParts": 1,
                        "RecipeIngredientQuantities": 1,
                        "RecipeInstructions": 1,
                        "Images": 1,
                        "MainImage": 1,
                        "Calories": 1,
                        "AuthorName": 1,
                        "DatePublished": 1,
                        "RecipeServings": 1,
                        "RecipeYield": 1,
                        "PrepTime": 1,
                        "RecipeCategory": 1,
                        "FatContent": 1,
                        "SaturatedFatContent": 1,
                        "CholesterolContent": 1,
                        "SodiumContent": 1,
                        "CarbohydrateContent": 1,
                        "FiberContent": 1,
                        "SugarContent": 1,
                        "ProteinContent": 1,
                        "AggregatedRating": 1,
                        "ReviewCount": 1,
                    },
                ).limit(30)
            )

        # Process results
        recipes_with_images = []
        recipes_without_images = []

        for recipe in results:
            has_image = False
            main_image = recipe.get("MainImage")
            images = recipe.get("Images", [])

            if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
                has_image = True
            elif images and isinstance(images, list) and len(images) > 0:
                if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                    has_image = True

            if has_image:
                recipes_with_images.append(recipe)
            else:
                recipes_without_images.append(recipe)

        # Combine results with images first
        sorted_results = recipes_with_images + recipes_without_images

        # Calculate pagination
        total_results = len(sorted_results)
        total_pages = max(1, min(3, math.ceil(total_results / per_page)))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = sorted_results[start_idx:end_idx]

        # Update search log with results count
        try:
            session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
            # Update the log entry with results count
            if db is not None:
                db.search_logs.update_one(
                    {"session_id": session_id, "query": user_message.lower().strip()},
                    {"$set": {"results_count": total_results}},
                    upsert=False,
                )
        except Exception as e:
            print(f"Failed to update search log with results count: {e}")

        # Format results
        recipes_data = []
        for recipe in page_results:
            # Extract image URL - check for existing images first
            image_url = None
            main_image = recipe.get("MainImage")
            images = recipe.get("Images", [])

            if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
                image_url = main_image.strip()
            elif images and isinstance(images, list) and len(images) > 0:
                if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                    image_url = images[0].strip()

            # Process ingredients - combine names with quantities
            ingredients = []
            ingredients_data = recipe.get("RecipeIngredientParts")
            quantities_data = recipe.get("RecipeIngredientQuantities")

            # Parse ingredient names
            ingredient_names = []
            if isinstance(ingredients_data, list):
                for item in ingredients_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    ingredient_names.extend([str(ing).strip() for ing in parsed if ing])
                                else:
                                    ingredient_names.append(str(item).strip())
                            else:
                                ingredient_names.append(str(item).strip())
                        except json.JSONDecodeError:
                            ingredient_names.append(str(item).strip())
                    elif item:
                        ingredient_names.append(str(item).strip())
            elif isinstance(ingredients_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if ingredients_data.strip().startswith("[") and ingredients_data.strip().endswith("]"):
                        parsed = json.loads(ingredients_data)
                        if isinstance(parsed, list):
                            ingredient_names.extend([str(ing).strip() for ing in parsed if ing])
                        else:
                            ingredient_names.append(ingredients_data.strip())
                    else:
                        ingredient_names.append(ingredients_data.strip())
                except json.JSONDecodeError:
                    ingredient_names.append(ingredients_data.strip())

            # Parse quantities
            quantities = []
            if isinstance(quantities_data, list):
                for item in quantities_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    quantities.extend([str(qty).strip() for qty in parsed if qty])
                                else:
                                    quantities.append(str(item).strip())
                            else:
                                quantities.append(str(item).strip())
                        except json.JSONDecodeError:
                            quantities.append(str(item).strip())
                    elif item:
                        quantities.append(str(item).strip())
            elif isinstance(quantities_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if quantities_data.strip().startswith("[") and quantities_data.strip().endswith("]"):
                        parsed = json.loads(quantities_data)
                        if isinstance(parsed, list):
                            quantities.extend([str(qty).strip() for qty in parsed if qty])
                        else:
                            quantities.append(quantities_data.strip())
                    else:
                        quantities.append(quantities_data.strip())
                except json.JSONDecodeError:
                    quantities.append(quantities_data.strip())

            # Combine ingredients with quantities
            for i, name in enumerate(ingredient_names):
                if i < len(quantities) and quantities[i] and quantities[i].lower() != "nan":
                    # Format: "quantity name"
                    ingredients.append(f"{quantities[i]} {name}")
                else:
                    # Just the ingredient name if no quantity available
                    ingredients.append(name)

            # If no image found, leave image_url as None (will show "no image found" in frontend)
            # Removed automatic image generation to revert to old concept

            # Process instructions - parse JSON strings properly
            instructions = []
            instructions_data = recipe.get("RecipeInstructions", [])

            if isinstance(instructions_data, list):
                for item in instructions_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    instructions.extend([str(inst).strip() for inst in parsed if inst])
                                else:
                                    instructions.append(str(item).strip())
                            else:
                                instructions.append(str(item).strip())
                        except json.JSONDecodeError:
                            instructions.append(str(item).strip())
                    elif item:
                        instructions.append(str(item).strip())
            elif isinstance(instructions_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if instructions_data.strip().startswith("[") and instructions_data.strip().endswith("]"):
                        parsed = json.loads(instructions_data)
                        if isinstance(parsed, list):
                            instructions.extend([str(inst).strip() for inst in parsed if inst])
                        else:
                            instructions.append(instructions_data.strip())
                    else:
                        instructions.append(instructions_data.strip())
                except json.JSONDecodeError:
                    instructions.append(instructions_data.strip())

            # Process calories - combine existing and calculated
            existing_calories = recipe.get("Calories")
            servings = safe_get_servings(recipe)

            # Calculate calories from ingredients
            calculated_calories = None
            try:
                ingredients_data = recipe.get("RecipeIngredientParts")
                quantities_data = recipe.get("RecipeIngredientQuantities")

                if ingredients_data and quantities_data:
                    calc_result = calculate_recipe_calories(ingredients_data, quantities_data, servings)
                    if calc_result:
                        calculated_calories = calc_result["calories_per_serving"]
            except Exception as e:
                print(f"Error calculating calories for recipe {recipe.get('RecipeId')}: {e}")

            # Determine which calorie value to display - PRIORITIZE CALCULATED CALORIES
            calories_display = "N/A"
            calorie_source = "none"

            # First try to use calculated calories (user preference)
            if calculated_calories:
                calories_display = f"{calculated_calories:.0f}"
                calorie_source = "calculated"
            # Only fall back to database calories if no calculated value
            elif existing_calories is not None:
                try:
                    existing_per_serving = float(existing_calories) / servings
                    calories_display = f"{existing_per_serving:.0f}"
                    calorie_source = "database"
                except (ValueError, TypeError, ZeroDivisionError):
                    calories_display = "N/A"
                    calorie_source = "none"

            # Calculate walkMeter
            walk_meter = calculate_walk_meter(calories_display)

            # Get top review for this recipe
            top_review = get_top_review(reviews_collection, recipe.get("RecipeId"))

            recipe_data = {
                "id": str(recipe.get("RecipeId", "")),
                "name": recipe.get("Name", "Unknown Recipe"),
                "image": image_url,
                "calories": calories_display,
                "walkMeter": walk_meter,
                "calorieSource": calorie_source,
                "calculatedCalories": calculated_calories,
                "existingCalories": existing_calories,
                "rating": recipe.get("AggregatedRating"),
                "reviews": recipe.get("ReviewCount"),
                "topReview": top_review,
                "url": f"https://www.food.com/recipe/{slugify(recipe.get('Name', ''))}-{recipe.get('RecipeId', '')}",
                "ingredients": ingredients,
                "instructions": instructions,
                "nutrition": {
                    "Fat": f"{recipe.get('FatContent', 'N/A')}g",
                    "Saturated Fat": f"{recipe.get('SaturatedFatContent', 'N/A')}g",
                    "Cholesterol": f"{recipe.get('CholesterolContent', 'N/A')}mg",
                    "Sodium": f"{recipe.get('SodiumContent', 'N/A')}mg",
                    "Carbohydrates": f"{recipe.get('CarbohydrateContent', 'N/A')}g",
                    "Fiber": f"{recipe.get('FiberContent', 'N/A')}g",
                    "Sugar": f"{recipe.get('SugarContent', 'N/A')}g",
                    "Protein": f"{recipe.get('ProteinContent', 'N/A')}g",
                },
                "additionalInfo": {
                    "Author": recipe.get("AuthorName", "N/A"),
                    "Published": recipe.get("DatePublished", "N/A"),
                    "Servings": recipe.get("RecipeServings", recipe.get("RecipeYield", "N/A")),
                    "Prep Time": f"{recipe.get('PrepTime', 'N/A')} minutes" if recipe.get("PrepTime") else "N/A",
                    "Category": recipe.get("RecipeCategory", "N/A"),
                },
            }
            recipes_data.append(recipe_data)

        # Prepare response with spell correction info
        response_data = {
            "recipes": recipes_data,
            "currentPage": page,
            "totalPages": total_pages,
            "totalResults": total_results,
            "success": True,
            "cuisine": detected_cuisine,
        }

        # Add spell correction info if corrections were made
        if has_corrections:
            response_data["spellCorrection"] = {
                "originalQuery": original_query,
                "correctedQuery": corrected_query,
                "wasUsed": True,
                "message": f"Showing results for '{corrected_query}'",
            }

        # Check if we should suggest alternative spelling even when results found
        if not has_corrections:
            alternative_suggestions = {"mali": "malai", "maali": "malai", "malae": "malai", "malay": "malai"}

            query_lower = user_message.lower().strip()
            print(
                f"DEBUG: Checking spell suggestion - has_corrections: {has_corrections}, query_lower: '{query_lower}'"
            )
            if query_lower in alternative_suggestions:
                suggested_term = alternative_suggestions[query_lower]
                print(f"DEBUG: Adding spell suggestion for '{query_lower}' -> '{suggested_term}'")
                response_data["spellSuggestion"] = {
                    "originalQuery": user_message,
                    "suggestedQuery": suggested_term,
                    "message": f"Did you mean '{suggested_term}'?",
                }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error during cuisine search: {e}")
        return jsonify({"error": "Search failed", "success": False}), 500


@app.route("/suggest", methods=["GET"])
def suggest():
    print("[Suggest Route] Received request")
    query = request.args.get("query", "")
    print(f"[Suggest Route] Query parameter: '{query}'")

    if not query or len(query) < 2:  # Only suggest if query is at least 2 chars
        print("[Suggest Route] Query too short or empty, returning empty list.")
        return jsonify([])

    client, db = ensure_mongodb_connection()
    if db is None:
        print("[Suggest Route] DB connection is None, returning empty list.")
        return jsonify([])

    recipes_collection_name = os.getenv("RECIPES_COLLECTION", "recipes")
    recipes_collection = db[recipes_collection_name]
    print(f"[Suggest Route] Using collection: {recipes_collection_name}")

    try:
        # Use text search if available, otherwise fall back to regex
        # First, try text search which is much faster
        try:
            suggestions_cursor = (
                recipes_collection.find(
                    {"$text": {"$search": query}}, {"Name": 1, "_id": 0, "score": {"$meta": "textScore"}}
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(10)
            )

            suggestions_list_from_db = list(suggestions_cursor)

            # If text search returns results, use them
            if suggestions_list_from_db:
                print(f"[Suggest Route] Text search found {len(suggestions_list_from_db)} results")
                suggestion_names = [s["Name"] for s in suggestions_list_from_db if "Name" in s and s["Name"]]
                return jsonify(suggestion_names[:7])
        except Exception as e:
            print("[Suggest Route] Text search failed, falling back to regex")

        # Fallback to regex if text search fails or returns no results
        # Use a more efficient regex pattern
        regex_query = {"$regex": f".*{re.escape(query)}.*", "$options": "i"}
        print(f"[Suggest Route] Using regex fallback: {regex_query}")

        suggestions_cursor = recipes_collection.find({"Name": regex_query}, {"Name": 1, "_id": 0}).limit(10)

        suggestions_list_from_db = list(suggestions_cursor)
        print(f"[Suggest Route] Regex search found {len(suggestions_list_from_db)} results")

        # Get unique names and limit to 7
        suggestion_names = []
        seen = set()
        for s in suggestions_list_from_db:
            if "Name" in s and s["Name"] and s["Name"] not in seen:
                suggestion_names.append(s["Name"])
                seen.add(s["Name"])
                if len(suggestion_names) >= 7:
                    break

        print(f"[Suggest Route] Returning {len(suggestion_names)} suggestions")
        return jsonify(suggestion_names)

    except Exception as e:
        print(f"[Suggest Route] Error in /suggest endpoint: {e}")
        return jsonify([]), 500  # Return empty list and 500 on error


@app.route("/trending", methods=["GET"])
def trending():
    """Get trending searches"""
    try:
        # Ensure database connection
        client, db = ensure_mongodb_connection()

        # Check cache first
        if db is not None:
            trending_cache = db.trending_cache
            cache_doc = trending_cache.find_one({"_id": "current"})

            # Use cache if it's less than 5 minutes old (reduced for faster updates)
            if cache_doc:
                cache_age = datetime.utcnow() - cache_doc.get("updated_at", datetime.min)
                if cache_age < timedelta(minutes=5):
                    return jsonify(
                        {
                            "trending": cache_doc.get("trending", []),
                            "lastUpdated": cache_doc.get("updated_at").isoformat() + "Z",
                        }
                    )

        # Calculate fresh trending data
        trending_data = calculate_trending_searches()

        # Update cache
        if db is not None:
            trending_cache = db.trending_cache
            trending_cache.replace_one(
                {"_id": "current"},
                {"_id": "current", "trending": trending_data, "updated_at": datetime.utcnow()},
                upsert=True,
            )

        return jsonify({"trending": trending_data, "lastUpdated": datetime.utcnow().isoformat() + "Z"})

    except Exception as e:
        print(f"Error in /trending endpoint: {e}")
        return jsonify({"error": "Failed to fetch trending searches"}), 500


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Tastory Premium",
                            "description": "Access to premium features including advanced search, analytics, and more.",
                        },
                        "unit_amount": 500,  # $5.00 in cents
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:3000")
            + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/canceled",
        )
        return jsonify({"id": checkout_session.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@app.route("/webhook", methods=["POST"])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": str(e)}), 400

    # Handle the event
    if event.type == "checkout.session.completed":
        session = event.data.object
        # Set up the customer for success
        handle_checkout_session(session)
    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        handle_subscription_updated(subscription)
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        handle_subscription_deleted(subscription)
    elif event.type == "invoice.paid":
        invoice = event.data.object
        handle_invoice_paid(invoice)
    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        handle_invoice_failed(invoice)

    return jsonify({"status": "success"})


def handle_checkout_session(session):
    """Handle successful checkout session."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in session")
        return

    try:
        # Get customer details
        customer = stripe.Customer.retrieve(customer_id)
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Ensure database connection and store subscription info in MongoDB
        client, db = ensure_mongodb_connection()
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {"customer_id": customer_id},
                {
                    "$set": {
                        "customer_id": customer_id,
                        "subscription_id": subscription_id,
                        "email": customer.email,
                        "status": subscription.status,
                        "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                        "updated_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
    except Exception as e:
        logging.error(f"Error handling checkout session: {str(e)}")


def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")

    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in subscription update")
        return

    try:
        client, db = ensure_mongodb_connection()
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {"subscription_id": subscription_id},
                {
                    "$set": {
                        "status": subscription.status,
                        "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
    except Exception as e:
        logging.error(f"Error handling subscription update: {str(e)}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellations."""
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")

    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in subscription deletion")
        return

    try:
        client, db = ensure_mongodb_connection()
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {"subscription_id": subscription_id},
                {"$set": {"status": "canceled", "canceled_at": datetime.utcnow(), "updated_at": datetime.utcnow()}},
            )
    except Exception as e:
        logging.error(f"Error handling subscription deletion: {str(e)}")


def handle_invoice_paid(invoice):
    """Handle successful invoice payments."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in invoice")
        return

    try:
        client, db = ensure_mongodb_connection()
        if db is not None:
            # Update subscription payment status
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {"subscription_id": subscription_id},
                {
                    "$set": {
                        "last_payment_status": "paid",
                        "last_payment_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            # Store invoice record
            invoices = db.invoices
            invoices.insert_one(
                {
                    "invoice_id": invoice.id,
                    "customer_id": customer_id,
                    "subscription_id": subscription_id,
                    "amount_paid": invoice.amount_paid,
                    "status": invoice.status,
                    "created_at": datetime.fromtimestamp(invoice.created),
                    "payment_date": datetime.utcnow(),
                }
            )
    except Exception as e:
        logging.error(f"Error handling invoice payment: {str(e)}")


def handle_invoice_failed(invoice):
    """Handle failed invoice payments."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in failed invoice")
        return

    try:
        client, db = ensure_mongodb_connection()
        if db is not None:
            # Update subscription payment status
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {"subscription_id": subscription_id},
                {
                    "$set": {
                        "last_payment_status": "failed",
                        "last_payment_attempt": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            # Store failed invoice record
            invoices = db.invoices
            invoices.insert_one(
                {
                    "invoice_id": invoice.id,
                    "customer_id": customer_id,
                    "subscription_id": subscription_id,
                    "amount_due": invoice.amount_due,
                    "status": invoice.status,
                    "created_at": datetime.fromtimestamp(invoice.created),
                    "failure_date": datetime.utcnow(),
                    "failure_reason": invoice.get("last_payment_error", {}).get("message", "Unknown error"),
                }
            )
    except Exception as e:
        logging.error(f"Error handling failed invoice: {str(e)}")


@app.route("/recipe/<recipe_id>/calories", methods=["GET"])
def recipe_calorie_details(recipe_id):
    """Get detailed calorie breakdown for a specific recipe."""
    client, db = ensure_mongodb_connection()
    if db is None:
        return jsonify({"error": "Database connection not available"}), 500

    try:
        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

        # Find the recipe - try both string and numeric formats
        recipe_query = {"RecipeId": int(recipe_id)} if recipe_id.isdigit() else {"RecipeId": recipe_id}
        recipe = recipes_collection.find_one(
            recipe_query,
            {
                "Name": 1,
                "RecipeIngredientParts": 1,
                "RecipeIngredientQuantities": 1,
                "Calories": 1,
                "RecipeServings": 1,
                "RecipeYield": 1,
            },
        )

        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        # Calculate detailed calorie breakdown
        ingredients_data = recipe.get("RecipeIngredientParts")
        quantities_data = recipe.get("RecipeIngredientQuantities")
        servings = safe_get_servings(recipe)
        existing_calories = recipe.get("Calories")

        calc_result = None
        try:
            if NUTRITIONAL_DB_AVAILABLE:
                calc_result = calculate_recipe_calories(ingredients_data, quantities_data, servings)
        except Exception as e:
            print(f"Error calculating calories for recipe {recipe_id}: {e}")
            calc_result = None

        response = {
            "recipe": {"id": recipe_id, "name": recipe.get("Name"), "servings": servings},
            "existingCalories": {
                "total": existing_calories,
                "perServing": existing_calories / servings if existing_calories else None,
            },
            "calculatedCalories": calc_result,
            "accuracy": None,
        }

        # Calculate accuracy if both values exist
        if existing_calories and calc_result:
            existing_per_serving = existing_calories / servings
            calculated_per_serving = calc_result["calories_per_serving"]

            if existing_per_serving > 0:
                accuracy = (1 - abs(existing_per_serving - calculated_per_serving) / existing_per_serving) * 100
                response["accuracy"] = f"{accuracy:.1f}%"

        return jsonify(response)

    except Exception as e:
        print(f"Error getting calorie details: {e}")
        return jsonify({"error": "Failed to calculate calorie details"}), 500


# --- Helper function to calculate Walk Meter from calories ---
def spell_correct_query(query):
    """
    Correct common spelling mistakes in cooking-related terms
    """
    # Dictionary of common cooking term corrections
    cooking_corrections = {
        # Indian cuisine corrections
        "mali": "malai",
        "maali": "malai",
        "malae": "malai",
        "malay": "malai",
        "biryani": "biryani",
        "biriyani": "biryani",
        "biriani": "biryani",
        "briyani": "biryani",
        "biriany": "biryani",
        "masala": "masala",
        "masaala": "masala",
        "masalla": "masala",
        "masalaa": "masala",
        "panir": "paneer",
        "paneer": "paneer",
        "paner": "paneer",
        "panear": "paneer",
        "chaapati": "chapati",
        "chapatti": "chapati",
        "chappati": "chapati",
        "naan": "naan",
        "nan": "naan",
        "naaan": "naan",
        "daal": "dal",
        "dall": "dal",
        "dhaal": "dal",
        "chole": "chole",
        "chhole": "chole",
        "cholle": "chole",
        "ghee": "ghee",
        "ghi": "ghee",
        "gheee": "ghee",
        "tumeric": "turmeric",
        "turmeric": "turmeric",
        "cumin": "cumin",
        "cummin": "cumin",
        "jeera": "jeera",
        "jira": "jeera",
        "garam": "garam",
        "garamm": "garam",
        "tandori": "tandoori",
        "tandoori": "tandoori",
        "tanduri": "tandoori",
        # Italian cuisine corrections
        "spagetti": "spaghetti",
        "spaghetti": "spaghetti",
        "spagetthi": "spaghetti",
        "lasagna": "lasagna",
        "lasagne": "lasagna",
        "lasagana": "lasagna",
        "pizza": "pizza",
        "pizzaa": "pizza",
        "piza": "pizza",
        "pasta": "pasta",
        "pastaa": "pasta",
        "pesto": "pesto",
        "pestoo": "pesto",
        "marinara": "marinara",
        "marinera": "marinara",
        "marianra": "marinara",
        "risotto": "risotto",
        "risoto": "risotto",
        "risottoo": "risotto",
        # Chinese cuisine corrections
        "fried rice": "fried rice",
        "fry rice": "fried rice",
        "freid rice": "fried rice",
        "noodles": "noodles",
        "noodels": "noodles",
        "noodle": "noodles",
        "dimsum": "dimsum",
        "dim sum": "dimsum",
        "dimsom": "dimsum",
        "wontons": "wonton",
        "wonton": "wonton",
        "wantans": "wonton",
        # Mexican cuisine corrections
        "burrito": "burrito",
        "burito": "burrito",
        "buritto": "burrito",
        "taco": "taco",
        "tacoo": "taco",
        "tacos": "taco",
        "quesadilla": "quesadilla",
        "quesadila": "quesadilla",
        "quesedilla": "quesadilla",
        "enchilada": "enchilada",
        "enchiladas": "enchilada",
        "enchillada": "enchilada",
        "guacamole": "guacamole",
        "guacamolle": "guacamole",
        "guacomole": "guacamole",
        "salsa": "salsa",
        "salsaa": "salsa",
        # General cooking terms
        "chicken": "chicken",
        "chiken": "chicken",
        "chikken": "chicken",
        "checken": "chicken",
        "chocolate": "chocolate",
        "chocolatte": "chocolate",
        "choclate": "chocolate",
        "desert": "dessert",
        "dessert": "dessert",
        "deserts": "dessert",
        "desserts": "dessert",
        "icecream": "ice cream",
        "ice cream": "ice cream",
        "icream": "ice cream",
        "cookies": "cookies",
        "cookie": "cookies",
        "cookeis": "cookies",
        "coookies": "cookies",
        "vegitable": "vegetable",
        "vegetable": "vegetable",
        "vegtable": "vegetable",
        "vegetables": "vegetable",
        "tomato": "tomato",
        "tomatoe": "tomato",
        "tomatos": "tomato",
        "tomatoes": "tomato",
        "onion": "onion",
        "onions": "onion",
        "oinion": "onion",
        "potato": "potato",
        "potatoes": "potato",
        "potatoe": "potato",
        "potatos": "potato",
        "garlic": "garlic",
        "garlik": "garlic",
        "garlick": "garlic",
        "carrots": "carrot",
        "carrot": "carrot",
        "carot": "carrot",
        "carots": "carrot",
    }

    # Handle None and empty input
    if not query:
        return {"original": query or "", "corrected": "", "has_corrections": False}

    # Split query into words
    words = query.lower().split()
    corrected_words = []
    has_corrections = False

    for word in words:
        # Check if word needs correction
        if word in cooking_corrections:
            corrected_words.append(cooking_corrections[word])
            if cooking_corrections[word] != word:
                has_corrections = True
        else:
            # Check for partial matches (fuzzy matching)
            best_match = None
            best_score = 0

            for incorrect, correct in cooking_corrections.items():
                # Simple fuzzy matching - check if words are similar
                if len(word) > 2 and len(incorrect) > 2:
                    # Calculate simple similarity score
                    common_chars = len(set(word) & set(incorrect))
                    max_len = max(len(word), len(incorrect))
                    similarity = common_chars / max_len

                    # If words are similar enough (>70% char overlap) and lengths are close
                    if similarity > 0.7 and abs(len(word) - len(incorrect)) <= 2:
                        if similarity > best_score:
                            best_score = similarity
                            best_match = correct

            if best_match and best_score > 0.7:
                corrected_words.append(best_match)
                has_corrections = True
            else:
                corrected_words.append(word)

    corrected_query = " ".join(corrected_words)

    return {"original": query, "corrected": corrected_query, "has_corrections": has_corrections}


def calculate_walk_meter(calories):
    """Convert calories to walking distance with engaging messaging"""
    if not calories or calories == "N/A":
        return {"distance": "N/A", "message": "Walk data not available", "emoji": "🤷‍♀️", "context": ""}

    try:
        cal_value = float(str(calories).replace(" cal", ""))
        if cal_value <= 0:
            return {
                "distance": "0 km",
                "message": "No walking needed!",
                "emoji": "😌",
                "context": "This is a very low-calorie option",
            }

        # Calculate walking distance (85 calories per km average)
        km_distance = cal_value / 85

        # Create engaging messages based on distance
        if km_distance < 0.5:
            return {
                "distance": f"{(km_distance * 1000):.0f}m",
                "message": "Just a short stroll!",
                "emoji": "🚶‍♀️",
                "context": "Less than a city block",
            }
        elif km_distance < 1:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "A nice neighborhood walk",
                "emoji": "🚶‍♂️",
                "context": "About 10-12 minutes walking",
            }
        elif km_distance < 2:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "A pleasant park stroll",
                "emoji": "🌳",
                "context": "Perfect for listening to 3-4 songs",
            }
        elif km_distance < 3:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "A good workout walk",
                "emoji": "💪",
                "context": "Like walking to the local café",
            }
        elif km_distance < 5:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "Time for a power walk!",
                "emoji": "🏃‍♀️",
                "context": "Equivalent to a short jogging session",
            }
        elif km_distance < 8:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "That's a serious hike!",
                "emoji": "🥾",
                "context": "Like walking across town",
            }
        elif km_distance < 15:
            return {
                "distance": f"{km_distance:.1f} km",
                "message": "Marathon training territory!",
                "emoji": "🏃‍♂️",
                "context": "Better save this for special occasions",
            }
        else:
            return {
                "distance": f"{km_distance:.0f} km",
                "message": "That's an ultra-marathon!",
                "emoji": "🏔️",
                "context": "Maybe consider sharing this dish!",
            }

    except (ValueError, TypeError):
        return {"distance": "N/A", "message": "Walk data not available", "emoji": "🤷‍♀️", "context": ""}


# --- Helper function to get stock photos for recipes without images ---
# COMMENTED OUT - Reverted to old concept of showing "no image found" for recipes without images
# def get_stock_photo_for_recipe(recipe_name, recipe_category, ingredients):
#     """Get an appropriate stock photo URL based on recipe characteristics"""
#
#     try:
#         # Try to get an actual food image from Google Images first
#         google_image_url = get_google_food_image(recipe_name, recipe_category)
#         if google_image_url:
#             return google_image_url
#     except Exception as e:
#         print(f"Google Images search failed: {e}")
#
#     # Fallback to Lorem Picsum with food-appropriate styling
#     # Each category gets a unique seed for consistent but varied images
#     image_seeds = {
#         # Main dish categories
#         "pizza": 100,
#         "pasta": 101,
#         "burger": 102,
#         "sandwich": 103,
#         "salad": 104,
#         "soup": 105,
#         "steak": 106,
#         "chicken": 107,
#         "fish": 108,
#         "seafood": 109,
#         "rice": 110,
#         "curry": 111,
#         "stir_fry": 112,
#         "tacos": 113,
#         "noodles": 114,
#
#         # Breakfast items
#         "breakfast": 200,
#         "pancakes": 201,
#         "eggs": 202,
#         "omelette": 203,
#         "toast": 204,
#         "cereal": 205,
#
#         # Desserts
#         "dessert": 300,
#         "cake": 301,
#         "cookies": 302,
#         "ice_cream": 303,
#         "pie": 304,
#         "chocolate": 305,
#         "cupcake": 306,
#
#         # Beverages
#         "smoothie": 400,
#         "juice": 401,
#         "coffee": 402,
#         "tea": 403,
#         "cocktail": 404,
#
#         # Appetizers
#         "appetizer": 500,
#         "dip": 501,
#         "bread": 502,
#         "cheese": 503,
#
#         # International cuisine
#         "italian": 600,
#         "mexican": 601,
#         "asian": 602,
#         "indian": 603,
#         "chinese": 604,
#         "japanese": 605,
#         "mediterranean": 606,
#
#         # Cooking methods
#         "grilled": 700,
#         "baked": 701,
#         "fried": 702,
#         "roasted": 703,
#
#         # Default fallback
#         "default": 999
#     }
#
#     # Convert inputs to lowercase for matching
#     recipe_name_lower = recipe_name.lower() if recipe_name else ""
#     recipe_category_lower = recipe_category.lower() if recipe_category else ""
#     ingredients_text = " ".join(ingredients).lower() if ingredients else ""
#
#     # Combine all text for keyword matching
#     all_text = f"{recipe_name_lower} {recipe_category_lower} {ingredients_text}"
#
#     # Priority matching - check specific keywords first
#     priority_keywords = [
#         "pizza", "pasta", "burger", "sandwich", "salad", "soup",
#         "steak", "chicken", "fish", "curry", "tacos", "noodles",
#         "cake", "cookies", "ice cream", "pie", "smoothie"
#     ]
#
#     for keyword in priority_keywords:
#         if keyword in all_text:
#             seed = image_seeds.get(keyword.replace(" ", "_"), image_seeds["default"])
#             return f"https://picsum.photos/seed/{seed}/500/300"
#
#     # Secondary matching - broader categories
#     secondary_keywords = [
#         ("breakfast", ["breakfast", "pancake", "egg", "omelette", "toast", "cereal"]),
#         ("dessert", ["dessert", "sweet", "chocolate", "sugar", "frosting", "cream"]),
#         ("italian", ["italian", "marinara", "parmesan", "basil", "oregano"]),
#         ("mexican", ["mexican", "taco", "burrito", "salsa", "cilantro", "lime"]),
#         ("asian", ["asian", "soy", "ginger", "sesame", "rice vinegar"]),
#         ("indian", ["indian", "curry", "masala", "turmeric", "cumin", "garam"]),
#         ("appetizer", ["appetizer", "dip", "chip", "starter", "finger"]),
#         ("grilled", ["grill", "bbq", "barbecue", "char"]),
#         ("baked", ["bake", "oven", "roast"]),
#     ]
#
#     for category, keywords in secondary_keywords:
#         if any(keyword in all_text for keyword in keywords):
#             if category in image_seeds:
#                 seed = image_seeds[category]
#                 return f"https://picsum.photos/seed/{seed}/500/300"
#
#     # Default fallback photo
#     seed = image_seeds["default"]
#     return f"https://picsum.photos/seed/{seed}/500/300"

# def get_google_food_image(recipe_name, recipe_category):
#     """Get a relevant food image using LoremFlickr (reliable food image service)"""
#
#     try:
#         # Create a food-focused search query
#         search_terms = []
#         if recipe_name:
#             # Clean the recipe name - remove common recipe words
#             clean_name = recipe_name.replace("Recipe", "").replace("recipe", "").replace("Copycat", "").strip()
#             # Take first few words to avoid overly specific searches
#             name_words = clean_name.split()[:2]
#             search_terms.extend(name_words)
#
#         # Add food context
#         search_terms.append("food")
#
#         # Create search query for LoremFlickr (uses comma-separated terms)
#         flickr_query = ",".join(search_terms).strip()
#         if not flickr_query or flickr_query == "food":
#             flickr_query = "delicious,food"
#
#         print(f"Searching LoremFlickr for: {flickr_query}")
#
#         # Use LoremFlickr as primary source (working reliably for food images)
#         encoded_query = urllib.parse.quote(flickr_query)
#         flickr_url = f"https://loremflickr.com/500/300/{encoded_query}"
#
#         print(f"Generated LoremFlickr URL: {flickr_url}")
#
#         # LoremFlickr is designed for this use case and provides consistent results
#         # No need to test the URL since LoremFlickr is reliable
#         return flickr_url
#
#     except Exception as e:
#         print(f"Error in LoremFlickr image search: {e}")
#         # Final fallback to a static food placeholder
#         fallback_url = "https://via.placeholder.com/500x300/8B4513/FFFFFF?text=Food+Image"
#         print(f"Using placeholder fallback: {fallback_url}")
#         return fallback_url


@app.route("/search/cuisine", methods=["POST"])
def cuisine_search():
    data = request.get_json()
    query = data.get("query", "").strip()
    page = data.get("page", 1)
    per_page = 12

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Check for spell corrections
        spell_check = spell_correct_query(query)
        original_query = spell_check["original"]
        corrected_query = spell_check["corrected"]
        has_corrections = spell_check["has_corrections"]

        # Use corrected query if available, otherwise use original
        search_query_text = corrected_query if has_corrections else query

        # Ensure database connection
        client, db = ensure_mongodb_connection()
        if db is None:
            return jsonify({"error": "Database connection not available"}), 500

        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]

        # Define cuisine categories
        cuisine_mapping = {
            "indian": [
                "indian",
                "chole",
                "puri",
                "curry",
                "masala",
                "naan",
                "roti",
                "biryani",
                "samosa",
                "pav bhaji",
                "bhaji",
                "pav",
                "dal",
                "tandoori",
                "tikka",
                "paneer",
                "dosa",
                "idli",
                "vada",
                "uttapam",
                "rajma",
                "palak",
                "saag",
                "aloo",
                "gobi",
                "matar",
                "jeera",
                "garam masala",
                "turmeric",
                "cumin",
                "cardamom",
                "coriander",
                "fenugreek",
                "chapati",
                "paratha",
                "kulcha",
                "bhatura",
                "rasam",
                "sambar",
                "chutney",
                "lassi",
                "kulfi",
                "gulab jamun",
                "rasgulla",
                "kheer",
                "halwa",
            ],
            "italian": ["italian", "pasta", "pizza", "risotto", "lasagna", "spaghetti", "marinara", "pesto"],
            "dessert": ["dessert", "ice cream", "cake", "pie", "cookie", "chocolate", "sweet", "pudding"],
            "chinese": ["chinese", "noodles", "fried rice", "dimsum", "spring roll", "wonton", "chow mein"],
            "mexican": ["mexican", "taco", "burrito", "enchilada", "quesadilla", "salsa", "guacamole"],
        }

        # Detect cuisine from query - improved logic for multi-word terms
        query_terms = search_query_text.lower().split()
        detected_cuisine = None
        original_query_lower = search_query_text.lower()

        for cuisine, terms in cuisine_mapping.items():
            # Check both individual words and the full query for multi-word terms
            cuisine_match = False

            # Check if any cuisine term appears in the original query
            for term in terms:
                if term in original_query_lower:
                    cuisine_match = True
                    break

            # Also check if any search term matches any cuisine term
            if not cuisine_match:
                for search_term in query_terms:
                    if any(search_term in term.lower() for term in terms):
                        cuisine_match = True
                        break

            if cuisine_match:
                detected_cuisine = cuisine
                break

        if not detected_cuisine:
            return jsonify({"error": "No cuisine type detected in query"}), 400

        # Create search query with improved regex handling
        cuisine_terms = cuisine_mapping[detected_cuisine]

        # Split multi-word terms and single-word terms for better regex handling
        single_word_terms = []
        multi_word_terms = []

        for term in cuisine_terms:
            if " " in term:
                multi_word_terms.append(term)
            else:
                single_word_terms.append(term)

        # Build cuisine conditions
        cuisine_conditions = []

        # Handle single-word terms
        if single_word_terms:
            single_word_pattern = f"({'|'.join(re.escape(term) for term in single_word_terms)})"
            cuisine_conditions.extend(
                [
                    {"RecipeCategory": {"$regex": single_word_pattern, "$options": "i"}},
                    {"Keywords": {"$regex": single_word_pattern, "$options": "i"}},
                    {"Name": {"$regex": single_word_pattern, "$options": "i"}},
                ]
            )

        # Handle multi-word terms separately
        for multi_term in multi_word_terms:
            escaped_term = re.escape(multi_term)
            cuisine_conditions.extend(
                [
                    {"RecipeCategory": {"$regex": escaped_term, "$options": "i"}},
                    {"Keywords": {"$regex": escaped_term, "$options": "i"}},
                    {"Name": {"$regex": escaped_term, "$options": "i"}},
                ]
            )

        search_query = {
            "$and": [
                # Must match the cuisine type
                {"$or": cuisine_conditions},
                # Must match all search terms
                *[
                    {
                        "$or": [
                            {"Name": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                            {"RecipeCategory": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                            {"Keywords": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                            {"RecipeIngredientParts": {"$regex": f"\\b{re.escape(term)}\\b", "$options": "i"}},
                        ]
                    }
                    for term in query_terms
                ],
            ]
        }

        # Execute search
        results = list(
            recipes_collection.find(
                search_query,
                {
                    "_id": 0,
                    "RecipeId": 1,
                    "Name": 1,
                    "Description": 1,
                    "RecipeIngredientParts": 1,
                    "RecipeIngredientQuantities": 1,
                    "RecipeInstructions": 1,
                    "Images": 1,
                    "MainImage": 1,
                    "Calories": 1,
                    "AuthorName": 1,
                    "DatePublished": 1,
                    "RecipeServings": 1,
                    "RecipeYield": 1,
                    "PrepTime": 1,
                    "RecipeCategory": 1,
                    "FatContent": 1,
                    "SaturatedFatContent": 1,
                    "CholesterolContent": 1,
                    "SodiumContent": 1,
                    "CarbohydrateContent": 1,
                    "FiberContent": 1,
                    "SugarContent": 1,
                    "ProteinContent": 1,
                    "AggregatedRating": 1,
                    "ReviewCount": 1,
                },
            ).limit(30)
        )

        # Process results (same logic as main chat route)
        recipes_with_images = []
        recipes_without_images = []

        for recipe in results:
            has_image = False
            main_image = recipe.get("MainImage")
            images = recipe.get("Images", [])

            if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
                has_image = True
            elif images and isinstance(images, list) and len(images) > 0:
                if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                    has_image = True

            if has_image:
                recipes_with_images.append(recipe)
            else:
                recipes_without_images.append(recipe)

        # Combine results with images first
        sorted_results = recipes_with_images + recipes_without_images

        # Calculate pagination
        total_results = len(sorted_results)
        total_pages = max(1, min(3, math.ceil(total_results / per_page)))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = sorted_results[start_idx:end_idx]

        # Get reviews collection for fetching top reviews
        reviews_collection = db[os.getenv("REVIEWS_COLLECTION", "reviews")]

        # Format results (using same processing logic as main chat route)
        recipes_data = []
        for recipe in page_results:
            # Extract image URL - check for existing images first
            image_url = None
            main_image = recipe.get("MainImage")
            images = recipe.get("Images", [])

            if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
                image_url = main_image.strip()
            elif images and isinstance(images, list) and len(images) > 0:
                if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                    image_url = images[0].strip()

            # Process ingredients - combine names with quantities
            ingredients = []
            ingredients_data = recipe.get("RecipeIngredientParts")
            quantities_data = recipe.get("RecipeIngredientQuantities")

            # Parse ingredient names
            ingredient_names = []
            if isinstance(ingredients_data, list):
                for item in ingredients_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    ingredient_names.extend([str(ing).strip() for ing in parsed if ing])
                                else:
                                    ingredient_names.append(str(item).strip())
                            else:
                                ingredient_names.append(str(item).strip())
                        except json.JSONDecodeError:
                            ingredient_names.append(str(item).strip())
                    elif item:
                        ingredient_names.append(str(item).strip())
            elif isinstance(ingredients_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if ingredients_data.strip().startswith("[") and ingredients_data.strip().endswith("]"):
                        parsed = json.loads(ingredients_data)
                        if isinstance(parsed, list):
                            ingredient_names.extend([str(ing).strip() for ing in parsed if ing])
                        else:
                            ingredient_names.append(ingredients_data.strip())
                    else:
                        ingredient_names.append(ingredients_data.strip())
                except json.JSONDecodeError:
                    ingredient_names.append(ingredients_data.strip())

            # Parse quantities
            quantities = []
            if isinstance(quantities_data, list):
                for item in quantities_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    quantities.extend([str(qty).strip() for qty in parsed if qty])
                                else:
                                    quantities.append(str(item).strip())
                            else:
                                quantities.append(str(item).strip())
                        except json.JSONDecodeError:
                            quantities.append(str(item).strip())
                    elif item:
                        quantities.append(str(item).strip())
            elif isinstance(quantities_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if quantities_data.strip().startswith("[") and quantities_data.strip().endswith("]"):
                        parsed = json.loads(quantities_data)
                        if isinstance(parsed, list):
                            quantities.extend([str(qty).strip() for qty in parsed if qty])
                        else:
                            quantities.append(quantities_data.strip())
                    else:
                        quantities.append(quantities_data.strip())
                except json.JSONDecodeError:
                    quantities.append(quantities_data.strip())

            # Combine ingredients with quantities
            for i, name in enumerate(ingredient_names):
                if i < len(quantities) and quantities[i] and quantities[i].lower() != "nan":
                    # Format: "quantity name"
                    ingredients.append(f"{quantities[i]} {name}")
                else:
                    # Just the ingredient name if no quantity available
                    ingredients.append(name)

            # If no image found, leave image_url as None (will show "no image found" in frontend)
            # Removed automatic image generation to revert to old concept

            # Process instructions - parse JSON strings properly
            instructions = []
            instructions_data = recipe.get("RecipeInstructions", [])

            if isinstance(instructions_data, list):
                for item in instructions_data:
                    if isinstance(item, str):
                        try:
                            # Try to parse as JSON if it looks like a JSON string
                            if item.strip().startswith("[") and item.strip().endswith("]"):
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    instructions.extend([str(inst).strip() for inst in parsed if inst])
                                else:
                                    instructions.append(str(item).strip())
                            else:
                                instructions.append(str(item).strip())
                        except json.JSONDecodeError:
                            instructions.append(str(item).strip())
                    elif item:
                        instructions.append(str(item).strip())
            elif isinstance(instructions_data, str):
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    if instructions_data.strip().startswith("[") and instructions_data.strip().endswith("]"):
                        parsed = json.loads(instructions_data)
                        if isinstance(parsed, list):
                            instructions.extend([str(inst).strip() for inst in parsed if inst])
                        else:
                            instructions.append(instructions_data.strip())
                    else:
                        instructions.append(instructions_data.strip())
                except json.JSONDecodeError:
                    instructions.append(instructions_data.strip())

            # Process calories - combine existing and calculated
            existing_calories = recipe.get("Calories")
            servings = safe_get_servings(recipe)

            # Calculate calories from ingredients
            calculated_calories = None
            try:
                ingredients_data = recipe.get("RecipeIngredientParts")
                quantities_data = recipe.get("RecipeIngredientQuantities")

                if ingredients_data and quantities_data:
                    calc_result = calculate_recipe_calories(ingredients_data, quantities_data, servings)
                    if calc_result:
                        calculated_calories = calc_result["calories_per_serving"]
            except Exception as e:
                print(f"Error calculating calories for recipe {recipe.get('RecipeId')}: {e}")

            # Determine which calorie value to display - PRIORITIZE CALCULATED CALORIES
            calories_display = "N/A"
            calorie_source = "none"

            # First try to use calculated calories (user preference)
            if calculated_calories:
                calories_display = f"{calculated_calories:.0f}"
                calorie_source = "calculated"
            # Only fall back to database calories if no calculated value
            elif existing_calories is not None:
                try:
                    existing_per_serving = float(existing_calories) / servings
                    calories_display = f"{existing_per_serving:.0f}"
                    calorie_source = "database"
                except (ValueError, TypeError, ZeroDivisionError):
                    calories_display = "N/A"
                    calorie_source = "none"

            # Calculate walkMeter
            walk_meter = calculate_walk_meter(calories_display)

            # Get top review for this recipe
            top_review = get_top_review(reviews_collection, recipe.get("RecipeId"))

            recipe_data = {
                "id": str(recipe.get("RecipeId", "")),
                "name": recipe.get("Name", "Unknown Recipe"),
                "image": image_url,
                "calories": calories_display,
                "walkMeter": walk_meter,
                "calorieSource": calorie_source,
                "calculatedCalories": calculated_calories,
                "existingCalories": existing_calories,
                "rating": recipe.get("AggregatedRating"),
                "reviews": recipe.get("ReviewCount"),
                "topReview": top_review,
                "url": f"https://www.food.com/recipe/{slugify(recipe.get('Name', ''))}-{recipe.get('RecipeId', '')}",
                "ingredients": ingredients,
                "instructions": instructions,
                "nutrition": {
                    "Fat": f"{recipe.get('FatContent', 'N/A')}g",
                    "Saturated Fat": f"{recipe.get('SaturatedFatContent', 'N/A')}g",
                    "Cholesterol": f"{recipe.get('CholesterolContent', 'N/A')}mg",
                    "Sodium": f"{recipe.get('SodiumContent', 'N/A')}mg",
                    "Carbohydrates": f"{recipe.get('CarbohydrateContent', 'N/A')}g",
                    "Fiber": f"{recipe.get('FiberContent', 'N/A')}g",
                    "Sugar": f"{recipe.get('SugarContent', 'N/A')}g",
                    "Protein": f"{recipe.get('ProteinContent', 'N/A')}g",
                },
                "additionalInfo": {
                    "Author": recipe.get("AuthorName", "N/A"),
                    "Published": recipe.get("DatePublished", "N/A"),
                    "Servings": recipe.get("RecipeServings", recipe.get("RecipeYield", "N/A")),
                    "Prep Time": f"{recipe.get('PrepTime', 'N/A')} minutes" if recipe.get("PrepTime") else "N/A",
                    "Category": recipe.get("RecipeCategory", "N/A"),
                },
            }
            recipes_data.append(recipe_data)

        # Prepare response with spell correction info
        response_data = {
            "recipes": recipes_data,
            "currentPage": page,
            "totalPages": total_pages,
            "totalResults": total_results,
            "success": True,
            "cuisine": detected_cuisine,
        }

        # Add spell correction info if corrections were made
        if has_corrections:
            response_data["spellCorrection"] = {
                "originalQuery": original_query,
                "correctedQuery": corrected_query,
                "wasUsed": True,
                "message": f"Showing results for '{corrected_query}'",
            }

        # Check if we should suggest alternative spelling even when results found
        if not has_corrections:
            alternative_suggestions = {"mali": "malai", "maali": "malai", "malae": "malai", "malay": "malai"}

            query_lower = query.lower().strip()
            if query_lower in alternative_suggestions:
                suggested_term = alternative_suggestions[query_lower]
                response_data["spellSuggestion"] = {
                    "originalQuery": query,
                    "suggestedQuery": suggested_term,
                    "message": f"Did you mean '{suggested_term}'?",
                }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error during cuisine search: {e}")
        return jsonify({"error": "Search failed", "success": False}), 500


# TODO: Future Unique Endpoints
# @app.route('/cooking-mode/<recipe_id>', methods=['POST'])
# - Start a cooking session with step tracking
# - Voice command processing
# - Timer management
#
# @app.route('/substitute/<ingredient>', methods=['GET'])
# - AI-powered ingredient substitution suggestions
#
# @app.route('/meal-plan', methods=['POST'])
# - Generate weekly meal plans based on preferences
#
# @app.route('/recipe-science/<recipe_id>', methods=['GET'])
# - Explain the science behind cooking techniques
#
# @app.route('/community/cook-along', methods=['GET', 'POST'])
# - Real-time cooking sessions with other users

if __name__ == "__main__":
    # Get port from environment variable (default to 5001 for local development)
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False for production
