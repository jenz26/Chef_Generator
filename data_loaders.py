"""
Data loading and validation for Chef Planner
Handles JSON file loading with graceful error handling and validation.
"""

import json
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

def load_json_file(file_path: str) -> Optional[Any]:
    """Load a JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error loading {file_path}: {e}")
        return None

def validate_customer_types(data: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate customer types data structure"""
    warnings = []

    if not isinstance(data, list):
        return False, ["Customer types data must be an array"]

    if not data:
        return False, ["Customer types array is empty"]

    required_fields = ['name']
    optional_fields = ['favourite_tags', 'secondary_favourite_tags', 'tag_score_weight',
                      'price_score_weight', 'evaluation_score_weight', 'expectations']

    for i, customer in enumerate(data):
        if not isinstance(customer, dict):
            return False, [f"Customer {i} is not an object"]

        # Check required fields
        for field in required_fields:
            if field not in customer:
                return False, [f"Customer {i} missing required field: {field}"]

        # Check optional fields and add warnings
        if 'favourite_tags' not in customer:
            warnings.append(f"Customer '{customer['name']}': missing favourite_tags")

        if 'sections' not in customer:
            warnings.append(f"Customer '{customer['name']}': missing sections data")
        elif isinstance(customer['sections'], dict):
            # Check sections structure
            for section_name, section_data in customer['sections'].items():
                if not isinstance(section_data, dict):
                    warnings.append(f"Customer '{customer['name']}': section '{section_name}' is not an object")
                elif 'cost_expectation' not in section_data:
                    warnings.append(f"Customer '{customer['name']}': section '{section_name}' missing cost_expectation")

    return True, warnings

