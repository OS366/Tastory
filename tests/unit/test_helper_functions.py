"""
Unit tests for helper functions in Tastory application.
"""
import pytest
from unittest.mock import patch

from app import (
    spell_correct_query,
    calculate_walk_meter,
    estimate_serving_size,
    safe_get_servings,
    slugify,
    generate_star_rating
)


class TestSpellCorrection:
    """Test spell correction functionality."""
    
    @pytest.mark.unit
    def test_spell_correct_common_typos(self):
        """Test correction of common cooking term typos."""
        test_cases = [
            ("mali", "malai"),
            ("chiken", "chicken"),
            ("spagetti", "spaghetti"),
            ("biriyani", "biryani"),
            ("tumeric", "turmeric"),
            ("tomatos", "tomato"),
            ("vegitable", "vegetable")
        ]
        
        for typo, expected in test_cases:
            result = spell_correct_query(typo)
            assert result["corrected"] == expected
            assert result["has_corrections"] is True
            assert result["original"] == typo
    
    @pytest.mark.unit
    def test_spell_correct_no_corrections_needed(self):
        """Test words that don't need correction."""
        test_cases = ["chicken", "biryani", "pizza", "pasta", "curry"]
        
        for word in test_cases:
            result = spell_correct_query(word)
            assert result["corrected"] == word
            assert result["has_corrections"] is False
            assert result["original"] == word
    
    @pytest.mark.unit
    def test_spell_correct_multiple_words(self):
        """Test spell correction for multiple word queries."""
        result = spell_correct_query("chiken biriyani")
        assert result["corrected"] == "chicken biryani"
        assert result["has_corrections"] is True
    
    @pytest.mark.unit
    def test_spell_correct_mixed_case(self):
        """Test spell correction with mixed case."""
        result = spell_correct_query("Chiken Biriyani")
        assert result["corrected"] == "chicken biryani"
        assert result["has_corrections"] is True
    
    @pytest.mark.unit
    def test_spell_correct_empty_string(self):
        """Test spell correction with empty string."""
        result = spell_correct_query("")
        assert result["corrected"] == ""
        assert result["has_corrections"] is False


class TestWalkMeterCalculation:
    """Test walk meter calculation functionality."""
    
    @pytest.mark.unit
    def test_walk_meter_valid_calories(self):
        """Test walk meter calculation with valid calorie values."""
        test_cases = [
            ("85", {"distance": "1.0 km", "message": "A pleasant park stroll"}),
            ("170", {"distance": "2.0 km", "message": "A good workout walk"}),
            ("400", {"distance": "4.7 km", "message": "Time for a power walk!"}),
            ("600", {"distance": "7.1 km", "message": "That's a serious hike!"}),
            ("1200", {"distance": "14.1 km", "message": "Marathon training territory!"}),
            ("1700", {"distance": "20 km", "message": "That's an ultra-marathon!"})
        ]
        
        for calories, expected in test_cases:
            result = calculate_walk_meter(calories)
            assert expected["distance"] in result["distance"]
            assert expected["message"] in result["message"]
    
    @pytest.mark.unit
    def test_walk_meter_edge_cases(self):
        """Test walk meter calculation with edge cases."""
        # Test with "N/A" calories
        result = calculate_walk_meter("N/A")
        assert result["distance"] == "N/A"
        assert "Walk data not available" in result["message"]
        
        # Test with zero calories
        result = calculate_walk_meter("0")
        assert "0 km" in result["distance"]
        
        # Test with very small calories
        result = calculate_walk_meter("10")
        assert "118m" in result["distance"]
    
    @pytest.mark.unit
    def test_walk_meter_invalid_input(self):
        """Test walk meter calculation with invalid input."""
        invalid_inputs = [None, "", "invalid", "abc"]
        
        for invalid_input in invalid_inputs:
            result = calculate_walk_meter(invalid_input)
            assert result["distance"] == "N/A"
            assert "Walk data not available" in result["message"]


class TestServingSizeEstimation:
    """Test serving size estimation functionality."""
    
    @pytest.mark.unit
    def test_estimate_serving_size_fondue_dishes(self):
        """Test estimation for fondue and similar dishes."""
        test_cases = [
            "Pizza Fondue",
            "Cheese Fondue", 
            "Chocolate Fondue",
            "Beef Stew",
            "Chicken Soup",
            "Vegetable Casserole",
            "Spinach Dip"
        ]
        
        for recipe_name in test_cases:
            result = estimate_serving_size(recipe_name)
            assert result == 6
    
    @pytest.mark.unit
    def test_estimate_serving_size_baked_goods(self):
        """Test estimation for baked goods."""
        test_cases = [
            "Chocolate Cake",
            "Apple Pie",
            "Banana Bread",
            "Sourdough Loaf"
        ]
        
        for recipe_name in test_cases:
            result = estimate_serving_size(recipe_name)
            assert result == 8
    
    @pytest.mark.unit
    def test_estimate_serving_size_salads(self):
        """Test estimation for salads and side dishes."""
        test_cases = [
            "Caesar Salad",
            "Green Salad",
            "Potato Side",
            "Rice Side Dish"
        ]
        
        for recipe_name in test_cases:
            result = estimate_serving_size(recipe_name)
            assert result == 4
    
    @pytest.mark.unit
    def test_estimate_serving_size_default(self):
        """Test estimation for general recipes."""
        test_cases = [
            "Chicken Biryani",
            "Pasta Marinara",
            "Grilled Salmon",
            "Random Recipe Name"
        ]
        
        for recipe_name in test_cases:
            result = estimate_serving_size(recipe_name)
            assert result == 4
    
    @pytest.mark.unit
    def test_estimate_serving_size_edge_cases(self):
        """Test estimation with edge cases."""
        assert estimate_serving_size("") == 4
        assert estimate_serving_size(None) == 4


