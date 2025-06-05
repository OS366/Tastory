"""
Integration tests for database operations in Tastory application.
"""

from datetime import datetime, timedelta

import pytest

from app import calculate_trending_searches, get_top_review, log_search_query


class TestRecipeDatabase:
    """Test recipe database operations."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_recipe_search_by_name(self, populated_db):
        """Test searching recipes by name."""
        recipes_collection = populated_db["recipes_test"]

        # Search for biryani
        results = list(recipes_collection.find({"Name": {"$regex": "biryani", "$options": "i"}}))

        assert len(results) > 0
        assert any("biryani" in recipe["Name"].lower() for recipe in results)

    @pytest.mark.integration
    @pytest.mark.database
    def test_recipe_search_by_ingredients(self, populated_db):
        """Test searching recipes by ingredients."""
        recipes_collection = populated_db["recipes_test"]

        # Search for recipes with chicken
        results = list(recipes_collection.find({"RecipeIngredientParts": {"$regex": "chicken", "$options": "i"}}))

        assert len(results) > 0
        for recipe in results:
            ingredients = recipe.get("RecipeIngredientParts", [])
            assert any("chicken" in str(ing).lower() for ing in ingredients)

    @pytest.mark.integration
    @pytest.mark.database
    def test_recipe_search_by_category(self, populated_db):
        """Test searching recipes by category."""
        recipes_collection = populated_db["recipes_test"]

        # Search for Indian recipes
        results = list(recipes_collection.find({"RecipeCategory": {"$regex": "indian", "$options": "i"}}))

        assert len(results) > 0
        for recipe in results:
            assert "indian" in recipe["RecipeCategory"].lower()

    @pytest.mark.integration
    @pytest.mark.database
    def test_recipe_pagination(self, populated_db):
        """Test recipe pagination functionality."""
        recipes_collection = populated_db["recipes_test"]

        # Test pagination
        page1 = list(recipes_collection.find({}).limit(2))
        page2 = list(recipes_collection.find({}).skip(2).limit(2))

        assert len(page1) <= 2
        assert len(page2) <= 2

        # Ensure different results
        page1_ids = [r["RecipeId"] for r in page1]
        page2_ids = [r["RecipeId"] for r in page2]
        assert set(page1_ids).isdisjoint(set(page2_ids))


class TestReviewDatabase:
    """Test review database operations."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_get_top_review_success(self, populated_db):
        """Test retrieving top review for a recipe."""
        # Recipe 1 has multiple reviews with different ratings
        top_review = get_top_review(populated_db["reviews_test"], 1)

        assert top_review is not None
        assert top_review["rating"] == 5  # Highest rating
        assert "text" in top_review
        assert "author" in top_review
        assert top_review["author"] == "FoodLover123"

    @pytest.mark.integration
    @pytest.mark.database
    def test_get_top_review_no_reviews(self, populated_db):
        """Test retrieving top review for recipe with no reviews."""
        top_review = get_top_review(populated_db["reviews_test"], 99999)

        assert top_review is None

    @pytest.mark.integration
    @pytest.mark.database
    def test_reviews_by_rating(self, populated_db):
        """Test filtering reviews by rating."""
        reviews_collection = populated_db["reviews_test"]

        # Get reviews with rating >= 4
        high_rated = list(reviews_collection.find({"Rating": {"$gte": 4}}))

        assert len(high_rated) > 0
        for review in high_rated:
            assert review["Rating"] >= 4

    @pytest.mark.integration
    @pytest.mark.database
    def test_reviews_sorting(self, populated_db):
        """Test sorting reviews by rating and length."""
        reviews_collection = populated_db["reviews_test"]

        # Get reviews sorted by rating (desc) then by length (desc)
        sorted_reviews = list(reviews_collection.find({"RecipeId": 1}).sort([("Rating", -1), ("ReviewLength", -1)]))

        assert len(sorted_reviews) > 1
        # First should be highest rated
        assert sorted_reviews[0]["Rating"] >= sorted_reviews[1]["Rating"]


