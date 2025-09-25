"""
Domain utilities for Chef Planner
Helper functions for ingredient matching, compatibility checks, and data manipulation.
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import streamlit as st
import pandas as pd

def find_ingredient_by_name(ingredients: List[Dict], name: str) -> Optional[Dict]:
    """Find an ingredient by name (case-insensitive)"""
    if not name:
        return None

    name_lower = name.lower()
    for ingredient in ingredients:
        ingredient_name = ingredient.get('name', '').lower()
        if ingredient_name == name_lower:
            return ingredient
    return None

def get_ingredient_names(ingredients: List[Dict]) -> List[str]:
    """Get list of all ingredient names"""
    return [ingredient.get('name', '') for ingredient in ingredients if ingredient.get('name')]

def build_matches_lookup(matches: List[Dict]) -> Dict[str, List[Tuple[str, int]]]:
    """
    Build a lookup dictionary for ingredient matches
    Returns: {ingredient_name: [(partner_name, match_value), ...]}
    """
    lookup = {}

    for match in matches:
        ingredient_a = match.get('A', '')
        ingredient_b = match.get('B', '')
        match_value = match.get('MatchValue', 1)

        if ingredient_a and ingredient_b:
            # Add bidirectional relationships
            if ingredient_a not in lookup:
                lookup[ingredient_a] = []
            if ingredient_b not in lookup:
                lookup[ingredient_b] = []

            lookup[ingredient_a].append((ingredient_b, match_value))
            lookup[ingredient_b].append((ingredient_a, match_value))

    # Sort partners by match value (descending) then alphabetically
    for ingredient in lookup:
        lookup[ingredient].sort(key=lambda x: (-x[1], x[0].lower()))

    return lookup

def get_top_partners(ingredient_name: str, matches_lookup: Dict[str, List[Tuple[str, int]]], limit: int = 10) -> List[Tuple[str, int]]:
    """Get top N partners for an ingredient, sorted by match value"""
    if ingredient_name not in matches_lookup:
        return []

    partners = matches_lookup[ingredient_name]
    return partners[:limit]

def filter_ingredients_by_tags(ingredients: List[Dict], required_tags: List[str] = None,
                              forbidden_tags: List[str] = None) -> List[Dict]:
    """Filter ingredients based on required and forbidden tags"""
    if not required_tags and not forbidden_tags:
        return ingredients

    filtered = []

    for ingredient in ingredients:
        ingredient_tags = ingredient.get('tags', [])
        if isinstance(ingredient_tags, str):
            ingredient_tags = [tag.strip() for tag in ingredient_tags.split(',')]

        # Check required tags
        if required_tags:
            has_required = any(tag in ingredient_tags for tag in required_tags)
            if not has_required:
                continue

        # Check forbidden tags
        if forbidden_tags:
            has_forbidden = any(tag in ingredient_tags for tag in forbidden_tags)
            if has_forbidden:
                continue

        filtered.append(ingredient)

    return filtered

def get_ingredient_tags_summary(ingredients: List[Dict]) -> Dict[str, int]:
    """Get a summary of all tags and their frequency"""
    tag_counts = {}

    for ingredient in ingredients:
        ingredient_tags = ingredient.get('tags', [])
        if isinstance(ingredient_tags, str):
            ingredient_tags = [tag.strip() for tag in ingredient_tags.split(',')]

        for tag in ingredient_tags:
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))

def create_flavor_radar_data(ingredient: Dict[str, Any]) -> Dict[str, int]:
    """Create radar chart data for ingredient flavor profile"""
    flavor_values = ingredient.get('flavor_values', {})

    # Default flavor values
    default_flavors = {'SOUR': 0, 'SALT': 0, 'ACID': 0, 'SWEET': 0, 'FAT': 0, 'UMAMI': 0}
    default_flavors.update(flavor_values)

    return default_flavors

def format_ingredient_quality_costs(ingredient: Dict[str, Any]) -> str:
    """Format ingredient quality costs for display"""
    quality_costs = ingredient.get('quality_costs', {})

    if not quality_costs:
        return "No cost data available"

    lines = []
    for quality in ['NORMAL', 'FIRST_CHOICE', 'GOURMET']:
        if quality in quality_costs:
            cost_data = quality_costs[quality]
            unit_cost = cost_data.get('unit_cost', 0)
            points_cost = cost_data.get('points_cost', 0)
            lines.append(f"**{quality}**: €{unit_cost:.2f} ({points_cost} pts)")

    return "\n".join(lines) if lines else "No cost data available"

def get_section_names() -> List[str]:
    """Get standard section names"""
    return ["Appetizer", "MainCourse", "SideDish", "Soup", "Salad", "Dessert", "Beverage"]

def get_customer_section_info(customer: Dict[str, Any], section: str) -> Dict[str, Any]:
    """Get section information for a customer"""
    sections_data = customer.get('sections', {})

    # Try multiple possible key formats
    section_keys = [section, section.lower(), f"menu_section_info.{section}"]

    for key in section_keys:
        if key in sections_data:
            return sections_data[key]

    # If not found, try nested structure
    menu_section_info = customer.get('menu_section_info', {})
    if section in menu_section_info:
        return menu_section_info[section]

    # Default values
    return {
        "probability": 0.5,
        "cost_expectation": 10.0
    }

def format_customer_expectations(customer: Dict[str, Any]) -> str:
    """Format customer expectations for display"""
    expectations = customer.get('expectations', {})

    if not expectations:
        return "No specific expectations"

    lines = []
    for tag, weight in expectations.items():
        if weight > 1.0:
            lines.append(f"**{tag}**: {weight:.1f}x (loves)")
        elif weight > 0.8:
            lines.append(f"**{tag}**: {weight:.1f}x (prefers)")
        elif weight < 0.5:
            lines.append(f"**{tag}**: {weight:.1f}x (dislikes)")

    return "\n".join(lines) if lines else "No specific expectations"

def format_customer_weights(customer: Dict[str, Any]) -> str:
    """Format customer scoring weights for display"""
    tag_weight = customer.get('tag_score_weight', 0.5)
    price_weight = customer.get('price_score_weight', 0.5)
    eval_weight = customer.get('evaluation_score_weight', 0.5)

    return f"""
