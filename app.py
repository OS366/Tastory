from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pymongo
from sentence_transformers import SentenceTransformer
import numpy as np
import datetime
import json
import re
import math # Required for math.ceil

app = Flask(__name__)
CORS(app)

# --- Load Embedding Model ---
MODEL_NAME = 'all-MiniLM-L6-v2'
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
RECIPE_EMBEDDING_FIELD = 'recipe_embedding_all_MiniLM_L6_v2'
RECIPE_VECTOR_INDEX_NAME = 'idx_recipes_vector'

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
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("MongoDB URI not found. Please set it in your .env file.")
        return None, None
    try:
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command('ping')
        db_name = os.getenv('DB_NAME', 'tastory')
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
    if not text: return ""
    text = text.lower()
    text = re.sub(r'\\s+', '-', text)
    text = re.sub(r'[^a-z0-9\\-]', '', text)
    text = re.sub(r'--+', '-', text)
    text = text.strip('-')
    return text

# --- Routes ---
@app.route('/')
def index():
    return jsonify({"message": "Tastory Chat API is running. Use the /chat endpoint."})

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    try:
        page = int(request.json.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    if page < 1:
        page = 1

    items_per_page = 10

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    global client, db
    if db is None:
        print("Database connection is not available. Attempting to reconnect...")
        client, db = connect_to_mongodb()
        if db is None:
             return jsonify({'reply': "Error: Could not connect to the database. Please check server logs."}), 500

    user_embedding = get_embedding(user_message)
    if not user_embedding:
        print("Failed to generate embedding for user message.")
        return jsonify({'reply': "Sorry, I couldn't understand your message well enough to search for recipes."}), 500

    print(f"Generated embedding for user message (first 3 dims): {user_embedding[:3]}...")

    recipes_collection_name = os.getenv('RECIPES_COLLECTION', 'recipes')
    recipes_collection = db[recipes_collection_name]

    vector_search_pipeline = [
        {
            "$vectorSearch": {
                "index": RECIPE_VECTOR_INDEX_NAME,
                "queryVector": user_embedding,
                "path": RECIPE_EMBEDDING_FIELD,
                "numCandidates": 200, # Fetch more candidates for better sorting before pagination
                "limit": 100  # Limit initial fetch, pagination happens after Python processing
            }
        },
        {
            "$project": {
                "_id": 0,
                "RecipeId": 1,
                "Name": 1,
                "Description": 1,
                "RecipeIngredientParts": 1,
                "RecipeInstructions": 1,
                "Images": 1,
                "MainImage": 1,
                "search_score": { "$meta": "vectorSearchScore" },
                "Calories": 1,
                "AuthorName": 1,
                "DatePublished": 1,
                "RecipeServings": 1,
                "RecipeYield": 1,
                "PrepTime": 1,
                "RecipeCategory": 1,
                "FatContent": 1, "SaturatedFatContent": 1, "CholesterolContent": 1,
                "SodiumContent": 1, "CarbohydrateContent": 1, "FiberContent": 1,
                "SugarContent": 1, "ProteinContent": 1
            }
        }
    ]

    try:
        all_top_candidates = list(recipes_collection.aggregate(vector_search_pipeline, maxTimeMS=30000))
        print(f"DEBUG: Candidates retrieved from DB for pagination: {len(all_top_candidates)}")

        recipes_with_images = []
        recipes_without_images = []

        for recipe_item in all_top_candidates: # Renamed recipe to recipe_item to avoid conflict with outer scope if any
            image_url_to_use = None
            main_image_val = recipe_item.get('MainImage')
            images_val = recipe_item.get('Images')
            if main_image_val and isinstance(main_image_val, str) and main_image_val.strip().lower().startswith(("http://", "https://")):
                image_url_to_use = main_image_val.strip()
            if not image_url_to_use and images_val and isinstance(images_val, list) and len(images_val) > 0:
                if isinstance(images_val[0], str) and images_val[0].strip().lower().startswith(("http://", "https://")):
                    image_url_to_use = images_val[0].strip()
            
            if image_url_to_use:
                recipe_item['_display_image_url'] = image_url_to_use 
                recipes_with_images.append(recipe_item)
            else:
                recipes_without_images.append(recipe_item)
        
        def get_calories_for_sorting(recipe_item_sort):
            calories_val = recipe_item_sort.get("Calories")
            if calories_val is None: return float('inf') 
            try: return float(calories_val)
            except (ValueError, TypeError): return float('inf')

        sorted_with_images = sorted(recipes_with_images, key=get_calories_for_sorting)
        sorted_without_images = sorted(recipes_without_images, key=get_calories_for_sorting)
        
        processed_results = sorted_with_images + sorted_without_images
        total_processed_results = len(processed_results)
        total_pages = math.ceil(total_processed_results / items_per_page)
        if page > total_pages and total_pages > 0: # Adjust page if out of bounds
            page = total_pages
        
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_results = processed_results[start_index:end_index]
        
        print(f"DEBUG: Total processed results: {total_processed_results}, Page: {page}, Total Pages: {total_pages}, Displaying {len(paginated_results)} items")
        
        bot_reply = ""
        if not paginated_results:
            if page == 1: # Only show no results message if it's the first page and nothing came through
                 bot_reply = "I couldn\'t find any recipes matching your query. Try phrasing it differently!"
            else: # On subsequent pages, if empty, means user paged too far (though we try to cap page number)
                 bot_reply = "<p class='text-center text-gray-500 dark:text-gray-400'>No more results on this page.</p>"
        else:
            for i, recipe in enumerate(paginated_results): # Iterate over paginated_results
                recipe_unique_id = recipe.get('RecipeId', f"page{page}_{i}") # Ensure unique IDs across pages too
                recipe_id_str = str(recipe.get('RecipeId', ''))
                recipe_name = recipe.get('Name', 'Recipe')
                recipe_slug = slugify(recipe_name)
                current_image_url = recipe.get('_display_image_url') 
                bot_reply += f'<div class="relative h-80 rounded-lg shadow-lg overflow-hidden group hover:shadow-xl transition-shadow duration-300">'
                if current_image_url:
                    bot_reply += f'<img src="{current_image_url}" alt="{recipe.get("Name", "N/A")}" class="absolute inset-0 w-full h-full object-cover">'
                else: 
                    bot_reply += '<div class="absolute inset-0 w-full h-full bg-gray-400 dark:bg-gray-600 flex items-center justify-center"><p class=\"text-gray-600 dark:text-gray-400 text-sm\">No Image</p></div>'
                bot_reply += '<div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/60 to-transparent"></div>'
                bot_reply += '<div class="relative z-10 flex flex-col h-full p-4 text-white">'
                bot_reply += f'<h3 class="text-2xl font-bold mb-1 drop-shadow-md">{recipe.get("Name", "N/A")}</h3>'
                calories = recipe.get('Calories')
                calories_display = "N/A"
                if calories is not None:
                    try: calories_display = f"{float(calories):.0f}"
                    except (ValueError, TypeError): calories_display = str(calories)
                bot_reply += f'<p class="text-sm text-gray-200 mb-3 drop-shadow-sm">Calories: {calories_display}</p>'
                bot_reply += '<div class="mt-auto">' 
                bot_reply += '<div class="flex flex-wrap justify-center items-center gap-4 mb-2 w-full">' 
                icon_base_classes = "text-4xl text-white/80 hover:text-white opacity-100 transition-opacity duration-200 cursor-pointer drop-shadow-sm"
                drawer_id_info = f"drawer-info-{recipe_unique_id}"
                content_id_info = f"content-info-{recipe_unique_id}"
                drawer_id_ingredients = f"drawer-ingredients-{recipe_unique_id}"
                content_id_ingredients = f"content-ingredients-{recipe_unique_id}"
                drawer_id_instructions = f"drawer-instructions-{recipe_unique_id}"
                content_id_instructions = f"content-instructions-{recipe_unique_id}"
                drawer_id_nutrition = f"drawer-nutrition-{recipe_unique_id}"
                content_id_nutrition = f"content-nutrition-{recipe_unique_id}"
                bot_reply += f'<button class="{icon_base_classes}" data-drawer-target="{drawer_id_info}" title="Info"><i class="fas fa-info-circle"></i></button>'
                bot_reply += f'<button class="{icon_base_classes}" data-drawer-target="{drawer_id_ingredients}" title="Ingredients"><i class="fas fa-apple-alt"></i></button>'
                bot_reply += f'<button class="{icon_base_classes}" data-drawer-target="{drawer_id_instructions}" title="Instructions"><i class="fas fa-book-open"></i></button>'
                bot_reply += f'<button class="{icon_base_classes}" data-drawer-target="{drawer_id_nutrition}" title="Nutrition"><i class="fas fa-chart-pie"></i></button>'
                if recipe_id_str: food_com_url = f"https://www.food.com/recipe/{recipe_slug}-{recipe_id_str}"; bot_reply += f'<a href="{food_com_url}" target="_blank" class="{icon_base_classes}" title="View on Food.com"><i class="fas fa-external-link-alt"></i></a>'
                bot_reply += '</div>' 
                bot_reply += '</div>' 
                bot_reply += '</div>' 
                drawer_classes = "fixed top-0 right-0 h-full w-80 bg-slate-800/90 dark:bg-black/90 backdrop-blur-lg shadow-2xl p-6 text-gray-100 transform translate-x-full transition-transform duration-300 ease-in-out z-40 overflow-y-auto"
                bot_reply += f'<div id="{drawer_id_info}" class="{drawer_classes}">'
                bot_reply += f'    <div class="flex items-center justify-between mb-4"> <h4 class="text-xl font-semibold text-white mr-2 flex-grow">Recipe Information</h4> <button class="speak-drawer-button text-gray-300 hover:text-white text-xl mr-3" title="Read content aloud" data-content-target="{content_id_info}"><i class="fas fa-volume-up"></i></button> <button data-close-drawer="{drawer_id_info}" class="text-gray-300 hover:text-white text-3xl leading-none">&times;</button> </div>'
                bot_reply += f'    <div id="{content_id_info}" class="drawer-readable-content space-y-2 text-sm">'
                bot_reply += f'        <p><span class="font-semibold">Author:</span> {recipe.get("AuthorName", "N/A")}</p>'
                date_published_val = recipe.get('DatePublished')
                date_str = "N/A"
                if date_published_val:
                    if isinstance(date_published_val, datetime.datetime): date_str = date_published_val.strftime('%Y-%m-%d')
                    elif isinstance(date_published_val, str):
                        try: date_str = datetime.datetime.fromisoformat(date_published_val.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except ValueError: date_str = date_published_val
                    else: date_str = str(date_published_val)
                bot_reply += f'        <p><span class="font-semibold">Published:</span> {date_str}</p>'
                servings = recipe.get('RecipeServings')
                recipe_yield = recipe.get('RecipeYield')
                serv_yield_str = "N/A"
                if servings is not None and str(servings).lower() != 'nan' and str(servings).strip() and str(servings) != 'character(0)': serv_yield_str = str(servings)
                elif recipe_yield and str(recipe_yield).lower() != 'nan' and str(recipe_yield).strip() and str(recipe_yield) != 'character(0)': serv_yield_str = str(recipe_yield)
                bot_reply += f'        <p><span class="font-semibold">Servings/Yield:</span> {serv_yield_str}</p>'
                prep_time = recipe.get('PrepTime')
                prep_time_str = "N/A"
                if prep_time is not None and str(prep_time).lower() != 'nan': prep_time_str = f"{prep_time} minutes"
                bot_reply += f'        <p><span class="font-semibold">Prep Time:</span> {prep_time_str}</p>'
                category = recipe.get('RecipeCategory')
                category_str = "N/A"
                if category: category_str = category[0] if isinstance(category, list) and category else (category if isinstance(category, str) else 'N/A')
                bot_reply += f'        <p><span class="font-semibold">Category:</span> {category_str}</p>'
                bot_reply += f'    </div>' # Close content_id_info
                bot_reply += f'</div>' # Close drawer_id_info

                bot_reply += f'<div id="{drawer_id_ingredients}" class="{drawer_classes}">'
                bot_reply += f'    <div class="flex items-center justify-between mb-4"> <h4 class="text-xl font-semibold text-white mr-2 flex-grow">Ingredients</h4> <button class="speak-drawer-button text-gray-300 hover:text-white text-xl mr-3" title="Read content aloud" data-content-target="{content_id_ingredients}"><i class="fas fa-volume-up"></i></button> <button data-close-drawer="{drawer_id_ingredients}" class="text-gray-300 hover:text-white text-3xl leading-none">&times;</button> </div>'
                bot_reply += f'    <div id="{content_id_ingredients}" class="drawer-readable-content">'
                ingredients_data = recipe.get('RecipeIngredientParts')
                ingredients_str_html = '<p class="text-sm">N/A</p>' # Default value
                actual_ingredients_list = None

                if isinstance(ingredients_data, list):
                    actual_ingredients_list = ingredients_data
                elif isinstance(ingredients_data, str):
                    if ingredients_data.strip().startswith('[') and ingredients_data.strip().endswith(']'):
                        try:
                            parsed_list = json.loads(ingredients_data)
                            if isinstance(parsed_list, list):
                                actual_ingredients_list = parsed_list
                        except json.JSONDecodeError:
                            # If JSON parsing fails for a string that looks like a list, treat it as a single string ingredient
                            if ingredients_data.strip(): # ensure it's not empty after strip
                                ingredients_str_html = f'<p class="text-sm">{ingredients_data}</p>'
                            # else, default N/A remains
                    elif ingredients_data.strip(): # If it's a non-empty string not appearing to be a list
                        ingredients_str_html = f'<p class="text-sm">{ingredients_data}</p>'
                    # else, (empty string or only whitespace) default N/A remains

                if actual_ingredients_list is not None: # This means it was successfully parsed as a list or was a list originally
                    if actual_ingredients_list: # Check if the list is not empty
                        li_items = "".join([f'<li>{str(ing)}</li>' for ing in actual_ingredients_list if ing and str(ing).strip()])
                        if li_items: # If any valid list items were generated
                            ingredients_str_html = f'<ul class="list-disc list-inside space-y-1 text-sm">{li_items}</ul>'
                        else: # All items were empty or invalid
                            ingredients_str_html = '<p class="text-sm">No ingredients listed.</p>'
                    else: # The list was empty
                        ingredients_str_html = '<p class="text-sm">No ingredients listed.</p>'
                # If actual_ingredients_list is None, ingredients_str_html has already been set (either to N/A or the string content)

                bot_reply += ingredients_str_html
                bot_reply += f'    </div>' # Close content_id_ingredients
                bot_reply += f'</div>' # Close drawer_id_ingredients

                bot_reply += f'<div id="{drawer_id_instructions}" class="{drawer_classes}">'
                bot_reply += f'    <div class="flex items-center justify-between mb-4"> <h4 class="text-xl font-semibold text-white mr-2 flex-grow">Instructions</h4> <button class="speak-drawer-button text-gray-300 hover:text-white text-xl mr-3" title="Read content aloud" data-content-target="{content_id_instructions}"><i class="fas fa-volume-up"></i></button> <button data-close-drawer="{drawer_id_instructions}" class="text-gray-300 hover:text-white text-3xl leading-none">&times;</button> </div>'
                bot_reply += f'    <div id="{content_id_instructions}" class="drawer-readable-content">'
                bot_reply += f'        <ol class="list-decimal list-inside space-y-1 text-sm">'
                instructions_data = recipe.get('RecipeInstructions', [])
                parsed_instructions = []
                if isinstance(instructions_data, list): parsed_instructions = instructions_data
                elif isinstance(instructions_data, str):
                    try:
                        parsed_instructions = json.loads(instructions_data)
                        if not isinstance(parsed_instructions, list): parsed_instructions = [str(instructions_data)]
                    except json.JSONDecodeError: parsed_instructions = [instructions_data]
                if parsed_instructions:
                    for step in parsed_instructions: bot_reply += f'<li>{step}</li>'
                else: bot_reply += '<li>No instructions provided.</li>'
                bot_reply += f'        </ol>'
                bot_reply += f'    </div>' # Close content_id_instructions
                bot_reply += f'</div>' # Close drawer_id_instructions

                bot_reply += f'<div id="{drawer_id_nutrition}" class="{drawer_classes}">'
                bot_reply += f'    <div class="flex items-center justify-between mb-4"> <h4 class="text-xl font-semibold text-white mr-2 flex-grow">Nutrition (per serving)</h4> <button class="speak-drawer-button text-gray-300 hover:text-white text-xl mr-3" title="Read content aloud" data-content-target="{content_id_nutrition}"><i class="fas fa-volume-up"></i></button> <button data-close-drawer="{drawer_id_nutrition}" class="text-gray-300 hover:text-white text-3xl leading-none">&times;</button> </div>'
                bot_reply += f'    <div id="{content_id_nutrition}" class="drawer-readable-content space-y-0.5 text-sm">'
                bot_reply += f'        <p>• Fat: {recipe.get("FatContent", "N/A")}g</p>'
                bot_reply += f'        <p>• Saturated Fat: {recipe.get("SaturatedFatContent", "N/A")}g</p>'
                bot_reply += f'        <p>• Cholesterol: {recipe.get("CholesterolContent", "N/A")}mg</p>'
                bot_reply += f'        <p>• Sodium: {recipe.get("SodiumContent", "N/A")}mg</p>'
                bot_reply += f'        <p>• Carbs: {recipe.get("CarbohydrateContent", "N/A")}g</p>'
                bot_reply += f'        <p>• Fiber: {recipe.get("FiberContent", "N/A")}g</p>'
                bot_reply += f'        <p>• Sugar: {recipe.get("SugarContent", "N/A")}g</p>'
                bot_reply += f'        <p>• Protein: {recipe.get("ProteinContent", "N/A")}g</p>'
                bot_reply += f'    </div>' # Close content_id_nutrition
                bot_reply += f'</div>' # Close drawer_id_nutrition
                bot_reply += '</div>' # --- Card End ---

        return jsonify({
            'reply': bot_reply, 
            'currentPage': page, 
            'totalPages': total_pages, 
            'totalResults': total_processed_results
        })

    except pymongo.errors.OperationFailure as e:
        print(f"MongoDB OperationFailure: {e.details}")
        error_message = str(e.details.get('errmsg', 'Unknown MongoDB error'))
        bot_reply = f"Sorry, I had trouble searching for recipes due to a database error: {error_message}"
        if "index not found" in error_message.lower() or "no such index" in error_message.lower():
             bot_reply = f"Sorry, I encountered an issue with the recipe search index ({RECIPE_VECTOR_INDEX_NAME}). Please ensure it\'s set up correctly in MongoDB Atlas."
        elif "vector search" in error_message.lower() and "wrong number of dimensions" in error_message.lower():
             bot_reply = f"Sorry, the search index ({RECIPE_VECTOR_INDEX_NAME}) seems to have a dimension mismatch. Expected 384 dimensions."
        print(f"DEBUG: bot_reply before jsonify (on error): {bot_reply}")
        return jsonify({'reply': bot_reply}), 500
    except Exception as e:
        print(f"Error during vector search or processing results: {e}")
        bot_reply = "Sorry, I encountered an unexpected error while searching for recipes."
        print(f"DEBUG: bot_reply before jsonify (on general exception): {bot_reply}")
        return jsonify({'reply': bot_reply}), 500

@app.route('/suggest', methods=['GET'])
def suggest():
    print("[Suggest Route] Received request")
    query = request.args.get('query', '')
    print(f"[Suggest Route] Query parameter: '{query}'")

    if not query or len(query) < 2: # Only suggest if query is at least 2 chars
        print("[Suggest Route] Query too short or empty, returning empty list.")
        return jsonify([])

    global db
    if db is None:
        print("[Suggest Route] DB connection is None, returning empty list.")
        return jsonify([]) 

    recipes_collection_name = os.getenv('RECIPES_COLLECTION', 'recipes')
    recipes_collection = db[recipes_collection_name]
    print(f"[Suggest Route] Using collection: {recipes_collection_name}")

    try:
        regex_query = f"^{re.escape(query)}"
        print(f"[Suggest Route] Constructed regex: '{regex_query}'")
        
        print("[Suggest Route] Attempting to query database...")
        suggestions_cursor = recipes_collection.find(
            {"Name": {"$regex": regex_query, "$options": "i"}},
            {"Name": 1, "_id": 0} # Project only the name
        ).limit(7) # Limit to 7 suggestions
        
        # Convert cursor to list to see results immediately for logging
        suggestions_list_from_db = list(suggestions_cursor)
        print(f"[Suggest Route] Suggestions from DB (raw list): {suggestions_list_from_db}")

        suggestion_names = list(set([s['Name'] for s in suggestions_list_from_db if 'Name' in s]))
        print(f"[Suggest Route] Processed suggestion names (unique, limited): {suggestion_names[:7]}")
        
        response_data = suggestion_names[:7]
        print(f"[Suggest Route] Returning JSON response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        print(f"[Suggest Route] Error in /suggest endpoint: {e}")
        # Consider the type of error, if it's a DB error, you might want to return a specific HTTP status
        return jsonify([]), 500 # Return empty list and 500 on error

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 