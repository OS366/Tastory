"""
Smoke tests for critical functionality - these should always pass.
"""
import pytest
from app import spell_correct_query, calculate_walk_meter, estimate_serving_size


class TestSmokeTests:
    """Basic smoke tests to ensure core functionality works."""
    
    @pytest.mark.smoke
    def test_spell_correction_basic(self):
        """Test that spell correction works for common cases."""
        result = spell_correct_query("mali")
        assert result["corrected"] == "malai"
        assert result["has_corrections"] is True
    
    @pytest.mark.smoke
    def test_walk_meter_basic(self):
        """Test that walk meter calculation works."""
        result = calculate_walk_meter("100")
        assert "km" in result["distance"] or "m" in result["distance"]
        assert "message" in result
        assert "emoji" in result
    
    @pytest.mark.smoke
    def test_serving_size_estimation_basic(self):
        """Test that serving size estimation works."""
        result = estimate_serving_size("Pizza Fondue")
        assert isinstance(result, int)
        assert result > 0
        assert result == 6  # Pizza Fondue should be 6 servings
    
    @pytest.mark.smoke
    def test_app_imports_successfully(self):
        """Test that the app can be imported without errors."""
        from app import app
        assert app is not None
        assert app.name == "app"
    
    @pytest.mark.smoke
    def test_basic_functions_handle_edge_cases(self):
        """Test that functions handle basic edge cases gracefully."""
        # Test with None
        spell_result = spell_correct_query(None)
        assert spell_result["original"] == ""
        
        # Test with empty string
        spell_result = spell_correct_query("")
        assert spell_result["corrected"] == ""
        
        # Test walk meter with invalid input
        walk_result = calculate_walk_meter("invalid")
        assert walk_result["distance"] == "N/A"
        
        # Test serving size with None
        serving_result = estimate_serving_size(None)
        assert serving_result == 4 