class TestSafeGetServings:
    """Test safe serving size extraction."""
    
    @pytest.mark.unit
    def test_safe_get_servings_valid_data(self, sample_recipes):
        """Test with valid serving data."""
        recipe = sample_recipes[0]  # Chicken Biryani with "4" servings
        result = safe_get_servings(recipe)
        assert result == 4
    
    @pytest.mark.unit
    def test_safe_get_servings_missing_data(self, sample_recipes):
        """Test with missing serving data."""
        recipe = sample_recipes[1]  # Pizza Fondue with None servings
        result = safe_get_servings(recipe)
        assert result == 6  # Should estimate based on recipe name
    
    @pytest.mark.unit
    def test_safe_get_servings_string_conversion(self):
        """Test string to int conversion."""
        recipe = {"RecipeServings": "8", "Name": "Test Recipe"}
        result = safe_get_servings(recipe)
        assert result == 8
    
    @pytest.mark.unit
    def test_safe_get_servings_invalid_string(self):
        """Test with invalid string values."""
        recipe = {"RecipeServings": "invalid", "Name": "Test Recipe"}
        result = safe_get_servings(recipe)
        assert result == 4  # Should fall back to default estimation
    
    @pytest.mark.unit
    def test_safe_get_servings_zero_servings(self):
        """Test with zero servings."""
        recipe = {"RecipeServings": "0", "Name": "Test Recipe"}
        result = safe_get_servings(recipe)
        assert result == 1  # Should return at least 1


class TestSlugify:
    """Test URL slug generation."""
    
    @pytest.mark.unit
    def test_slugify_normal_text(self):
        """Test slugification of normal text."""
        test_cases = [
            ("Chicken Biryani", "chickenbiryani"),
            ("Pizza Margherita", "pizzamargherita"),
            ("Chocolate Chip Cookies", "chocolatechipcookies")
        ]
        
        for text, expected in test_cases:
            result = slugify(text)
            assert result == expected
    
    @pytest.mark.unit
    def test_slugify_special_characters(self):
        """Test slugification with special characters."""
        test_cases = [
            ("Mom's Apple Pie!", "momsapplepie"),
            ("Café au Lait", "cafaulait"),
            ("Fish & Chips", "fishchips")
        ]
        
        for text, expected in test_cases:
            result = slugify(text)
            assert result == expected
    
    @pytest.mark.unit
    def test_slugify_edge_cases(self):
        """Test slugification edge cases."""
        assert slugify("") == ""
        assert slugify(None) == ""
        assert slugify("   ") == ""
        assert slugify("---") == ""


class TestStarRatingGeneration:
    """Test star rating HTML generation."""
    
    @pytest.mark.unit
    def test_generate_star_rating_valid_ratings(self):
        """Test star rating generation with valid ratings."""
        test_cases = [
            (5.0, 5, 0, 0),  # (rating, full_stars, half_stars, empty_stars)
            (4.5, 4, 1, 0),
            (3.7, 3, 1, 1),  # 3.7 has 3 full, 1 half, 1 empty
            (2.0, 2, 0, 3),
            (0.0, 0, 0, 5)
        ]
        
        for rating, expected_full, expected_half, expected_empty in test_cases:
            result = generate_star_rating(rating)
            assert result is not None
            assert "fa-star" in result  # Should contain star icons
            
            # Count star types in the result
            full_count = result.count('fas fa-star text-gold-500')
            half_count = result.count('fas fa-star-half-alt text-gold-500')
            empty_count = result.count('far fa-star text-gold-500/50')
            
            assert full_count == expected_full
            assert half_count == expected_half
            assert empty_count == expected_empty
    
    @pytest.mark.unit
    def test_generate_star_rating_invalid_input(self):
        """Test star rating generation with invalid input."""
        invalid_inputs = [None, "", "invalid", -1, 6]
        
        for invalid_input in invalid_inputs:
            result = generate_star_rating(invalid_input)
            if invalid_input in [None, "", "invalid"]:
                assert "No rating" in result
            else:
                # Should clamp to valid range
                assert "fa-star" in result or "No rating" in result


class TestErrorHandling:
    """Test error handling in helper functions."""
    
    @pytest.mark.unit
    def test_functions_handle_none_input(self):
        """Test that functions handle None input gracefully."""
        # These should not raise exceptions
        spell_result = spell_correct_query(None)
        assert spell_result is not None
        assert spell_result["original"] == ""
        assert spell_result["corrected"] == ""
        assert spell_result["has_corrections"] is False
        
        walk_result = calculate_walk_meter(None)
        assert walk_result is not None
        assert walk_result["distance"] == "N/A"
        
        assert estimate_serving_size(None) == 4
        assert slugify(None) == ""
    
    @pytest.mark.unit
    def test_functions_handle_empty_input(self):
        """Test that functions handle empty input gracefully."""
        # These should not raise exceptions
        assert spell_correct_query("") is not None
        assert calculate_walk_meter("") is not None
        assert estimate_serving_size("") == 4
        assert slugify("") == "" 