**Tag Focus**: {tag_weight:.1f} (cares about favorite ingredients)
**Price Focus**: {price_weight:.1f} (sensitive to cost)
**Quality Focus**: {eval_weight:.1f} (values high-quality recipes)
"""

def search_ingredients(ingredients: List[Dict], query: str) -> List[str]:
    """Search ingredients by name (for autocomplete)"""
    if not query:
        return []

    query_lower = query.lower()
    matches = []

    for ingredient in ingredients:
        name = ingredient.get('name', '')
        if query_lower in name.lower():
            matches.append(name)

    return sorted(matches)[:20]  # Limit to 20 results

def validate_template_unlock(template_name: str, available_points: int, current_unlocked: List[str]) -> Tuple[bool, str]:
    """Check if a template can be unlocked"""
    from templates_catalog import TEMPLATES_CATALOG

    if template_name in current_unlocked:
        return True, f"✅ {template_name} is already unlocked"

    if template_name not in TEMPLATES_CATALOG:
        return False, f"❌ Template '{template_name}' not found"

    template = TEMPLATES_CATALOG[template_name]
    required_points = template.points

    if required_points <= available_points:
        return True, f"✅ Can unlock {template_name} for {required_points} points"
    else:
        needed = required_points - available_points
        return False, f"❌ Need {needed} more points to unlock {template_name}"

def calculate_total_unlock_cost(template_names: List[str]) -> int:
    """Calculate total cost to unlock a list of templates"""
    from templates_catalog import TEMPLATES_CATALOG

    total_cost = 0
    for template_name in template_names:
        if template_name in TEMPLATES_CATALOG:
            total_cost += TEMPLATES_CATALOG[template_name].points

    return total_cost


# New functions for MVP 0.2

def flavor_profile_for(ingredients: List[str], ingredients_df: pd.DataFrame) -> Dict[str, int]:
    """
    Calculate combined flavor profile for a list of ingredients
    """
    profile = {'SOUR': 0, 'SALT': 0, 'ACID': 0, 'SWEET': 0, 'FAT': 0, 'UMAMI': 0}

    for ing_name in ingredients:
        ing_row = ingredients_df[ingredients_df['name'] == ing_name]
        if not ing_row.empty:
            ing_flavors = ing_row.iloc[0].get('flavor_values', {})
            if isinstance(ing_flavors, dict):
                for flavor, value in ing_flavors.items():
                    if flavor in profile:
                        profile[flavor] += int(value)

    return profile


def avg_matchvalue(ingredients: List[str], matches_df: pd.DataFrame) -> Tuple[float, int]:
    """
    Calculate average MatchValue and count of strong triangular relationships
    Returns: (average_match_value, triangle_count)
    """
    if len(ingredients) < 2:
        return 1.0, 0

    total_match_value = 0.0
    pair_count = 0

    # Calculate average match value for all pairs
    for i in range(len(ingredients)):
        for j in range(i + 1, len(ingredients)):
            ing_a, ing_b = ingredients[i], ingredients[j]

            # Find match
            match = matches_df[
                ((matches_df['A'] == ing_a) & (matches_df['B'] == ing_b)) |
                ((matches_df['A'] == ing_b) & (matches_df['B'] == ing_a))
            ]

            if not match.empty:
                total_match_value += match.iloc[0]['MatchValue']
            else:
                total_match_value += 1.0  # Neutral match

            pair_count += 1

    avg_mv = total_match_value / max(pair_count, 1)

    # Count triangular relationships (all 3 pairs have MatchValue >= 2)
    triangles = 0
    if len(ingredients) >= 3:
        for i in range(len(ingredients)):
            for j in range(i + 1, len(ingredients)):
                for k in range(j + 1, len(ingredients)):
                    ing_a, ing_b, ing_c = ingredients[i], ingredients[j], ingredients[k]

                    # Check all three pairs
                    pairs = [(ing_a, ing_b), (ing_a, ing_c), (ing_b, ing_c)]
                    all_strong = True

                    for pair_a, pair_b in pairs:
                        match = matches_df[
                            ((matches_df['A'] == pair_a) & (matches_df['B'] == pair_b)) |
                            ((matches_df['A'] == pair_b) & (matches_df['B'] == pair_a))
                        ]

                        if match.empty or match.iloc[0]['MatchValue'] < 2:
                            all_strong = False
                            break

                    if all_strong:
                        triangles += 1

    return round(avg_mv, 2), triangles


def template_category(template_name: str) -> str:
    """
    Get the category for a template
    """
    from templates_catalog import TEMPLATES_CATALOG
    if template_name in TEMPLATES_CATALOG:
        return TEMPLATES_CATALOG[template_name].category
    return "Unknown"


def is_gourmet_segment(segment_name: str, segment_data: Dict[str, Any] = None) -> bool:
    """
    Heuristic to determine if a segment is gourmet-oriented
    Based on name containing "Gourmet" or high eval/tag weights
    """
    if not segment_name:
        return False

    # Name-based check
    if 'gourmet' in segment_name.lower():
        return True

    # Weight-based check
    if segment_data:
        eval_weight = segment_data.get('evaluation_score_weight', 0.5)
        tag_weight = segment_data.get('tag_score_weight', 0.5)
        price_weight = segment_data.get('price_score_weight', 0.5)

        # High focus on quality/tags and low focus on price
        if eval_weight >= 0.8 and tag_weight >= 0.7 and price_weight <= 0.3:
            return True

    return False


def collect_tags(ingredients: List[str], ingredients_df: pd.DataFrame) -> Set[str]:
    """
    Collect all unique tags from a list of ingredients
    """
    all_tags = set()

    for ing_name in ingredients:
        ing_row = ingredients_df[ingredients_df['name'] == ing_name]
        if not ing_row.empty:
            tags = ing_row.iloc[0].get('tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                # Handle comma-separated string tags
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                all_tags.update(tag_list)

    return all_tags


def format_role_display(role: str) -> str:
    """
    Get user-friendly display name for ingredient roles
    """
    role_names = {
        'hero': '🌟 Protagonista',
        'base': '🍝 Base',
        'complement': '🥄 Complemento',
        'seasoning': '🌿 Condimento',
        'fat': '🧈 Grassi',
        'cheese': '🧀 Formaggio'
    }
    return role_names.get(role, role.title())


def get_ingredient_display_info(ing_name: str, ingredients_df: pd.DataFrame,
                               role: str, tier: str) -> Dict[str, Any]:
    """
    Get formatted display information for an ingredient
    """
    ing_row = ingredients_df[ingredients_df['name'] == ing_name]
    if ing_row.empty:
        return {
            'name': ing_name,
            'role': format_role_display(role),
            'tier': tier,
            'tags': [],
            'cost': 0.0
        }

    ing_data = ing_row.iloc[0]
    quality_costs = ing_data.get('quality_costs', {})

    # Get cost for tier
    cost = 0.0
    if isinstance(quality_costs, dict) and tier in quality_costs:
        tier_data = quality_costs[tier]
        if isinstance(tier_data, dict):
            cost = tier_data.get('unit_cost', 0.0)

    return {
        'name': ing_name,
        'role': format_role_display(role),
        'tier': tier,
        'tags': ing_data.get('tags', []),
        'cost': cost
    }