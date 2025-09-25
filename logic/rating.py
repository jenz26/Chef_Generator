"""
Recipe Rating and Segment Fit Calculation for Chef Planner MVP 0.2
Implements the 1-5 star rating system with breakdown and segment fit scoring.
"""

from typing import List, Dict, Any, Tuple, Set
import pandas as pd
from .generator import RecipeVariant


# Constants for rating calculation
DIVISOR_STARS = 20
QUALITY_UNIT = {"NORMAL": 0.0, "FIRST_CHOICE": 0.7, "GOURMET": 1.4}
COMPAT_MAX = 15


def compute_perks(variant: RecipeVariant, ingredients_df: pd.DataFrame) -> Tuple[List[str], float]:
    """
    Compute active perks and their bonus value (capped at +30)
    Returns: (active_perks_list, total_perk_bonus)
    """
    perks = []
    total_bonus = 0.0

    ingredients = variant.ingredients
    flavor_profile = variant.flavor_profile
    roles = variant.roles

    # Get ingredient data
    ing_data = {}
    for ing_name in ingredients:
        ing_row = ingredients_df[ingredients_df['name'] == ing_name]
        if not ing_row.empty:
            ing_data[ing_name] = ing_row.iloc[0]

    # 1. BalancedRecipe: +4...+8
    if _is_balanced_recipe(flavor_profile):
        bonus = 6.0  # Average of range
        perks.append("BalancedRecipe")
        total_bonus += bonus

    # 2. SayCheese: +2...+6
    cheese_bonus = _calculate_cheese_bonus(ingredients, ing_data, variant)
    if cheese_bonus > 0:
        perks.append("SayCheese")
        total_bonus += cheese_bonus

    # 3. VeggiesPower: +2...+6
    veggie_bonus = _calculate_veggie_bonus(ingredients, ing_data)
    if veggie_bonus > 0:
        perks.append("VeggiesPower")
        total_bonus += veggie_bonus

    # 4. ComplexAroma: +3...+8
    aroma_bonus = _calculate_aroma_bonus(ingredients, ing_data)
    if aroma_bonus > 0:
        perks.append("ComplexAroma")
        total_bonus += aroma_bonus

    # Cap total perk bonus at +30
    total_bonus = min(total_bonus, 30.0)

    return perks, total_bonus


def quality_bonus(tiers: Dict[str, str], cap: int = 20) -> float:
    """
    Calculate quality bonus from ingredient tiers
    NORMAL=0, FIRST_CHOICE=+0.7, GOURMET=+1.4, capped at +20
    """
    total_bonus = 0.0

    for tier in tiers.values():
        total_bonus += QUALITY_UNIT.get(tier, 0.0)

    return min(total_bonus, float(cap))


def compatibility_bonus(avg_mv: float, triangles: int) -> float:
    """
    Calculate compatibility bonus
    Formula: ((avg_mv - 1)/2)*15 + min(triangles, 3)
    """
    # Normalize average MatchValue to 0-1 scale, then multiply by 15
    mv_bonus = ((avg_mv - 1.0) / 2.0) * COMPAT_MAX

    # Triangle bonus: +1 per triangle, max +3
    triangle_bonus = min(triangles, 3)

    return max(0.0, mv_bonus + triangle_bonus)


def complexity_tuning(count_ing: int, template_category: str, is_gourmet: bool) -> float:
    """
    Complexity adjustment based on ingredient count vs expected range
    Returns: -5...+5, with +1 extra for gourmet coherence
    """
    # Expected ranges per category
    ideal_ranges = {
        "Pasta & Riso": (8, 10),
        "Carne": (6, 8),
        "Pesce": (6, 8),
        "Vegetariano": (5, 7),
        "Dessert": (6, 8),
        "Burger": (5, 6)
    }

    ideal_min, ideal_max = ideal_ranges.get(template_category, (6, 8))
    ideal_center = (ideal_min + ideal_max) / 2

    # Calculate deviation from ideal
    deviation = abs(count_ing - ideal_center)

    if deviation <= 1:
        complexity_score = 2.0  # Perfect complexity
    elif deviation <= 2:
        complexity_score = 0.0  # Acceptable complexity
    elif deviation <= 3:
        complexity_score = -2.0  # Slightly off
    else:
        complexity_score = -5.0  # Too far from ideal

    # Bonus for gourmet coherence
    gourmet_bonus = 1.0 if is_gourmet else 0.0

    return complexity_score + gourmet_bonus


