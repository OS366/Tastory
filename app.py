import datetime
import json
import logging
import math
import os
import re
import uuid
from datetime import datetime, timedelta

import pymongo
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import stripe

app = Flask(__name__)
CORS(app)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

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


# --- Helper function to log search queries ---
def log_search_query(query, session_id, results_count=None):
    """Log search queries for trending calculation"""
    if db is None:
        return
    
    try:
        search_logs = db.search_logs
        log_entry = {
            "query": query.lower().strip(),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "results_count": results_count
        }
        search_logs.insert_one(log_entry)
    except Exception as e:
        print(f"Error logging search query: {e}")


# --- Helper function to calculate trending searches ---
def calculate_trending_searches():
    """Calculate trending searches based on recent activity"""
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
            {
                "$match": {
                    "timestamp": {"$gte": twenty_four_hours_ago}
                }
            },
            {
                "$group": {
                    "_id": "$query",
                    "total_count": {"$sum": 1},
                    "recent_count": {
                        "$sum": {
                            "$cond": [{"$gte": ["$timestamp", one_hour_ago]}, 1, 0]
                        }
                    },
                    "medium_count": {
                        "$sum": {
                            "$cond": [{"$gte": ["$timestamp", six_hours_ago]}, 1, 0]
                        }
                    }
                }
            },
            {
                "$match": {
                    "total_count": {"$gte": 5}  # Minimum 5 searches to qualify
                }
            },
            {
                "$addFields": {
                    "score": {
                        "$divide": [
                            {
                                "$add": [
                                    {"$multiply": ["$recent_count", 3]},
                                    {"$multiply": ["$medium_count", 2]},
                                    "$total_count"
                                ]
                            },
                            2  # time decay factor
                        ]
                    }
                }
            },
            {
                "$sort": {"score": -1}
            },
            {
                "$limit": 10
            },
            {
                "$project": {
                    "_id": 0,
                    "query": "$_id",
                    "count": "$total_count",
                    "score": 1
                }
            }
        ]
        
        trending = list(search_logs.aggregate(pipeline))
        
        # Calculate trend direction
        for item in trending:
            # This is simplified - in production, you'd compare with previous period
            if item.get("score", 0) > 10:
                item["trend"] = "up"
            else:
                item["trend"] = "stable"
            item["percentChange"] = 0  # Placeholder
        
        return trending
        
    except Exception as e:
        print(f"Error calculating trending searches: {e}")
        return []


