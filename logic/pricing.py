"""
Target-based Pricing and Tier Selection for Chef Planner MVP 0.2
Estimates costs and automatically adjusts ingredient tiers to match cost expectations.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
from .generator import RecipeVariant


# Quality tier multipliers for pricing
TIER_COSTS = {
    'NORMAL': 1.0,
    'FIRST_CHOICE': 1.5,
    'GOURMET': 2.5
}


def estimate_cost(ingredients: List[str], tiers: Dict[str, str],
                 ingredients_df: pd.DataFrame) -> float:
    """
    Estimate total cost of recipe based on ingredient tiers
    """
    total_cost = 0.0

    for ing_name in ingredients:
        ing_row = ingredients_df[ingredients_df['name'] == ing_name]
        if ing_row.empty:
            continue

        ing_data = ing_row.iloc[0]
        tier = tiers.get(ing_name, 'NORMAL')

        # Get base cost from quality_costs
        quality_costs = ing_data.get('quality_costs', {})
        if isinstance(quality_costs, dict) and tier in quality_costs:
            tier_data = quality_costs[tier]
            if isinstance(tier_data, dict):
                unit_cost = tier_data.get('unit_cost', 1.0)
            else:
                unit_cost = 1.0
        else:
            # Fallback to tier multiplier
            base_cost = 1.0
            if isinstance(quality_costs, dict) and 'NORMAL' in quality_costs:
                normal_data = quality_costs['NORMAL']
                if isinstance(normal_data, dict):
                    base_cost = normal_data.get('unit_cost', 1.0)
            unit_cost = base_cost * TIER_COSTS.get(tier, 1.0)

        total_cost += unit_cost

    return round(total_cost, 2)


def target_based_tiering(variant: RecipeVariant, segment: Dict[str, Any],
                        section: str, ingredients_df: pd.DataFrame,
                        cost_expectation: float) -> Tuple[Dict[str, str], float, float]:
    """
    Auto-adjust ingredient tiers to approach target cost expectation
    Returns: (final_tiers, total_cost, suggested_price)
    """
    ingredients = variant.ingredients
    roles = variant.roles

    # Start with all NORMAL tiers
    current_tiers = {ing: 'NORMAL' for ing in ingredients}

    # Initial cost estimate
    current_cost = estimate_cost(ingredients, current_tiers, ingredients_df)

    # If cost is much lower than target, upgrade tiers strategically
    if current_cost < cost_expectation * 0.8:
        current_tiers, current_cost = _upgrade_tiers(
            ingredients, roles, current_tiers, cost_expectation,
            ingredients_df, variant
        )

    # If cost is much higher than target, downgrade tiers
    elif current_cost > cost_expectation * 1.2:
        current_tiers, current_cost = _downgrade_tiers(
            ingredients, roles, current_tiers, cost_expectation,
            ingredients_df
        )

    # Suggested price is close to cost expectation or actual cost if can't reach target
    if abs(current_cost - cost_expectation) <= cost_expectation * 0.15:
        suggested_price = cost_expectation
    else:
        suggested_price = max(current_cost * 1.1, cost_expectation * 0.85)

    return current_tiers, current_cost, round(suggested_price, 2)


def _upgrade_tiers(ingredients: List[str], roles: Dict[str, str],
                  current_tiers: Dict[str, str], target_cost: float,
                  ingredients_df: pd.DataFrame, variant: RecipeVariant) -> Tuple[Dict[str, str], float]:
    """
    Strategically upgrade tiers to approach target cost
    Priority: hero -> premium ingredients (fat/cheese) -> complements
    """
    tiers = current_tiers.copy()

    # Priority order for upgrades
    hero = ingredients[0]  # First ingredient is always hero
    upgrade_priority = []

    # 1. Hero ingredient first
    upgrade_priority.append(hero)

    # 2. Premium ingredients (fat, cheese, base)
    premium_roles = ['fat', 'cheese', 'base']
    for ing in ingredients[1:]:
        if roles.get(ing, '') in premium_roles:
            upgrade_priority.append(ing)

    # 3. Complements
    for ing in ingredients[1:]:
        if roles.get(ing, '') == 'complement':
            upgrade_priority.append(ing)

    # 4. Seasonings last
    for ing in ingredients[1:]:
        if roles.get(ing, '') == 'seasoning':
            upgrade_priority.append(ing)

    # Try upgrading ingredients in priority order
    for ing in upgrade_priority:
        if ing not in ingredients_df['name'].values:
            continue

        current_tier = tiers[ing]

        # Try upgrading to next tier
        if current_tier == 'NORMAL':
            test_tiers = tiers.copy()
            test_tiers[ing] = 'FIRST_CHOICE'
            test_cost = estimate_cost(ingredients, test_tiers, ingredients_df)

            if test_cost <= target_cost * 1.05:  # Allow 5% tolerance
                tiers[ing] = 'FIRST_CHOICE'
                current_cost = test_cost

                # Check if we can upgrade further to GOURMET
                if test_cost < target_cost * 0.9:
                    test_tiers[ing] = 'GOURMET'
                    gourmet_cost = estimate_cost(ingredients, test_tiers, ingredients_df)

                    if gourmet_cost <= target_cost * 1.05:
                        tiers[ing] = 'GOURMET'
                        current_cost = gourmet_cost

        elif current_tier == 'FIRST_CHOICE':
            test_tiers = tiers.copy()
            test_tiers[ing] = 'GOURMET'
            test_cost = estimate_cost(ingredients, test_tiers, ingredients_df)

            if test_cost <= target_cost * 1.05:
                tiers[ing] = 'GOURMET'
                current_cost = test_cost

    final_cost = estimate_cost(ingredients, tiers, ingredients_df)
    return tiers, final_cost


def _downgrade_tiers(ingredients: List[str], roles: Dict[str, str],
                    current_tiers: Dict[str, str], target_cost: float,
                    ingredients_df: pd.DataFrame) -> Tuple[Dict[str, str], float]:
    """
    Strategically downgrade tiers to approach target cost
    Priority: seasonings -> complements -> premium -> hero (last resort)
    """
    tiers = current_tiers.copy()

    # Priority order for downgrades (reverse of upgrade)
    hero = ingredients[0]
    downgrade_priority = []

    # 1. Seasonings first
    for ing in ingredients[1:]:
        if roles.get(ing, '') == 'seasoning':
            downgrade_priority.append(ing)

    # 2. Complements
    for ing in ingredients[1:]:
        if roles.get(ing, '') == 'complement':
            downgrade_priority.append(ing)

    # 3. Premium ingredients
    premium_roles = ['fat', 'cheese', 'base']
    for ing in ingredients[1:]:
        if roles.get(ing, '') in premium_roles:
            downgrade_priority.append(ing)

    # 4. Hero as last resort
    downgrade_priority.append(hero)

    # Try downgrading ingredients in priority order
    current_cost = estimate_cost(ingredients, tiers, ingredients_df)

    for ing in downgrade_priority:
        if current_cost <= target_cost * 1.1:  # Within 10% tolerance
            break

        if ing not in ingredients_df['name'].values:
            continue

        current_tier = tiers[ing]

        # Try downgrading to lower tier
        if current_tier == 'GOURMET':
            test_tiers = tiers.copy()
            test_tiers[ing] = 'FIRST_CHOICE'
            test_cost = estimate_cost(ingredients, test_tiers, ingredients_df)

            if test_cost >= target_cost * 0.8:  # Don't go too low
                tiers[ing] = 'FIRST_CHOICE'
                current_cost = test_cost

        elif current_tier == 'FIRST_CHOICE':
            test_tiers = tiers.copy()
            test_tiers[ing] = 'NORMAL'
            test_cost = estimate_cost(ingredients, test_tiers, ingredients_df)

            if test_cost >= target_cost * 0.7:  # Don't go too low
                tiers[ing] = 'NORMAL'
                current_cost = test_cost

    final_cost = estimate_cost(ingredients, tiers, ingredients_df)
    return tiers, final_cost


def get_cost_deviation_badge(actual_cost: float, target_cost: float) -> Tuple[str, str]:
    """
    Get badge text and color for cost deviation
    Returns: (badge_text, badge_color)
    """
    if target_cost <= 0:
        return "Target sconosciuto", "secondary"

    deviation_pct = ((actual_cost - target_cost) / target_cost) * 100

    if abs(deviation_pct) <= 10:
        return "Target ✓", "success"
    elif deviation_pct > 10:
        over_pct = int(deviation_pct)
        return f"Sopra target +{over_pct}%", "warning" if over_pct <= 25 else "danger"
    else:
        under_pct = int(abs(deviation_pct))
        return f"Sotto target -{under_pct}%", "info"


def get_tier_display_name(tier: str) -> str:
    """Get user-friendly tier names"""
    tier_names = {
        'NORMAL': 'Normale',
        'FIRST_CHOICE': 'Prima Scelta',
        'GOURMET': 'Gourmet'
    }
    return tier_names.get(tier, tier)