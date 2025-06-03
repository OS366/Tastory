import datetime
import json
import logging
import math  # Required for math.ceil
import os
import re

import numpy as np
import pymongo
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# --- Load Embedding Model ---
MODEL_NAME = "all-MiniLM-L6-v2"
embedding_model = None
try:
    print(f"Loading sentence-transformer model: {MODEL_NAME}...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"Model {MODEL_NAME} loaded successfully.")
    _ = embedding_model.encode("Test sentence")
    print("Test embedding generated successfully.")
except Exception as e:
    print(f"Error loading sentence-transformer model: {e}")
    embedding_model = None

# --- Recipe Embedding Configuration ---
RECIPE_EMBEDDING_FIELD = "recipe_embedding_all_MiniLM_L6_v2"
RECIPE_VECTOR_INDEX_NAME = "idx_recipes_vector"


def get_embedding(text):
    if embedding_model is None:
        print("Embedding model is not available.")
        return None
    if not text or not isinstance(text, str):
        print("Invalid input text for embedding.")
        return None
    try:
        embedding = embedding_model.encode(text)
        return embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
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
    except pymongo.errors.ConfigurationError as e:
        print(f"MongoDB Configuration Error: {e}")
        return None, None
    except pymongo.errors.ConnectionFailure as e:
        print(f"MongoDB Connection Failure: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB connection: {e}")
        return None, None


client, db = connect_to_mongodb()


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


# Routes
@app.route("/health")
def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test MongoDB connection
        db.recipes.find_one({}, {"_id": 1})
        return {"status": "healthy", "service": "tastory-api", "database": "connected"}, 200
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}, 503