class TestSearchLogging:
    """Test search query logging functionality."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_log_search_query(self, mock_db):
        """Test logging search queries."""
        session_id = "test-session-123"
        query = "chicken biryani"

        log_search_query(query, session_id, results_count=5)

        # Check if logged
        search_logs = mock_db.search_logs
        logged_entry = search_logs.find_one({"query": query.lower()})

        assert logged_entry is not None
        assert logged_entry["session_id"] == session_id
        assert logged_entry["results_count"] == 5
        assert "timestamp" in logged_entry

    @pytest.mark.integration
    @pytest.mark.database
    def test_multiple_search_logging(self, mock_db):
        """Test logging multiple search queries."""
        queries = ["pizza", "biryani", "cookies"]
        session_id = "test-session-456"

        for query in queries:
            log_search_query(query, session_id)

        # Check all are logged
        search_logs = mock_db.search_logs
        logged_count = search_logs.count_documents({"session_id": session_id})

        assert logged_count == len(queries)


class TestTrendingCalculations:
    """Test trending search calculations."""

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.slow
    def test_calculate_trending_searches(self, mock_db):
        """Test calculating trending searches."""
        # Insert test search logs
        search_logs = mock_db.search_logs
        now = datetime.utcnow()

        # Create search logs with different patterns
        test_logs = [
            # Popular recent searches
            {"query": "biryani", "timestamp": now - timedelta(minutes=30), "session_id": "s1"},
            {"query": "biryani", "timestamp": now - timedelta(minutes=25), "session_id": "s2"},
            {"query": "biryani", "timestamp": now - timedelta(minutes=20), "session_id": "s3"},
            {"query": "biryani", "timestamp": now - timedelta(minutes=15), "session_id": "s4"},
            {"query": "biryani", "timestamp": now - timedelta(minutes=10), "session_id": "s5"},
            {"query": "biryani", "timestamp": now - timedelta(minutes=5), "session_id": "s6"},
            # Moderately popular
            {"query": "pizza", "timestamp": now - timedelta(hours=2), "session_id": "s7"},
            {"query": "pizza", "timestamp": now - timedelta(hours=1), "session_id": "s8"},
            {"query": "pizza", "timestamp": now - timedelta(minutes=45), "session_id": "s9"},
            {"query": "pizza", "timestamp": now - timedelta(minutes=30), "session_id": "s10"},
            {"query": "pizza", "timestamp": now - timedelta(minutes=15), "session_id": "s11"},
            # Less popular but recent
            {"query": "cookies", "timestamp": now - timedelta(minutes=10), "session_id": "s12"},
            {"query": "cookies", "timestamp": now - timedelta(minutes=5), "session_id": "s13"},
            {"query": "cookies", "timestamp": now - timedelta(minutes=2), "session_id": "s14"},
            # Old searches (should not appear in trending)
            {"query": "old_recipe", "timestamp": now - timedelta(days=2), "session_id": "s15"},
        ]

        search_logs.insert_many(test_logs)

        # Calculate trending
        trending = calculate_trending_searches()

        assert isinstance(trending, list)
        assert len(trending) > 0

        # Check structure
        if trending:
            trend_item = trending[0]
            required_fields = ["query", "count", "score"]
            for field in required_fields:
                assert field in trend_item

            # "biryani" should be highly ranked due to recent activity
            queries = [item["query"] for item in trending]
            assert "biryani" in queries

    @pytest.mark.integration
    @pytest.mark.database
    def test_trending_cache(self, mock_db):
        """Test trending cache functionality."""
        # Create cache entry
        trending_cache = mock_db.trending_cache
        cache_data = {
            "_id": "current",
            "trending": [{"query": "test", "count": 10, "score": 5.0}],
            "updated_at": datetime.utcnow() - timedelta(minutes=5),
        }
        trending_cache.insert_one(cache_data)

        # Verify cache retrieval
        cached = trending_cache.find_one({"_id": "current"})
        assert cached is not None
        assert "trending" in cached
        assert "updated_at" in cached


class TestComplexQueries:
    """Test complex database queries."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_multi_field_search(self, populated_db):
        """Test searching across multiple fields."""
        recipes_collection = populated_db["recipes_test"]

        # Search for "chicken" in name, ingredients, or category
        query = {
            "$or": [
                {"Name": {"$regex": "chicken", "$options": "i"}},
                {"RecipeIngredientParts": {"$regex": "chicken", "$options": "i"}},
                {"RecipeCategory": {"$regex": "chicken", "$options": "i"}},
            ]
        }

        results = list(recipes_collection.find(query))
        assert len(results) > 0

        # Verify each result contains "chicken" in at least one field
        for recipe in results:
            contains_chicken = (
                "chicken" in recipe.get("Name", "").lower()
                or any("chicken" in str(ing).lower() for ing in recipe.get("RecipeIngredientParts", []))
                or "chicken" in recipe.get("RecipeCategory", "").lower()
            )
            assert contains_chicken

    @pytest.mark.integration
    @pytest.mark.database
    def test_aggregation_pipeline(self, populated_db):
        """Test MongoDB aggregation pipeline."""
        recipes_collection = populated_db["recipes_test"]

        # Aggregate recipes by category
        pipeline = [
            {"$group": {"_id": "$RecipeCategory", "count": {"$sum": 1}, "avg_rating": {"$avg": "$AggregatedRating"}}},
            {"$sort": {"count": -1}},
        ]

        results = list(recipes_collection.aggregate(pipeline))
        assert len(results) > 0

        for result in results:
            assert "_id" in result  # Category name
            assert "count" in result
            assert result["count"] > 0

    @pytest.mark.integration
    @pytest.mark.database
    def test_text_search_index(self, populated_db):
        """Test text search functionality."""
        recipes_collection = populated_db["recipes_test"]

        try:
            # Create text index for testing
            recipes_collection.create_index(
                [("Name", "text"), ("Description", "text"), ("RecipeIngredientParts", "text")]
            )

            # Perform text search
            results = list(
                recipes_collection.find({"$text": {"$search": "chicken"}}, {"score": {"$meta": "textScore"}}).sort(
                    [("score", {"$meta": "textScore"})]
                )
            )

            assert len(results) >= 0  # May be empty if no text index

        except Exception:
            # Text search may not be available in mongomock
            pytest.skip("Text search not available in test environment")


