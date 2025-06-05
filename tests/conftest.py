"""
Test configuration and fixtures for Tastory application.
"""
import os
import pytest
import json
from unittest.mock import Mock, patch
import mongomock
from datetime import datetime, timedelta

# Import the Flask app and modules to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, spell_correct_query, calculate_walk_meter, estimate_serving_size, safe_get_servings
from nutritional_database import calculate_recipe_calories


@pytest.fixture(scope="session")
def test_app():
    """Create application for testing."""
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "MONGODB_URI": "mongodb://test",
        "DB_NAME": "tastory_test",
        "RECIPES_COLLECTION": "recipes_test",
        "REVIEWS_COLLECTION": "reviews_test"
    })
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def mock_db():
    """Create a mock MongoDB database for testing."""
    client = mongomock.MongoClient()
    db = client["tastory_test"]
    
    # Mock the global db variable in app.py
    with patch('app.db', db):
        yield db


@pytest.fixture(scope="function")
def sample_recipes():
    """Sample recipe data for testing."""
    return [
        {
            "RecipeId": 1,
            "Name": "Chicken Biryani",
            "Description": "Delicious Indian rice dish",
            "RecipeIngredientParts": ["2 cups basmati rice", "500g chicken", "2 onions"],
            "RecipeIngredientQuantities": ["2 cups", "500g", "2"],
            "RecipeInstructions": ["Cook rice", "Fry chicken", "Layer and cook"],
            "Calories": 450,
            "RecipeServings": "4",
            "RecipeYield": None,
            "PrepTime": 60,
            "RecipeCategory": "Indian",
            "AggregatedRating": 4.5,
            "ReviewCount": 125,
            "AuthorName": "Chef Kumar",
            "DatePublished": "2024-01-01",
            "MainImage": "https://example.com/biryani.jpg",
            "Images": ["https://example.com/biryani.jpg"],
            "FatContent": 15.2,
            "SaturatedFatContent": 4.1,
            "CholesterolContent": 65,
            "SodiumContent": 890,
            "CarbohydrateContent": 52.3,
            "FiberContent": 2.8,
            "SugarContent": 3.2,
            "ProteinContent": 28.5
        },
        {
            "RecipeId": 2,
            "Name": "Pizza Fondue",
            "Description": "Cheesy pizza fondue for sharing",
            "RecipeIngredientParts": ["2 cups cheese", "1 cup milk", "pizza seasoning"],
            "RecipeIngredientQuantities": ["2 cups", "1 cup", "1 tbsp"],
            "RecipeInstructions": ["Melt cheese", "Add milk", "Season and serve"],
            "Calories": 522.5,
            "RecipeServings": None,
            "RecipeYield": None,
            "PrepTime": 20,
            "RecipeCategory": "Appetizer",
            "AggregatedRating": 3.8,
            "ReviewCount": 45,
            "AuthorName": "Food Network",
            "DatePublished": "2024-02-15",
            "MainImage": None,
            "Images": [],
            "FatContent": 35.2,
            "SaturatedFatContent": 22.1,
            "CholesterolContent": 110,
            "SodiumContent": 1250,
            "CarbohydrateContent": 15.3,
            "FiberContent": 0.5,
            "SugarContent": 12.1,
            "ProteinContent": 32.8
        },
        {
            "RecipeId": 3,
            "Name": "Chocolate Chip Cookies",
            "Description": "Classic homemade cookies",
            "RecipeIngredientParts": ["2 cups flour", "1 cup butter", "chocolate chips"],
            "RecipeIngredientQuantities": ["2 cups", "1 cup", "1 cup"],
            "RecipeInstructions": ["Mix ingredients", "Shape cookies", "Bake at 350F"],
            "Calories": 320,
            "RecipeServings": "24",
            "RecipeYield": "24 cookies",
            "PrepTime": 45,
            "RecipeCategory": "Dessert",
            "AggregatedRating": 4.8,
            "ReviewCount": 89,
            "AuthorName": "Baker Betty",
            "DatePublished": "2024-03-10",
            "MainImage": "https://example.com/cookies.jpg",
            "Images": ["https://example.com/cookies.jpg"],
            "FatContent": 8.2,
            "SaturatedFatContent": 5.1,
            "CholesterolContent": 25,
            "SodiumContent": 180,
            "CarbohydrateContent": 22.3,
            "FiberContent": 1.2,
            "SugarContent": 12.5,
            "ProteinContent": 3.8
        }
    ]