@app.route("/")
def index():
    return jsonify(
        {
            "name": "Tastory API",
            "tagline": "The Food Search Engine",
            "version": "1.0.0-beta",
            "endpoints": {
                "/chat": "Search for recipes using natural language",
                "/suggest": "Get search suggestions as you type",
                "/health": "Health check endpoint"
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
    user_message = data.get("message", "")
    page = data.get("page", 1)
    per_page = 12  # Fixed at 12 for 4x3 grid

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    global client, db
    if db is None:
        print("Database connection is not available. Attempting to reconnect...")
        client, db = connect_to_mongodb()
        if db is None:
            return jsonify({"reply": "Error: Could not connect to the database. Please check server logs."}), 500

    user_embedding = get_embedding(user_message)
    if not user_embedding:
        print("Failed to generate embedding for user message.")
        return jsonify({"reply": "Sorry, I couldn't understand your message well enough to search for recipes."}), 500

    print(f"Generated embedding for user message (first 3 dims): {user_embedding[:3]}...")

    recipes_collection_name = os.getenv("RECIPES_COLLECTION", "recipes")
    recipes_collection = db[recipes_collection_name]

    # Optimized vector search pipeline - fetch only what we need for the current page
    skip_amount = (page - 1) * per_page

    vector_search_pipeline = [
        {
            "$vectorSearch": {
                "index": RECIPE_VECTOR_INDEX_NAME,
                "queryVector": user_embedding,
                "path": RECIPE_EMBEDDING_FIELD,
                "numCandidates": 20,  # Further reduced for faster search
                "limit": 15,  # Just enough for one page plus a few extra
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
                "search_score": {"$meta": "vectorSearchScore"},
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
            }
        },
        # Sort in MongoDB instead of Python for better performance
        {"$sort": {"search_score": -1}},
        # Limit results early to avoid processing too much data
        {"$limit": 30},
    ]

    try:
        # Execute the pipeline with a reasonable timeout
        results = list(recipes_collection.aggregate(vector_search_pipeline, maxTimeMS=15000))

        # Sort results by image availability - process all results first
        recipes_with_images = []
        recipes_without_images = []

        for recipe in results:
            # Check if recipe has a valid image
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

        # Quick count for total pages (estimate based on sorted results)
        total_results = len(sorted_results)
        total_pages = max(1, min(3, math.ceil(total_results / per_page)))  # Cap at 3 pages for performance

        # Get the recipes for current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = sorted_results[start_idx:end_idx]

        # Convert to simple JSON format instead of HTML
        recipes_data = []
        for recipe in page_results:
            # Extract image URL
            image_url = None
            main_image = recipe.get("MainImage")
            images = recipe.get("Images", [])

            if main_image and isinstance(main_image, str) and main_image.strip().startswith(("http://", "https://")):
                image_url = main_image.strip()
            elif images and isinstance(images, list) and len(images) > 0:
                if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                    image_url = images[0].strip()

            # Process ingredients
            ingredients = []
            ingredients_data = recipe.get("RecipeIngredientParts")
            quantities_data = recipe.get("RecipeIngredientQuantities")

            if isinstance(ingredients_data, list):
                # If we have quantities, combine them with ingredients
                if isinstance(quantities_data, list):
                    for i, ing in enumerate(ingredients_data):
                        if ing and str(ing).strip():
                            if i < len(quantities_data) and quantities_data[i]:
                                quantity = str(quantities_data[i]).strip()
                                # Skip NA, N/A, None, or similar non-quantity values
                                if quantity.upper() in ["NA", "N/A", "NONE", "NULL", ""]:
                                    ingredients.append(str(ing))
                                else:
                                    # Combine quantity with ingredient
                                    ingredients.append(f"{quantity} {ing}")
                            else:
                                # No quantity for this ingredient
                                ingredients.append(str(ing))
                else:
                    # No quantities available, just use ingredients as is
                    ingredients = [str(ing) for ing in ingredients_data if ing and str(ing).strip()]
            elif isinstance(ingredients_data, str):
                if ingredients_data.strip().startswith("["):
                    try:
                        parsed = json.loads(ingredients_data)
                        if isinstance(parsed, list):
                            # Try to parse quantities too
                            if isinstance(quantities_data, str) and quantities_data.strip().startswith("["):
                                try:
                                    parsed_quantities = json.loads(quantities_data)
                                    if isinstance(parsed_quantities, list):
                                        for i, ing in enumerate(parsed):
                                            if ing and str(ing).strip():
                                                if i < len(parsed_quantities) and parsed_quantities[i]:
                                                    ingredients.append(f"{parsed_quantities[i]} {ing}")
                                                else:
                                                    ingredients.append(str(ing))
                                    else:
                                        ingredients = [str(ing) for ing in parsed if ing and str(ing).strip()]
                                except Exception:
                                    ingredients = [str(ing) for ing in parsed if ing and str(ing).strip()]
                            else:
                                ingredients = [str(ing) for ing in parsed if ing and str(ing).strip()]
                    except Exception:
                        if ingredients_data.strip():
                            ingredients = [ingredients_data]
                elif ingredients_data.strip():
                    ingredients = [ingredients_data]

            # Process instructions
            instructions = []
            instructions_data = recipe.get("RecipeInstructions", [])
            if isinstance(instructions_data, list):
                instructions = [str(inst) for inst in instructions_data if inst]
            elif isinstance(instructions_data, str):
                try:
                    parsed = json.loads(instructions_data)
                    if isinstance(parsed, list):
                        instructions = [str(inst) for inst in parsed if inst]
                    else:
                        instructions = [instructions_data]
                except Exception:
                    if instructions_data.strip():
                        instructions = [instructions_data]

            # Process calories
            calories = recipe.get("Calories")
            calories_display = "N/A"
            if calories is not None:
                try:
                    calories_display = f"{float(calories):.0f}"
                except Exception:
                    calories_display = str(calories)

            # Build recipe data object
            recipe_data = {
                "id": str(recipe.get("RecipeId", "")),
                "name": recipe.get("Name", "Unknown Recipe"),
                "image": image_url,
                "calories": calories_display,
                "rating": recipe.get("AggregatedRating"),
                "reviews": recipe.get("ReviewCount"),
                "url": (
                    f"https://www.food.com/recipe/" f"{slugify(recipe.get('Name', ''))}-{recipe.get('RecipeId', '')}"
                ),
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

        return jsonify(
            {
                "recipes": recipes_data,
                "currentPage": page,
                "totalPages": total_pages,
                "totalResults": total_results,
                "success": True,
            }
        )

    except pymongo.errors.OperationFailure as e:
        print(f"MongoDB OperationFailure: {e.details}")
        error_message = str(e.details.get("errmsg", "Unknown MongoDB error"))

        # If vector search times out, try a simpler text search fallback
        if "time limit" in error_message.lower():
            print("Vector search timed out, falling back to text search...")
            try:
                # Use text search as fallback
                text_search_results = list(
                    recipes_collection.find(
                        {"$text": {"$search": user_message}},
                        {
                            "_id": 0,
                            "RecipeId": 1,
                            "Name": 1,
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
                            "score": {"$meta": "textScore"},
                        },
                    )
                    .sort([("score", {"$meta": "textScore"})])
                    .limit(30)
                )

                if text_search_results:
                    # Sort text search results by image availability
                    recipes_with_images = []
                    recipes_without_images = []

                    for recipe in text_search_results:
                        # Check if recipe has a valid image
                        has_image = False
                        main_image = recipe.get("MainImage")
                        images = recipe.get("Images", [])

                        if (
                            main_image
                            and isinstance(main_image, str)
                            and main_image.strip().startswith(("http://", "https://"))
                        ):
                            has_image = True
                        elif images and isinstance(images, list) and len(images) > 0:
                            if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                                has_image = True

                        if has_image:
                            recipes_with_images.append(recipe)
                        else:
                            recipes_without_images.append(recipe)

                    # Combine results with images first
                    sorted_text_results = recipes_with_images + recipes_without_images

                    # Process text search results the same way
                    total_results = len(sorted_text_results)
                    total_pages = max(1, min(3, math.ceil(total_results / per_page)))
                    start_idx = (page - 1) * per_page
                    end_idx = start_idx + per_page
                    page_results = sorted_text_results[start_idx:end_idx]

                    # Process results into JSON format (same as vector search)
                    recipes_data = []
                    for recipe in page_results:
                        # Extract image URL
                        image_url = None
                        main_image = recipe.get("MainImage")
                        images = recipe.get("Images", [])

                        if (
                            main_image
                            and isinstance(main_image, str)
                            and main_image.strip().startswith(("http://", "https://"))
                        ):
                            image_url = main_image.strip()
                        elif images and isinstance(images, list) and len(images) > 0:
                            if isinstance(images[0], str) and images[0].strip().startswith(("http://", "https://")):
                                image_url = images[0].strip()

                        # Process ingredients
                        ingredients = []
                        ingredients_data = recipe.get("RecipeIngredientParts")
                        quantities_data = recipe.get("RecipeIngredientQuantities")

                        if isinstance(ingredients_data, list):
                            # If we have quantities, combine them with ingredients
                            if isinstance(quantities_data, list):
                                for i, ing in enumerate(ingredients_data):
                                    if ing and str(ing).strip():
                                        if i < len(quantities_data) and quantities_data[i]:
                                            quantity = str(quantities_data[i]).strip()
                                            # Skip NA, N/A, None, or similar non-quantity values
                                            if quantity.upper() in ["NA", "N/A", "NONE", "NULL", ""]:
                                                ingredients.append(str(ing))
                                            else:
                                                # Combine quantity with ingredient
                                                ingredients.append(f"{quantity} {ing}")
                                        else:
                                            # No quantity for this ingredient
                                            ingredients.append(str(ing))
                            else:
                                # No quantities available, just use ingredients as is
                                ingredients = [str(ing) for ing in ingredients_data if ing and str(ing).strip()]
                        elif isinstance(ingredients_data, str):
                            if ingredients_data.strip().startswith("["):
                                try:
                                    parsed = json.loads(ingredients_data)
                                    if isinstance(parsed, list):
                                        # Try to parse quantities too
                                        if isinstance(quantities_data, str) and quantities_data.strip().startswith("["):
                                            try:
                                                parsed_quantities = json.loads(quantities_data)
                                                if isinstance(parsed_quantities, list):
                                                    for i, ing in enumerate(parsed):
                                                        if ing and str(ing).strip():
                                                            if i < len(parsed_quantities) and parsed_quantities[i]:
                                                                quantity = str(parsed_quantities[i]).strip()
                                                                # Skip NA, N/A, None, or similar non-quantity values
                                                                if quantity.upper() in [
                                                                    "NA",
                                                                    "N/A",
                                                                    "NONE",
                                                                    "NULL",
                                                                    "",
                                                                ]:
                                                                    ingredients.append(str(ing))
                                                                else:
                                                                    # Combine quantity with ingredient
                                                                    ingredients.append(f"{quantity} {ing}")
                                                            else:
                                                                ingredients.append(str(ing))
                                                else:
                                                    ingredients = [
                                                        str(ing) for ing in parsed if ing and str(ing).strip()
                                                    ]
                                            except Exception:
                                                ingredients = [str(ing) for ing in parsed if ing and str(ing).strip()]
                                        else:
                                            ingredients = [str(ing) for ing in parsed if ing and str(ing).strip()]
                                except Exception:
                                    if ingredients_data.strip():
                                        ingredients = [ingredients_data]
                            elif ingredients_data.strip():
                                ingredients = [ingredients_data]

                        # Process instructions
                        instructions = []
                        instructions_data = recipe.get("RecipeInstructions", [])
                        if isinstance(instructions_data, list):
                            instructions = [str(inst) for inst in instructions_data if inst]
                        elif isinstance(instructions_data, str):
                            try:
                                parsed = json.loads(instructions_data)
                                if isinstance(parsed, list):
                                    instructions = [str(inst) for inst in parsed if inst]
                                else:
                                    instructions = [instructions_data]
                            except Exception:
                                if instructions_data.strip():
                                    instructions = [instructions_data]

                        # Process calories
                        calories = recipe.get("Calories")
                        calories_display = "N/A"
                        if calories is not None:
                            try:
                                calories_display = f"{float(calories):.0f}"
                            except Exception:
                                calories_display = str(calories)

                        # Build recipe data object
                        recipe_data = {
                            "id": str(recipe.get("RecipeId", "")),
                            "name": recipe.get("Name", "Unknown Recipe"),
                            "image": image_url,
                            "calories": calories_display,
                            "rating": recipe.get("AggregatedRating"),
                            "reviews": recipe.get("ReviewCount"),
                            "url": (
                                f"https://www.food.com/recipe/"
                                f"{slugify(recipe.get('Name', ''))}-{recipe.get('RecipeId', '')}"
                            ),
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
                                "Prep Time": (
                                    f"{recipe.get('PrepTime', 'N/A')} minutes" if recipe.get("PrepTime") else "N/A"
                                ),
                                "Category": recipe.get("RecipeCategory", "N/A"),
                            },
                        }

                        recipes_data.append(recipe_data)

                    return jsonify(
                        {
                            "recipes": recipes_data,
                            "currentPage": page,
                            "totalPages": total_pages,
                            "totalResults": total_results,
                            "success": True,
                            "searchType": "text",  # Indicate fallback was used
                        }
                    )
                else:
                    return jsonify(
                        {"recipes": [], "success": True, "currentPage": 1, "totalPages": 0, "totalResults": 0}
                    )
            except Exception as fallback_error:
                print(f"Text search fallback also failed: {fallback_error}")
                return jsonify({"error": "Search failed", "success": False}), 500
        else:
            return jsonify({"error": error_message, "success": False}), 500
    except Exception as e:
        print(f"Error during vector search: {e}")
        return jsonify({"error": "Search failed", "success": False}), 500


@app.route("/suggest", methods=["GET"])
def suggest():
    print("[Suggest Route] Received request")
    query = request.args.get("query", "")
    print(f"[Suggest Route] Query parameter: '{query}'")

    if not query or len(query) < 2:  # Only suggest if query is at least 2 chars
        print("[Suggest Route] Query too short or empty, returning empty list.")
        return jsonify([])

    global db
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
        except Exception as text_search_error:
            print(f"[Suggest Route] Text search failed, falling back to regex: {text_search_error}")

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