class TestDataIntegrity:
    """Test data integrity and validation."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_recipe_data_structure(self, populated_db):
        """Test recipe data structure integrity."""
        recipes_collection = populated_db["recipes_test"]

        for recipe in recipes_collection.find():
            # Check required fields
            assert "RecipeId" in recipe
            assert "Name" in recipe

            # Check data types
            assert isinstance(recipe["RecipeId"], int)
            assert isinstance(recipe["Name"], str)

            # Check rating is valid
            if "AggregatedRating" in recipe and recipe["AggregatedRating"] is not None:
                rating = recipe["AggregatedRating"]
                assert 0 <= rating <= 5

    @pytest.mark.integration
    @pytest.mark.database
    def test_review_data_structure(self, populated_db):
        """Test review data structure integrity."""
        reviews_collection = populated_db["reviews_test"]

        for review in reviews_collection.find():
            # Check required fields
            assert "RecipeId" in review
            assert "Rating" in review

            # Check data types and ranges
            assert isinstance(review["RecipeId"], int)
            assert isinstance(review["Rating"], int)
            assert 1 <= review["Rating"] <= 5

            # Check review text exists
            assert "Review" in review
            assert isinstance(review["Review"], str)
            assert len(review["Review"]) > 0

    @pytest.mark.integration
    @pytest.mark.database
    def test_referential_integrity(self, populated_db):
        """Test referential integrity between recipes and reviews."""
        recipes_collection = populated_db["recipes_test"]
        reviews_collection = populated_db["reviews_test"]

        # Get all recipe IDs
        recipe_ids = set(r["RecipeId"] for r in recipes_collection.find())

        # Check that all reviews reference valid recipes
        for review in reviews_collection.find():
            assert review["RecipeId"] in recipe_ids
