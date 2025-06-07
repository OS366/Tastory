"""
API endpoint tests for Tastory application.
"""

import json
from unittest.mock import Mock, patch

import pytest


class TestChatEndpoint:
    """Test /chat endpoint functionality."""

    @pytest.mark.api
    def test_chat_successful_search(self, test_app, populated_db):
        """Test successful recipe search via chat endpoint."""
        payload = {"message": "chicken biryani", "page": 1}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "recipes" in data
        assert len(data["recipes"]) > 0
        assert data["currentPage"] == 1
        assert "totalPages" in data
        assert "totalResults" in data

        # Check recipe structure
        recipe = data["recipes"][0]
        expected_fields = ["id", "name", "calories", "walkMeter", "rating", "reviews"]
        for field in expected_fields:
            assert field in recipe

    @pytest.mark.api
    def test_chat_spell_correction(self, test_app, populated_db):
        """Test spell correction in chat endpoint."""
        payload = {"message": "chiken", "page": 1}  # Typo for chicken

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "spellCorrection" in data
        assert data["spellCorrection"]["originalQuery"] == "chiken"
        assert data["spellCorrection"]["correctedQuery"] == "chicken"
        assert data["spellCorrection"]["wasUsed"] is True

    @pytest.mark.api
    def test_chat_empty_message(self, test_app):
        """Test chat endpoint with empty message."""
        payload = {"message": "", "page": 1}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @pytest.mark.api
    def test_chat_missing_message(self, test_app):
        """Test chat endpoint with missing message field."""
        payload = {"page": 1}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 400

    @pytest.mark.api
    def test_chat_pagination(self, test_app, populated_db):
        """Test pagination in chat endpoint."""
        payload = {"message": "recipe", "page": 2}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["currentPage"] == 2

    @pytest.mark.api
    def test_chat_options_request(self, test_app):
        """Test OPTIONS request for CORS."""
        response = test_app.open("/chat", method="OPTIONS")
        assert response.status_code == 200


class TestSuggestEndpoint:
    """Test /suggest endpoint functionality."""

    @pytest.mark.api
    def test_suggest_valid_query(self, test_app, populated_db):
        """Test suggest endpoint with valid query."""
        response = test_app.get("/suggest?query=chick")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert isinstance(data, list)
        # Should return suggestions containing "chicken"
        suggestions = [s.lower() for s in data]
        assert any("chicken" in s for s in suggestions)

    @pytest.mark.api
    def test_suggest_empty_query(self, test_app):
        """Test suggest endpoint with empty query."""
        response = test_app.get("/suggest?query=")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    @pytest.mark.api
    def test_suggest_short_query(self, test_app):
        """Test suggest endpoint with very short query."""
        response = test_app.get("/suggest?query=a")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []  # Should return empty for queries < 2 chars

    @pytest.mark.api
    def test_suggest_no_query_param(self, test_app):
        """Test suggest endpoint without query parameter."""
        response = test_app.get("/suggest")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []


class TestTrendingEndpoint:
    """Test /trending endpoint functionality."""

    @pytest.mark.api
    def test_trending_success(self, test_app, mock_trending_cache):
        """Test successful trending endpoint response."""
        response = test_app.get("/trending")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "trending" in data
        assert "lastUpdated" in data
        assert isinstance(data["trending"], list)

        if data["trending"]:
            trend_item = data["trending"][0]
            expected_fields = ["query", "count", "score", "trend"]
            for field in expected_fields:
                assert field in trend_item

    @pytest.mark.api
    @patch("app.db", None)
    def test_trending_no_database(self, test_app):
        """Test trending endpoint when database is unavailable."""
        response = test_app.get("/trending")

        # Should still return 200 with empty trending data
        assert response.status_code == 200 or response.status_code == 500