# --- Routes ---
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
                "/trending": "Get trending recipe searches",
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
    user_message = data.get("message") or data.get("query", "")  # Handle both formats
    user_message = user_message.strip()
    page = data.get("page", 1)
    per_page = 12  # Fixed at 12 for 4x3 grid

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Log the search query
    try:
        session_id = request.headers.get('X-Session-ID', str(uuid.uuid4()))
        log_search_query(user_message, session_id, results_count=None)
    except Exception as e:
        print(f"Failed to log search query: {e}")

    global client, db
    if db is None:
        print("Database connection is not available. Attempting to reconnect...")
        client, db = connect_to_mongodb()
        if db is None:
            return jsonify({"reply": "Error: Could not connect to the database. Please check server logs."}), 500

    try:
        # Try exact text search first
        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
        
        # Split the query into words for exact matching
        search_terms = user_message.lower().split()
        
        # Define cuisine categories and their related terms
        cuisine_categories = {
            "indian": ["indian", "chole", "puri", "curry", "masala", "naan", "roti", "biryani", "samosa"],
            "italian": ["italian", "pasta", "pizza", "risotto", "lasagna"],
            "dessert": ["dessert", "ice cream", "cake", "pie", "cookie", "chocolate", "sweet"],
            "chinese": ["chinese", "noodles", "fried rice", "dimsum", "spring roll"],
            "mexican": ["mexican", "taco", "burrito", "enchilada", "quesadilla"],
        }

        # Detect cuisine type from search terms
        detected_cuisine = None
        for cuisine, terms in cuisine_categories.items():
            if any(term in search_terms for term in terms):
                detected_cuisine = cuisine
                break

        # Create a more strict text search query with cuisine filtering
        query_conditions = []
        
        # Add exact word matching conditions
        for term in search_terms:
            query_conditions.append({
                "$or": [
                    {"Name": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                    {"RecipeCategory": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                    {"Keywords": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                    {"RecipeIngredientParts": {"$regex": f"\\b{term}\\b", "$options": "i"}}
                ]
            })

        # If cuisine is detected, add cuisine-specific filtering
        if detected_cuisine:
            cuisine_terms = cuisine_categories[detected_cuisine]
            cuisine_condition = {
                "$or": [
                    {"RecipeCategory": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}},
                    {"Keywords": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}},
                    {"Name": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}}
                ]
            }
            query_conditions.append(cuisine_condition)

        # Combine all conditions with $and
        exact_match_query = {"$and": query_conditions}

        # Execute exact match search
        exact_results = list(recipes_collection.find(
            exact_match_query,
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
            }
        ).limit(30))

        # If exact matches are too few, try fuzzy text search
        if len(exact_results) < 5:  # Threshold for minimum results
            # Create fuzzy search query
            fuzzy_terms = []
            for term in search_terms:
                fuzzy_terms.append({"$regex": f"{term}", "$options": "i"})
            
            fuzzy_query = {
                "$and": [
                    {
                        "$or": [
                            {"Name": {"$in": fuzzy_terms}},
                            {"RecipeCategory": {"$in": fuzzy_terms}},
                            {"Keywords": {"$in": fuzzy_terms}},
                            {"RecipeIngredientParts": {"$in": fuzzy_terms}}
                        ]
                    }
                ]
            }

            # If cuisine is detected, add cuisine filtering to fuzzy search
            if detected_cuisine:
                cuisine_terms = cuisine_categories[detected_cuisine]
                cuisine_condition = {
                    "$or": [
                        {"RecipeCategory": {"$regex": f"({'|'.join(cuisine_terms)})", "$options": "i"}},
                        {"Keywords": {"$regex": f"({'|'.join(cuisine_terms)})", "$options": "i"}},
                        {"Name": {"$regex": f"({'|'.join(cuisine_terms)})", "$options": "i"}}
                    ]
                }
                fuzzy_query["$and"].append(cuisine_condition)

            # Execute fuzzy search
            fuzzy_results = list(recipes_collection.find(
                fuzzy_query,
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
                }
            ).limit(30))

            # Combine exact and fuzzy results, removing duplicates
            seen_ids = set(recipe["RecipeId"] for recipe in exact_results)
            for recipe in fuzzy_results:
                if recipe["RecipeId"] not in seen_ids:
                    exact_results.append(recipe)
                    seen_ids.add(recipe["RecipeId"])

        # Process results
        recipes_with_images = []
        recipes_without_images = []

        for recipe in exact_results:
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

        # Format results
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
            if isinstance(ingredients_data, list):
                ingredients = [str(ing) for ing in ingredients_data if ing and str(ing).strip()]
            elif isinstance(ingredients_data, str):
                ingredients = [ingredients_data]

            # Process instructions
            instructions = []
            instructions_data = recipe.get("RecipeInstructions", [])
            if isinstance(instructions_data, list):
                instructions = [str(inst) for inst in instructions_data if inst]
            elif isinstance(instructions_data, str):
                instructions = [instructions_data]

            # Process calories
            calories = recipe.get("Calories")
            calories_display = "N/A"
            if calories is not None:
                try:
                    calories_display = f"{float(calories):.0f}"
                except:
                    calories_display = str(calories)

            recipe_data = {
                "id": str(recipe.get("RecipeId", "")),
                "name": recipe.get("Name", "Unknown Recipe"),
                "image": image_url,
                "calories": calories_display,
                "rating": recipe.get("AggregatedRating"),
                "reviews": recipe.get("ReviewCount"),
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

        return jsonify({
            "recipes": recipes_data,
            "currentPage": page,
            "totalPages": total_pages,
            "totalResults": total_results,
            "success": True,
            "searchType": "exact",
            "detectedCuisine": detected_cuisine
        })

    except Exception as e:
        print(f"Error during search: {e}")
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


@app.route("/trending", methods=["GET"])
def trending():
    """Get trending searches"""
    try:
        # Check cache first
        if db is not None:
            trending_cache = db.trending_cache
            cache_doc = trending_cache.find_one({"_id": "current"})
            
            # Use cache if it's less than 15 minutes old
            if cache_doc:
                cache_age = datetime.utcnow() - cache_doc.get("updated_at", datetime.min)
                if cache_age < timedelta(minutes=15):
                    return jsonify({
                        "trending": cache_doc.get("trending", []),
                        "lastUpdated": cache_doc.get("updated_at").isoformat() + "Z"
                    })
        
        # Calculate fresh trending data
        trending_data = calculate_trending_searches()
        
        # Update cache
        if db is not None:
            trending_cache = db.trending_cache
            trending_cache.replace_one(
                {"_id": "current"},
                {
                    "_id": "current",
                    "trending": trending_data,
                    "updated_at": datetime.utcnow()
                },
                upsert=True
            )
        
        return jsonify({
            "trending": trending_data,
            "lastUpdated": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        print(f"Error in /trending endpoint: {e}")
        return jsonify({"error": "Failed to fetch trending searches"}), 500


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Tastory Premium',
                        'description': 'Access to premium features including advanced search, analytics, and more.',
                    },
                    'unit_amount': 500,  # $5.00 in cents
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=os.getenv('FRONTEND_URL', 'http://localhost:3000') + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=os.getenv('FRONTEND_URL', 'http://localhost:3000') + '/canceled',
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403


@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': str(e)}), 400

    # Handle the event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        # Set up the customer for success
        handle_checkout_session(session)
    elif event.type == 'customer.subscription.updated':
        subscription = event.data.object
        handle_subscription_updated(subscription)
    elif event.type == 'customer.subscription.deleted':
        subscription = event.data.object
        handle_subscription_deleted(subscription)
    elif event.type == 'invoice.paid':
        invoice = event.data.object
        handle_invoice_paid(invoice)
    elif event.type == 'invoice.payment_failed':
        invoice = event.data.object
        handle_invoice_failed(invoice)

    return jsonify({'status': 'success'})

def handle_checkout_session(session):
    """Handle successful checkout session."""
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in session")
        return
    
    try:
        # Get customer details
        customer = stripe.Customer.retrieve(customer_id)
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Store subscription info in MongoDB
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {'customer_id': customer_id},
                {
                    '$set': {
                        'customer_id': customer_id,
                        'subscription_id': subscription_id,
                        'email': customer.email,
                        'status': subscription.status,
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
    except Exception as e:
        logging.error(f"Error handling checkout session: {str(e)}")

def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    
    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in subscription update")
        return
        
    try:
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {'subscription_id': subscription_id},
                {
                    '$set': {
                        'status': subscription.status,
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    except Exception as e:
        logging.error(f"Error handling subscription update: {str(e)}")

def handle_subscription_deleted(subscription):
    """Handle subscription cancellations."""
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    
    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in subscription deletion")
        return
        
    try:
        if db is not None:
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {'subscription_id': subscription_id},
                {
                    '$set': {
                        'status': 'canceled',
                        'canceled_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    except Exception as e:
        logging.error(f"Error handling subscription deletion: {str(e)}")

def handle_invoice_paid(invoice):
    """Handle successful invoice payments."""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in invoice")
        return
        
    try:
        if db is not None:
            # Update subscription payment status
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {'subscription_id': subscription_id},
                {
                    '$set': {
                        'last_payment_status': 'paid',
                        'last_payment_date': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Store invoice record
            invoices = db.invoices
            invoices.insert_one({
                'invoice_id': invoice.id,
                'customer_id': customer_id,
                'subscription_id': subscription_id,
                'amount_paid': invoice.amount_paid,
                'status': invoice.status,
                'created_at': datetime.fromtimestamp(invoice.created),
                'payment_date': datetime.utcnow()
            })
    except Exception as e:
        logging.error(f"Error handling invoice payment: {str(e)}")

def handle_invoice_failed(invoice):
    """Handle failed invoice payments."""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    if not customer_id or not subscription_id:
        logging.error("Missing customer_id or subscription_id in failed invoice")
        return
        
    try:
        if db is not None:
            # Update subscription payment status
            subscriptions = db.subscriptions
            subscriptions.update_one(
                {'subscription_id': subscription_id},
                {
                    '$set': {
                        'last_payment_status': 'failed',
                        'last_payment_attempt': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Store failed invoice record
            invoices = db.invoices
            invoices.insert_one({
                'invoice_id': invoice.id,
                'customer_id': customer_id,
                'subscription_id': subscription_id,
                'amount_due': invoice.amount_due,
                'status': invoice.status,
                'created_at': datetime.fromtimestamp(invoice.created),
                'failure_date': datetime.utcnow(),
                'failure_reason': invoice.get('last_payment_error', {}).get('message', 'Unknown error')
            })
    except Exception as e:
        logging.error(f"Error handling failed invoice: {str(e)}")

@app.route("/search/cuisine", methods=["POST"])
def cuisine_search():
    data = request.get_json()
    query = data.get("query", "").strip()
    page = data.get("page", 1)
    per_page = 12

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        recipes_collection = db[os.getenv("RECIPES_COLLECTION", "recipes")]
        
        # Define cuisine categories
        cuisine_mapping = {
            "indian": ["indian", "chole", "puri", "curry", "masala", "naan", "roti", "biryani", "samosa"],
            "italian": ["italian", "pasta", "pizza", "risotto", "lasagna"],
            "dessert": ["dessert", "ice cream", "cake", "pie", "cookie", "chocolate", "sweet"],
            "chinese": ["chinese", "noodles", "fried rice", "dimsum", "spring roll"],
            "mexican": ["mexican", "taco", "burrito", "enchilada", "quesadilla"],
        }

        # Detect cuisine from query
        query_terms = query.lower().split()
        detected_cuisine = None
        for cuisine, terms in cuisine_mapping.items():
            if any(term in query_terms for term in terms):
                detected_cuisine = cuisine
                break

        if not detected_cuisine:
            return jsonify({"error": "No cuisine type detected in query"}), 400

        # Create search query
        cuisine_terms = cuisine_mapping[detected_cuisine]
        search_query = {
            "$and": [
                # Must match the cuisine type
                {
                    "$or": [
                        {"RecipeCategory": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}},
                        {"Keywords": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}},
                        {"Name": {"$regex": f"\\b({'|'.join(cuisine_terms)})\\b", "$options": "i"}}
                    ]
                },
                # Must match all search terms
                *[{
                    "$or": [
                        {"Name": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                        {"RecipeCategory": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                        {"Keywords": {"$regex": f"\\b{term}\\b", "$options": "i"}},
                        {"RecipeIngredientParts": {"$regex": f"\\b{term}\\b", "$options": "i"}}
                    ]
                } for term in query_terms]
            ]
        }

        # Execute search
        results = list(recipes_collection.find(
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
            }
        ).limit(30))

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

        # Format results
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
            if isinstance(ingredients_data, list):
                ingredients = [str(ing) for ing in ingredients_data if ing and str(ing).strip()]
            elif isinstance(ingredients_data, str):
                ingredients = [ingredients_data]

            # Process instructions
            instructions = []
            instructions_data = recipe.get("RecipeInstructions", [])
            if isinstance(instructions_data, list):
                instructions = [str(inst) for inst in instructions_data if inst]
            elif isinstance(instructions_data, str):
                instructions = [instructions_data]

            # Process calories
            calories = recipe.get("Calories")
            calories_display = "N/A"
            if calories is not None:
                try:
                    calories_display = f"{float(calories):.0f}"
                except:
                    calories_display = str(calories)

            recipe_data = {
                "id": str(recipe.get("RecipeId", "")),
                "name": recipe.get("Name", "Unknown Recipe"),
                "image": image_url,
                "calories": calories_display,
                "rating": recipe.get("AggregatedRating"),
                "reviews": recipe.get("ReviewCount"),
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

        return jsonify({
            "recipes": recipes_data,
            "currentPage": page,
            "totalPages": total_pages,
            "totalResults": total_results,
            "success": True,
            "cuisine": detected_cuisine
        })

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