def final_stars(evaluation_base: float, perk: float, quality: float,
               compat: float, complexity: float, divisor: int = DIVISOR_STARS) -> float:
    """
    Calculate final star rating (1-5 stars)
    Formula: (EvaluationBase + PerkBonus + QualityBonus + CompatibilityBonus + ComplexityTuning) / divisor, clamped 1-5
    """
    total_score = evaluation_base + perk + quality + compat + complexity
    stars = total_score / divisor

    # Clamp to 1-5 range
    return max(1.0, min(5.0, stars))


def segment_fit(stars: float, segment: Dict[str, Any], section: str,
               suggested_price: float, variant: RecipeVariant,
               ingredients_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate segment fit percentage breakdown
    Returns: {price_fit, tag_fit, eval_fit, total_fit}
    """
    # Get segment data
    price_weight = segment.get('price_score_weight', 0.33)
    tag_weight = segment.get('tag_score_weight', 0.33)
    eval_weight = segment.get('evaluation_score_weight', 0.33)

    # Normalize weights
    total_weight = price_weight + tag_weight + eval_weight
    if total_weight > 0:
        price_weight /= total_weight
        tag_weight /= total_weight
        eval_weight /= total_weight

    # Get section cost expectation
    from domain_utils import get_customer_section_info
    section_info = get_customer_section_info(segment, section)
    cost_expectation = section_info.get('cost_expectation', 10.0)

    # 1. Price Fit: 100% if price matches cost_expectation, linear drop ±15%
    price_fit = _calculate_price_fit(suggested_price, cost_expectation)

    # 2. Tag Fit: coverage of favourite/expected tags
    tag_fit = _calculate_tag_fit(segment, variant, ingredients_df)

    # 3. Eval Fit: star rating normalized (5★=100%, 4★=80%, etc.)
    eval_fit = (stars / 5.0) * 100.0

    # Total weighted fit
    total_fit = (price_fit * price_weight + tag_fit * tag_weight + eval_fit * eval_weight)

    return {
        'price_fit': round(price_fit, 1),
        'tag_fit': round(tag_fit, 1),
        'eval_fit': round(eval_fit, 1),
        'total_fit': round(total_fit, 1)
    }


def get_rating_breakdown(variant: RecipeVariant, tiers: Dict[str, str],
                        template_category: str, ingredients_df: pd.DataFrame,
                        is_gourmet: bool = False) -> Dict[str, float]:
    """
    Get detailed rating breakdown for display
    Returns: {evaluation_base, perk_bonus, quality_bonus, compatibility_bonus, complexity_tuning, total_score, stars}
    """
    # Base evaluation (can be adjusted based on template)
    evaluation_base = 10.0

    # Calculate each component
    perks, perk_bonus = compute_perks(variant, ingredients_df)
    quality_bonus_val = quality_bonus(tiers)
    compat_bonus = compatibility_bonus(variant.compatibility_avg, variant.triangles)
    complexity_adj = complexity_tuning(len(variant.ingredients), template_category, is_gourmet)

    # Calculate final rating
    total_score = evaluation_base + perk_bonus + quality_bonus_val + compat_bonus + complexity_adj
    stars = final_stars(evaluation_base, perk_bonus, quality_bonus_val, compat_bonus, complexity_adj)

    return {
        'evaluation_base': round(evaluation_base, 1),
        'perk_bonus': round(perk_bonus, 1),
        'quality_bonus': round(quality_bonus_val, 1),
        'compatibility_bonus': round(compat_bonus, 1),
        'complexity_tuning': round(complexity_adj, 1),
        'total_score': round(total_score, 1),
        'stars': round(stars, 1),
        'active_perks': perks
    }


# Helper functions
def _is_balanced_recipe(flavor_profile: Dict[str, int]) -> bool:
    """
    Check if recipe has balanced flavor profile
    Criteria: no axis > 2.5x median, ≥3 axes > 0
    """
    if not flavor_profile:
        return False

    values = [v for v in flavor_profile.values() if v > 0]
    if len(values) < 3:  # Need at least 3 active flavor axes
        return False

    if not values:
        return False

    sorted_values = sorted(values)
    median_val = sorted_values[len(sorted_values) // 2]

    if median_val <= 0:
        return False

    # Check if any value is more than 2.5x the median
    max_val = max(values)
    if max_val > 2.5 * median_val:
        return False

    return True


def _calculate_cheese_bonus(ingredients: List[str], ing_data: Dict[str, Any],
                           variant: RecipeVariant) -> float:
    """Calculate SayCheese perk bonus (+2...+6)"""
    has_cheese = False

    for ing_name in ingredients:
        if ing_name in ing_data:
            tags = ing_data[ing_name].get('tags', [])
            if isinstance(tags, list) and 'Cheese' in tags:
                has_cheese = True
                break

    if not has_cheese:
        return 0.0

    # Check if cheese makes sense for the recipe style
    # Higher bonus for styles that traditionally use cheese
    if variant.style in ['classico', 'umami']:
        return 4.0  # Good cheese usage
    else:
        return 2.0  # Acceptable cheese usage


def _calculate_veggie_bonus(ingredients: List[str], ing_data: Dict[str, Any]) -> float:
    """Calculate VeggiesPower perk bonus (+2...+6)"""
    veggie_count = 0
    total_count = len(ingredients)

    veggie_tags = ['Vegetables', 'Herbs', 'Legumes', 'Salad', 'Tomato']

    for ing_name in ingredients:
        if ing_name in ing_data:
            tags = ing_data[ing_name].get('tags', [])
            if isinstance(tags, list):
                if any(vtag in tags for vtag in veggie_tags):
                    veggie_count += 1

    if total_count == 0:
        return 0.0

    veggie_ratio = veggie_count / total_count

    if veggie_ratio >= 0.3:  # ≥30% vegetables
        return 5.0
    elif veggie_ratio >= 0.2:  # ≥20% vegetables
        return 3.0
    else:
        return 0.0


def _calculate_aroma_bonus(ingredients: List[str], ing_data: Dict[str, Any]) -> float:
    """Calculate ComplexAroma perk bonus (+3...+8)"""
    aroma_tags = ['Herbs', 'Spices', 'Garlic', 'Onion', 'Citrus', 'Wine']
    aroma_count = 0

    for ing_name in ingredients:
        if ing_name in ing_data:
            tags = ing_data[ing_name].get('tags', [])
            if isinstance(tags, list):
                if any(atag in tags for atag in aroma_tags):
                    aroma_count += 1

    if aroma_count >= 4:
        return 7.0  # Very complex aroma
    elif aroma_count >= 3:
        return 5.0  # Good aroma complexity
    else:
        return 0.0


def _calculate_price_fit(suggested_price: float, cost_expectation: float) -> float:
    """Calculate price fit percentage (100% at target, linear drop ±15%)"""
    if cost_expectation <= 0:
        return 50.0  # Neutral if no expectation

    deviation_pct = abs(suggested_price - cost_expectation) / cost_expectation

    if deviation_pct <= 0.05:  # Within 5%
        return 100.0
    elif deviation_pct <= 0.15:  # Within 15%
        # Linear drop from 100% to 70%
        return 100.0 - (deviation_pct - 0.05) / 0.10 * 30.0
    else:
        # Beyond 15% deviation
        return max(20.0, 70.0 - (deviation_pct - 0.15) * 100.0)


def _calculate_tag_fit(segment: Dict[str, Any], variant: RecipeVariant,
                      ingredients_df: pd.DataFrame) -> float:
    """Calculate tag fit based on coverage of segment preferences"""
    # Get segment favorite tags
    favourite_tags = set(segment.get('favourite_tags', []))
    secondary_tags = set(segment.get('secondary_favourite_tags', []))
    expectations = segment.get('expectations', {})

    # Collect all tags from recipe ingredients
    recipe_tags = set()
    for ing_name in variant.ingredients:
        ing_row = ingredients_df[ingredients_df['name'] == ing_name]
        if not ing_row.empty:
            ing_tags = ing_row.iloc[0].get('tags', [])
            if isinstance(ing_tags, list):
                recipe_tags.update(ing_tags)

    # Calculate coverage scores
    total_score = 0.0
    max_possible = 0.0

    # Favourite tags coverage (weight = 3)
    if favourite_tags:
        covered_fav = len(favourite_tags.intersection(recipe_tags))
        total_fav = len(favourite_tags)
        fav_score = (covered_fav / total_fav) * 3.0
        total_score += fav_score
        max_possible += 3.0

    # Secondary favourite tags coverage (weight = 2)
    if secondary_tags:
        covered_sec = len(secondary_tags.intersection(recipe_tags))
        total_sec = len(secondary_tags)
        sec_score = (covered_sec / total_sec) * 2.0
        total_score += sec_score
        max_possible += 2.0

    # Expectations coverage (weight = 2)
    if expectations:
        exp_score = 0.0
        for tag, weight in expectations.items():
            if tag in recipe_tags:
                exp_score += min(weight, 1.0)  # Cap individual tag bonus
        exp_score = min(exp_score, 2.0)  # Cap total expectations bonus
        total_score += exp_score
        max_possible += 2.0

    if max_possible > 0:
        return (total_score / max_possible) * 100.0
    else:
        return 50.0  # Neutral if no preferences defined