#!/usr/bin/env python3

"""
Nutritional Database for Calorie Calculation
Maps common ingredients to calories per standard unit
"""

import json
import re

# Nutritional data: ingredient_name -> calories per common unit
NUTRITIONAL_DATABASE = {
    # Vegetables (per cup unless specified)
    "cabbage": 22,
    "onion": 64,
    "carrot": 52,
    "carrots": 52,
    "celery": 16,
    "tomato": 32,
    "potato": 116,
    "potatoes": 116,
    "broccoli": 25,
    "spinach": 7,
    "lettuce": 5,
    "bell pepper": 30,
    "mushroom": 15,
    "mushrooms": 15,
    "garlic": 4,  # per clove
    "ginger": 1,  # per teaspoon
    # Proteins (per 100g unless specified)
    "chicken breast": 165,
    "chicken": 165,
    "beef": 250,
    "ground beef": 250,
    "pork": 242,
    "salmon": 208,
    "tuna": 132,
    "eggs": 155,  # per 100g
    "egg": 70,  # per large egg
    "beans": 127,  # per cup cooked
    "black beans": 227,  # per cup
    "kidney beans": 225,  # per cup
    "chickpeas": 269,  # per cup
    # Grains & Starches (per cup cooked)
    "rice": 205,
    "white rice": 205,
    "brown rice": 216,
    "pasta": 220,
    "bread": 80,  # per slice
    "flour": 455,  # per cup
    "oats": 154,
    "quinoa": 222,
    # Dairy (per cup unless specified)
    "milk": 149,
    "cheese": 113,  # per oz
    "butter": 102,  # per tablespoon
    "yogurt": 154,
    "cream": 821,  # heavy cream per cup
    "sour cream": 493,
    # Oils & Fats (per tablespoon)
    "olive oil": 119,
    "vegetable oil": 120,
    "oil": 120,
    "coconut oil": 117,
    # Liquids (per cup)
    "water": 0,
    "broth": 15,
    "chicken broth": 15,
    "vegetable broth": 12,
    "tomato juice": 41,
    "wine": 125,
    # Common seasonings (per teaspoon)
    "salt": 0,
    "pepper": 6,
    "sugar": 16,
    "honey": 21,  # per tablespoon
    "vanilla": 12,  # per teaspoon
    # Nuts & Seeds (per oz)
    "almonds": 164,
    "walnuts": 185,
    "peanuts": 161,
    "sunflower seeds": 165,
    # Fruits (per medium fruit or cup)
    "apple": 95,
    "banana": 105,
    "orange": 65,
    "lemon": 17,
    "berries": 84,  # per cup
    "strawberries": 49,  # per cup
}

# Unit conversion factors to standardize measurements
UNIT_CONVERSIONS = {
    # Volume conversions to cups
    "cup": 1.0,
    "cups": 1.0,
    "tablespoon": 1 / 16,
    "tablespoons": 1 / 16,
    "tbsp": 1 / 16,
    "teaspoon": 1 / 48,
    "teaspoons": 1 / 48,
    "tsp": 1 / 48,
    "pint": 2.0,
    "quart": 4.0,
    "liter": 4.227,
    "ml": 1 / 236.6,
    "fluid ounce": 1 / 8,
    "fl oz": 1 / 8,
    # Weight conversions (approximations to cups)
    "pound": 2.0,  # very rough approximation
    "lb": 2.0,
    "ounce": 1 / 8,
    "oz": 1 / 8,
    "gram": 1 / 240,  # very rough
    "kg": 4.2,
    # Count conversions
    "piece": 1.0,
    "pieces": 1.0,
    "slice": 1.0,
    "slices": 1.0,
    "clove": 1.0,
    "cloves": 1.0,
}


def normalize_ingredient_name(ingredient):
    """Clean and normalize ingredient names for database lookup."""
    if not ingredient:
        return ""

    # Convert to lowercase and remove extra spaces
    ingredient = ingredient.lower().strip()

    # Remove common prefixes/suffixes
    remove_words = [
        "fresh",
        "dried",
        "chopped",
        "diced",
        "sliced",
        "minced",
        "cooked",
        "raw",
        "frozen",
        "canned",
        "organic",
        "large",
        "small",
        "medium",
        "whole",
        "ground",
        "shredded",
        "grated",
    ]

    words = ingredient.split()
    filtered_words = [word for word in words if word not in remove_words]

    return " ".join(filtered_words)