def validate_ingredients_data(data: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate ingredients data structure"""
    warnings = []

    if not isinstance(data, list):
        return False, ["Ingredients data must be an array"]

    if not data:
        return False, ["Ingredients array is empty"]

    for i, ingredient in enumerate(data):
        if not isinstance(ingredient, dict):
            return False, [f"Ingredient {i} is not an object"]

        # Check name field
        name_fields = ['name', 'Name']
        has_name = any(field in ingredient for field in name_fields)
        if not has_name:
            return False, [f"Ingredient {i} missing name field"]

        ingredient_name = ingredient.get('name', ingredient.get('Name', f'Ingredient {i}'))

        # Check optional but important fields
        if 'tags' not in ingredient and 'Tags' not in ingredient:
            warnings.append(f"Ingredient '{ingredient_name}': missing tags")

        if 'flavor_values' not in ingredient and 'FlavorValues' not in ingredient:
            warnings.append(f"Ingredient '{ingredient_name}': missing flavor values")

        if 'quality_costs' not in ingredient and 'Qualities' not in ingredient:
            warnings.append(f"Ingredient '{ingredient_name}': missing quality costs")

    return True, warnings

def validate_matches_data(data: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate matches data structure"""
    warnings = []

    if not isinstance(data, list):
        return False, ["Matches data must be an array"]

    if not data:
        warnings.append("Matches array is empty")
        return True, warnings

    required_fields = ['IngredientA', 'IngredientB', 'MatchValue']
    alt_fields = {'IngredientA': ['A'], 'IngredientB': ['B'], 'MatchValue': ['MatchValue']}

    for i, match in enumerate(data[:100]):  # Check only first 100 for performance
        if not isinstance(match, dict):
            return False, [f"Match {i} is not an object"]

        # Check required fields (with alternatives)
        for field in required_fields:
            if field not in match and not any(alt in match for alt in alt_fields.get(field, [])):
                return False, [f"Match {i} missing field: {field}"]

        # Check match value range
        match_value = match.get('MatchValue', match.get('MatchValue', 0))
        if match_value not in [1, 2, 3]:
            warnings.append(f"Match {i}: MatchValue should be 1, 2, or 3 (found {match_value})")

    return True, warnings

def normalize_ingredients_data(raw_data: List[Dict]) -> List[Dict]:
    """Normalize ingredient data to consistent format"""
    normalized = []

    for ingredient in raw_data:
        normalized_ingredient = {}

        # Normalize name
        normalized_ingredient['name'] = ingredient.get('name', ingredient.get('Name', 'Unknown'))

        # Normalize tags
        tags = ingredient.get('tags', ingredient.get('Tags', []))
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        normalized_ingredient['tags'] = tags

        # Normalize flavor values
        flavor_values = ingredient.get('flavor_values', ingredient.get('FlavorValues', {}))
        if isinstance(flavor_values, dict):
            # Ensure all flavor keys exist
            default_flavors = {'SOUR': 0, 'SALT': 0, 'ACID': 0, 'SWEET': 0, 'FAT': 0, 'UMAMI': 0}
            default_flavors.update(flavor_values)
            normalized_ingredient['flavor_values'] = default_flavors
        else:
            normalized_ingredient['flavor_values'] = {'SOUR': 0, 'SALT': 0, 'ACID': 0, 'SWEET': 0, 'FAT': 0, 'UMAMI': 0}

        # Normalize portions
        portions = ingredient.get('portions', ingredient.get('Portions', {}))
        if isinstance(portions, dict):
            default_portions = {'SMALL': 1, 'MEDIUM': 5, 'LARGE': 10}
            default_portions.update(portions)
            normalized_ingredient['portions'] = default_portions
        else:
            normalized_ingredient['portions'] = {'SMALL': 1, 'MEDIUM': 5, 'LARGE': 10}

        # Normalize quality costs
        qualities = ingredient.get('quality_costs', ingredient.get('Qualities', {}))
        if isinstance(qualities, dict):
            default_qualities = {
                'NORMAL': {'unit_cost': 1.0, 'points_cost': 1},
                'FIRST_CHOICE': {'unit_cost': 2.0, 'points_cost': 2},
                'GOURMET': {'unit_cost': 3.0, 'points_cost': 3}
            }

            # Update with existing data
            for quality in ['NORMAL', 'FIRST_CHOICE', 'GOURMET']:
                if quality in qualities:
                    quality_data = qualities[quality]
                    if isinstance(quality_data, dict):
                        unit_cost = quality_data.get('unit_cost', quality_data.get('UnitCost', default_qualities[quality]['unit_cost']))
                        points_cost = quality_data.get('points_cost', quality_data.get('PointsCost', default_qualities[quality]['points_cost']))
                        default_qualities[quality] = {'unit_cost': unit_cost, 'points_cost': points_cost}

            normalized_ingredient['quality_costs'] = default_qualities
        else:
            normalized_ingredient['quality_costs'] = {
                'NORMAL': {'unit_cost': 1.0, 'points_cost': 1},
                'FIRST_CHOICE': {'unit_cost': 2.0, 'points_cost': 2},
                'GOURMET': {'unit_cost': 3.0, 'points_cost': 3}
            }

        # Copy other fields as-is
        for key, value in ingredient.items():
            if key.lower() not in ['name', 'tags', 'flavorvalues', 'flavor_values', 'portions', 'qualities', 'quality_costs']:
                normalized_ingredient[key] = value

        normalized.append(normalized_ingredient)

    return normalized

def normalize_matches_data(raw_data: List[Dict]) -> List[Dict]:
    """Normalize matches data to consistent format"""
    normalized = []

    for match in raw_data:
        normalized_match = {
            'A': match.get('IngredientA', match.get('A', '')),
            'B': match.get('IngredientB', match.get('B', '')),
            'MatchValue': match.get('MatchValue', 1)
        }
        normalized.append(normalized_match)

    return normalized

def create_demo_data() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Create demo data when files are not available"""

    # Demo customer types
    demo_customers = [
        {
            "name": "Gourmet",
            "favourite_tags": ["Wine", "Seafood"],
            "secondary_favourite_tags": ["Meat", "Dairy"],
            "tag_score_weight": 1.0,
            "price_score_weight": 0.0,
            "evaluation_score_weight": 1.0,
            "expectations": {"Wine": 0.8, "Seafood": 0.9},
            "sections": {
                "MainCourse": {"probability": 1.0, "cost_expectation": 25.0},
                "Appetizer": {"probability": 0.8, "cost_expectation": 15.0},
                "Dessert": {"probability": 0.9, "cost_expectation": 12.0}
            }
        },
        {
            "name": "BlueCollar",
            "favourite_tags": ["Carbs", "Beer"],
            "secondary_favourite_tags": ["Meat"],
            "tag_score_weight": 0.7,
            "price_score_weight": 1.0,
            "evaluation_score_weight": 0.0,
            "expectations": {"Carbs": 0.9, "Beer": 0.8},
            "sections": {
                "MainCourse": {"probability": 1.0, "cost_expectation": 12.0},
                "Appetizer": {"probability": 0.3, "cost_expectation": 6.0},
                "Dessert": {"probability": 0.2, "cost_expectation": 4.0}
            }
        }
    ]

    # Demo ingredients
    demo_ingredients = [
        {
            "name": "Salmon",
            "tags": ["Seafood", "Premium"],
            "flavor_values": {"SOUR": 1, "SALT": 2, "ACID": 0, "SWEET": 0, "FAT": 4, "UMAMI": 3},
            "portions": {"SMALL": 100, "MEDIUM": 200, "LARGE": 300},
            "quality_costs": {
                "NORMAL": {"unit_cost": 3.0, "points_cost": 2},
                "FIRST_CHOICE": {"unit_cost": 5.0, "points_cost": 3},
                "GOURMET": {"unit_cost": 8.0, "points_cost": 4}
            }
        },
        {
            "name": "Pasta",
            "tags": ["Carbs", "Basic"],
            "flavor_values": {"SOUR": 0, "SALT": 1, "ACID": 0, "SWEET": 1, "FAT": 1, "UMAMI": 1},
            "portions": {"SMALL": 80, "MEDIUM": 120, "LARGE": 200},
            "quality_costs": {
                "NORMAL": {"unit_cost": 0.5, "points_cost": 1},
                "FIRST_CHOICE": {"unit_cost": 1.0, "points_cost": 1},
                "GOURMET": {"unit_cost": 2.0, "points_cost": 2}
            }
        },
        {
            "name": "Tomato",
            "tags": ["Vegetables", "Acid"],
            "flavor_values": {"SOUR": 3, "SALT": 0, "ACID": 4, "SWEET": 2, "FAT": 0, "UMAMI": 2},
            "portions": {"SMALL": 50, "MEDIUM": 100, "LARGE": 150},
            "quality_costs": {
                "NORMAL": {"unit_cost": 0.8, "points_cost": 1},
                "FIRST_CHOICE": {"unit_cost": 1.5, "points_cost": 1},
                "GOURMET": {"unit_cost": 2.5, "points_cost": 2}
            }
        }
    ]

    # Demo matches
    demo_matches = [
        {"A": "Salmon", "B": "Pasta", "MatchValue": 2},
        {"A": "Salmon", "B": "Tomato", "MatchValue": 3},
        {"A": "Pasta", "B": "Tomato", "MatchValue": 3}
    ]

    return demo_customers, demo_ingredients, demo_matches

@st.cache_data
def load_and_validate_data(customers_path: str, ingredients_path: str, matches_path: str) -> Tuple[Optional[List[Dict]], Optional[List[Dict]], Optional[List[Dict]], List[str]]:
    """Load and validate all data files"""
    all_warnings = []

    # Try to load customer types
    customers_raw = load_json_file(customers_path)
    customers = None
    if customers_raw is not None:
        is_valid, warnings = validate_customer_types(customers_raw)
        if is_valid:
            customers = customers_raw
            all_warnings.extend([f"Customers: {w}" for w in warnings])
        else:
            all_warnings.extend([f"Customers ERROR: {w}" for w in warnings])

    # Try to load ingredients
    ingredients_raw = load_json_file(ingredients_path)
    ingredients = None
    if ingredients_raw is not None:
        is_valid, warnings = validate_ingredients_data(ingredients_raw)
        if is_valid:
            ingredients = normalize_ingredients_data(ingredients_raw)
            all_warnings.extend([f"Ingredients: {w}" for w in warnings])
        else:
            all_warnings.extend([f"Ingredients ERROR: {w}" for w in warnings])

    # Try to load matches
    matches_raw = load_json_file(matches_path)
    matches = None
    if matches_raw is not None:
        is_valid, warnings = validate_matches_data(matches_raw)
        if is_valid:
            matches = normalize_matches_data(matches_raw)
            all_warnings.extend([f"Matches: {w}" for w in warnings])
        else:
            all_warnings.extend([f"Matches ERROR: {w}" for w in warnings])

    # If any data is missing, offer demo mode
    if customers is None or ingredients is None or matches is None:
        st.warning("⚠️ Some data files are missing or invalid. Using demo data to show UI functionality.")
        demo_customers, demo_ingredients, demo_matches = create_demo_data()
        return demo_customers, demo_ingredients, demo_matches, all_warnings

    return customers, ingredients, matches, all_warnings