@pytest.fixture(scope="function")
def sample_reviews():
    """Sample review data for testing."""
    return [
        {
            "RecipeId": 1,
            "Rating": 5,
            "Review": "Amazing biryani recipe! The flavors were incredible and my family loved it.",
            "AuthorName": "FoodLover123",
            "DateSubmitted": "2024-01-15T10:30:00Z",
            "ReviewLength": 75
        },
        {
            "RecipeId": 1,
            "Rating": 4,
            "Review": "Good recipe but took longer than expected.",
            "AuthorName": "QuickCook",
            "DateSubmitted": "2024-01-20T14:45:00Z",
            "ReviewLength": 45
        },
        {
            "RecipeId": 2,
            "Rating": 3,
            "Review": "Decent fondue but a bit too salty for my taste.",
            "AuthorName": "HealthyEater",
            "DateSubmitted": "2024-02-20T18:15:00Z",
            "ReviewLength": 48
        },
        {
            "RecipeId": 3,
            "Rating": 5,
            "Review": "Perfect cookies! Crispy outside, soft inside. Will make again!",
            "AuthorName": "BakingMom",
            "DateSubmitted": "2024-03-15T09:20:00Z",
            "ReviewLength": 62
        }
    ]


@pytest.fixture(scope="function")
def populated_db(mock_db, sample_recipes, sample_reviews):
    """Database populated with test data."""
    # Insert test recipes
    recipes_collection = mock_db["recipes_test"]
    recipes_collection.insert_many(sample_recipes)
    
    # Insert test reviews
    reviews_collection = mock_db["reviews_test"]
    reviews_collection.insert_many(sample_reviews)
    
    return mock_db


@pytest.fixture
def mock_stripe():
    """Mock Stripe for payment testing."""
    with patch('stripe.checkout.Session.create') as mock_create:
        mock_create.return_value = Mock(id="cs_test_123")
        yield mock_create


@pytest.fixture
def mock_calculate_calories():
    """Mock calorie calculation for testing."""
    with patch('app.calculate_recipe_calories') as mock_calc:
        mock_calc.return_value = {
            "calories_per_serving": 112.5,
            "total_calories": 450,
            "ingredient_breakdown": [
                {"ingredient": "rice", "calories": 200},
                {"ingredient": "chicken", "calories": 250}
            ]
        }
        yield mock_calc


@pytest.fixture(scope="function")
def test_session_id():
    """Generate a test session ID."""
    return "test-session-12345"


@pytest.fixture(scope="function")
def sample_search_queries():
    """Sample search queries for testing."""
    return {
        "valid_queries": [
            "chicken biryani",
            "pizza",
            "chocolate cookies",
            "indian curry",
            "pasta marinara"
        ],
        "typo_queries": [
            "mali",
            "chiken",
            "spagetti",
            "biriyani",
            "tomatos"
        ],
        "empty_queries": [
            "",
            "   ",
            None
        ]
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def capture_logs(caplog):
    """Capture application logs for testing."""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


# Helper fixtures for specific test scenarios
@pytest.fixture
def recipe_with_no_servings():
    """Recipe data with missing serving information."""
    return {
        "RecipeId": 999,
        "Name": "Test Recipe No Servings",
        "RecipeServings": None,
        "RecipeYield": None,
        "Calories": 300
    }


@pytest.fixture
def recipe_with_string_servings():
    """Recipe data with string serving information."""
    return {
        "RecipeId": 998,
        "Name": "Test Recipe String Servings",
        "RecipeServings": "6",
        "RecipeYield": "serves 6",
        "Calories": 600
    }


@pytest.fixture
def mock_trending_cache(mock_db):
    """Mock trending cache data."""
    cache_data = {
        "_id": "current",
        "trending": [
            {"query": "biryani", "count": 150, "score": 75.5, "trend": "up"},
            {"query": "pizza", "count": 120, "score": 60.0, "trend": "stable"},
            {"query": "cookies", "count": 90, "score": 45.0, "trend": "up"}
        ],
        "updated_at": datetime.utcnow() - timedelta(minutes=5)
    }
    
    trending_collection = mock_db["trending_cache"]
    trending_collection.insert_one(cache_data)
    return cache_data 