class TestCuisineSearchEndpoint:
    """Test /search/cuisine endpoint functionality."""

    @pytest.mark.api
    def test_cuisine_search_indian(self, test_app, populated_db):
        """Test cuisine search for Indian food."""
        payload = {"query": "indian biryani", "page": 1}

        response = test_app.post("/search/cuisine", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["cuisine"] == "indian"
        assert "recipes" in data

    @pytest.mark.api
    def test_cuisine_search_no_cuisine_detected(self, test_app, populated_db):
        """Test cuisine search when no cuisine is detected."""
        payload = {"query": "xyz123 abcdef", "page": 1}  # Nonsense query that won't match any cuisine

        response = test_app.post("/search/cuisine", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @pytest.mark.api
    def test_cuisine_search_empty_query(self, test_app):
        """Test cuisine search with empty query."""
        payload = {"query": "", "page": 1}

        response = test_app.post("/search/cuisine", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 400


class TestCalorieDetailsEndpoint:
    """Test /recipe/<recipe_id>/calories endpoint."""

    @pytest.mark.api
    def test_calorie_details_valid_recipe(self, test_app, populated_db):
        """Test calorie details for valid recipe."""
        response = test_app.get("/recipe/1/calories")

        assert response.status_code == 200
        data = json.loads(response.data)

        expected_fields = ["recipe", "existingCalories", "calculatedCalories"]
        for field in expected_fields:
            assert field in data

        assert data["recipe"]["id"] == "1"
        assert "name" in data["recipe"]
        assert "servings" in data["recipe"]

    @pytest.mark.api
    def test_calorie_details_invalid_recipe(self, test_app, populated_db):
        """Test calorie details for non-existent recipe."""
        response = test_app.get("/recipe/99999/calories")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    @pytest.mark.api
    def test_calorie_details_invalid_id_format(self, test_app, populated_db):
        """Test calorie details with invalid ID format."""
        response = test_app.get("/recipe/invalid/calories")

        assert response.status_code == 404


class TestStripeEndpoints:
    """Test Stripe payment endpoints."""

    @pytest.mark.api
    def test_create_checkout_session(self, test_app, mock_stripe):
        """Test checkout session creation."""
        response = test_app.post("/create-checkout-session", data=json.dumps({}), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "id" in data
        mock_stripe.assert_called_once()

    @pytest.mark.api
    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session_error(self, mock_create, test_app):
        """Test checkout session creation with Stripe error."""
        mock_create.side_effect = Exception("Stripe error")

        response = test_app.post("/create-checkout-session", data=json.dumps({}), content_type="application/json")

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data

    @pytest.mark.api
    @patch("stripe.Webhook.construct_event")
    def test_webhook_valid_event(self, mock_construct, test_app):
        """Test webhook with valid event."""
        mock_event = Mock()
        mock_event.type = "checkout.session.completed"
        mock_event.data.object = {"customer": "cus_test", "subscription": "sub_test"}
        mock_construct.return_value = mock_event

        response = test_app.post("/webhook", data="test_payload", headers={"Stripe-Signature": "test_signature"})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    @pytest.mark.api
    @patch("stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_construct, test_app):
        """Test webhook with invalid signature."""
        import stripe

        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig_header")

        response = test_app.post("/webhook", data="test_payload", headers={"Stripe-Signature": "invalid_signature"})

        assert response.status_code == 400


class TestHomeEndpoint:
    """Test home endpoint."""

    @pytest.mark.api
    def test_home_endpoint(self, test_app):
        """Test home endpoint returns API information."""
        response = test_app.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)

        expected_fields = ["name", "tagline", "version", "endpoints"]
        for field in expected_fields:
            assert field in data

        assert data["name"] == "Tastory API"
        assert "endpoints" in data
        assert "/chat" in data["endpoints"]


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.api
    def test_invalid_json_payload(self, test_app):
        """Test endpoints with invalid JSON."""
        response = test_app.post("/chat", data="invalid json", content_type="application/json")

        assert response.status_code in [400, 500]

    @pytest.mark.api
    def test_missing_content_type(self, test_app):
        """Test endpoints without proper content type."""
        response = test_app.post("/chat", data='{"message": "test"}')

        # Should handle gracefully
        assert response.status_code in [200, 400, 415]

    @pytest.mark.api
    @patch("app.db", None)
    @patch("app.connect_to_mongodb")
    def test_database_unavailable(self, mock_connect, test_app):
        """Test endpoints when database is unavailable."""
        # Mock connection failure
        mock_connect.return_value = (None, None)

        payload = {"message": "test", "page": 1}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "reply" in data  # App returns "reply" field, not "error"
        assert "Could not connect to the database" in data["reply"]


class TestResponseFormat:
    """Test response format consistency."""

    @pytest.mark.api
    def test_chat_response_format(self, test_app, populated_db):
        """Test chat endpoint response format consistency."""
        payload = {"message": "test", "page": 1}

        response = test_app.post("/chat", data=json.dumps(payload), content_type="application/json")

        data = json.loads(response.data)

        # Check required fields in response
        if response.status_code == 200:
            assert "recipes" in data
            assert "currentPage" in data
            assert "totalPages" in data
            assert "success" in data

            # Check recipe format
            if data["recipes"]:
                recipe = data["recipes"][0]
                required_fields = [
                    "id",
                    "name",
                    "calories",
                    "walkMeter",
                    "rating",
                    "reviews",
                    "url",
                    "ingredients",
                    "instructions",
                ]
                for field in required_fields:
                    assert field in recipe

    @pytest.mark.api
    def test_suggest_response_format(self, test_app, populated_db):
        """Test suggest endpoint response format."""
        response = test_app.get("/suggest?query=test")

        data = json.loads(response.data)
        assert isinstance(data, list)

        # All items should be strings
        for item in data:
            assert isinstance(item, str)

    @pytest.mark.api
    def test_trending_response_format(self, test_app, mock_trending_cache):
        """Test trending endpoint response format."""
        response = test_app.get("/trending")

        if response.status_code == 200:
            data = json.loads(response.data)
            assert "trending" in data
            assert "lastUpdated" in data

            # Check trending item format
            if data["trending"]:
                item = data["trending"][0]
                required_fields = ["query", "count", "score"]
                for field in required_fields:
                    assert field in item