def extract_quantity_and_unit(quantity_str):
    """Extract numeric quantity and unit from quantity string."""
    if not quantity_str:
        return 1.0, "piece"

    # Convert to string if not already
    quantity_str = str(quantity_str).lower().strip()

    # Pattern to match number and unit
    # Examples: "2 cups", "1.5 tbsp", "46", "1/2 tsp"
    pattern = r"([0-9]*\.?[0-9]+(?:/[0-9]+)?)\s*([a-zA-Z]*)"
    match = re.match(pattern, quantity_str)

    if match:
        quantity_part = match.group(1)
        unit_part = match.group(2) or "piece"

        # Handle fractions
        if "/" in quantity_part:
            parts = quantity_part.split("/")
            quantity = float(parts[0]) / float(parts[1])
        else:
            quantity = float(quantity_part)

        return quantity, unit_part

    # If no pattern matches, try to extract just the number
    try:
        return float(quantity_str), "piece"
    except:
        return 1.0, "piece"


def calculate_ingredient_calories(ingredient_name, quantity_str):
    """Calculate calories for a single ingredient."""
    # Normalize the ingredient name
    normalized_name = normalize_ingredient_name(ingredient_name)

    # Extract quantity and unit
    quantity, unit = extract_quantity_and_unit(quantity_str)

    # Find matching ingredient in database
    calories_per_unit = None
    for db_ingredient, calories in NUTRITIONAL_DATABASE.items():
        if db_ingredient in normalized_name or normalized_name in db_ingredient:
            calories_per_unit = calories
            break

    if calories_per_unit is None:
        # If no match found, use a default calorie estimate
        return estimate_unknown_ingredient_calories(normalized_name, quantity, unit)

    # Convert units to standard unit (usually cups)
    unit_multiplier = UNIT_CONVERSIONS.get(unit, 1.0)
    standard_quantity = quantity * unit_multiplier

    # Calculate total calories
    total_calories = calories_per_unit * standard_quantity

    return max(0, total_calories)  # Ensure non-negative


def estimate_unknown_ingredient_calories(ingredient_name, quantity, unit):
    """Provide rough calorie estimates for unknown ingredients."""
    # Very basic categorization by common ingredient types
    if any(word in ingredient_name for word in ["oil", "fat", "butter"]):
        return quantity * 120  # High calorie estimate for fats
    elif any(word in ingredient_name for word in ["vegetable", "fruit", "herb", "spice"]):
        return quantity * 25  # Low calorie estimate for produce
    elif any(word in ingredient_name for word in ["meat", "protein", "fish"]):
        return quantity * 200  # Medium-high for proteins
    elif any(word in ingredient_name for word in ["grain", "flour", "rice", "pasta"]):
        return quantity * 150  # Medium for carbs
    else:
        return quantity * 50  # Conservative default


def calculate_recipe_calories(ingredients_list, quantities_list, servings=1):
    """Calculate total calories for a recipe."""
    if not ingredients_list or not quantities_list:
        return None

    # Handle string inputs (JSON)
    if isinstance(ingredients_list, str):
        try:
            ingredients_list = json.loads(ingredients_list)
        except:
            return None

    if isinstance(quantities_list, str):
        try:
            quantities_list = json.loads(quantities_list)
        except:
            return None

    total_calories = 0
    calculation_details = []

    # Ensure both lists have the same length
    min_length = min(len(ingredients_list), len(quantities_list))

    for i in range(min_length):
        ingredient = ingredients_list[i]
        quantity = quantities_list[i]

        ingredient_calories = calculate_ingredient_calories(ingredient, quantity)
        total_calories += ingredient_calories

        calculation_details.append({"ingredient": ingredient, "quantity": quantity, "calories": ingredient_calories})

    # Calculate per serving
    servings = max(1, servings or 1)  # Ensure at least 1 serving
    calories_per_serving = total_calories / servings

    return {
        "total_calories": round(total_calories, 1),
        "calories_per_serving": round(calories_per_serving, 1),
        "servings": servings,
        "calculation_details": calculation_details,
    }


# Test function
if __name__ == "__main__":
    # Test with sample data
    test_ingredients = ["plain tomato juice", "cabbage", "onion", "carrots", "celery"]
    test_quantities = ["46", "4", "1", "2", "1"]

    result = calculate_recipe_calories(test_ingredients, test_quantities, servings=4)
    print(f"Test calculation: {result}")
