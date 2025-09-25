"""
Recipe Variant Generator for Chef Planner MVP 0.2
Auto-generates 2-3 coherent recipe variants from segment, section, template, anchor ingredient.
"""

from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass
import pandas as pd
import random
import streamlit as st


@dataclass
class RecipeVariant:
    """Represents a generated recipe variant"""
    ingredients: List[str]  # First is always the hero/anchor
    roles: Dict[str, str]   # ingredient -> role mapping
    tiers: Dict[str, str]   # ingredient -> tier mapping (filled by pricing)
    flavor_profile: Dict[str, int]  # SOUR, SALT, ACID, SWEET, FAT, UMAMI
    compatibility_avg: float  # Average MatchValue (1-3)
    triangles: int  # Number of strong triangular relationships
    notes: str      # Generation explanation
    style: str      # Variant style: "classico", "fresco", "umami"


def generate_variants(segment: Dict[str, Any], section: str, template: str,
                     anchor_name: str, ingredients_df: pd.DataFrame,
                     matches_df: pd.DataFrame, templates_meta: Dict[str, Any],
                     n_variants: int = 3) -> List[RecipeVariant]:
    """
    Generate 2-3 coherent recipe variants based on inputs
    """
    # Find anchor ingredient
    anchor_row = ingredients_df[ingredients_df['name'] == anchor_name]
    if anchor_row.empty:
        raise ValueError(f"Anchor ingredient '{anchor_name}' not found")

    anchor_row = anchor_row.iloc[0]

    # Validate template compatibility (reuse existing logic)
    from templates_catalog import check_template_compatibility
    is_compat, msg = check_template_compatibility(template, anchor_row.to_dict())
    if not is_compat and "❌" in msg:
        raise ValueError(f"Template incompatible with anchor: {msg}")

    # Build candidate pool
    candidate_pool = build_candidate_pool(template, anchor_row, ingredients_df, matches_df)

    # Get template category and ingredient range
    template_category = _get_template_category(template)
    min_ing, max_ing = _get_ingredient_range(template_category)

    variants = []
    styles = ["classico", "fresco", "umami"]

    for i in range(min(n_variants, 3)):
        style = styles[i] if i < len(styles) else "classico"

        variant = _generate_single_variant(
            anchor_name, anchor_row, candidate_pool, template, template_category,
            segment, min_ing, max_ing, matches_df, style, i
        )
        variants.append(variant)

    return variants


def build_candidate_pool(template: str, anchor_row: pd.Series,
                        ingredients_df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build pool of candidate ingredients compatible with template and anchor
    """
    # Start with all ingredients except the anchor
    candidates = ingredients_df[ingredients_df['name'] != anchor_row['name']].copy()

    # Apply template-specific filters
    template_lower = template.lower()

    # Vegetarian templates: no meat/seafood
    if any(veg_word in template_lower for veg_word in ['veggies', 'vegetable', 'salad', 'velvety']):
        candidates = candidates[~candidates['tags'].apply(
            lambda tags: any(tag in tags for tag in ['Meat', 'Seafood']) if isinstance(tags, list) else False
        )]

    # Veggie Burger: no meat/seafood
    if template == 'Veggie Burger':
        candidates = candidates[~candidates['tags'].apply(
            lambda tags: any(tag in tags for tag in ['Meat', 'Seafood']) if isinstance(tags, list) else False
        )]

    # Dessert templates: no meat/seafood for main roles
    dessert_templates = ['Pie', 'Cookies', 'Semifreddo', 'Pastries', 'Cheesecake', 'Ice Cream', 'Fried Dessert', 'Millefeuille']
    if template in dessert_templates:
        # Allow meat/seafood for minor roles but not as primary ingredients
        pass  # We'll handle this in role assignment

    # Calculate match scores with anchor
    anchor_matches = matches_df[
        (matches_df['A'] == anchor_row['name']) | (matches_df['B'] == anchor_row['name'])
    ]

    match_scores = {}
    for _, match in anchor_matches.iterrows():
        other_ing = match['B'] if match['A'] == anchor_row['name'] else match['A']
        match_scores[other_ing] = match['MatchValue']

    # Add match scores to candidates
    candidates['anchor_match'] = candidates['name'].map(match_scores).fillna(1.0)

    # Score by segment preferences
    segment_tags = set()
    if 'favourite_tags' in segment:
        segment_tags.update(segment['favourite_tags'])
    if 'secondary_favourite_tags' in segment:
        segment_tags.update(segment['secondary_favourite_tags'])

    def calc_segment_score(tags):
        if not isinstance(tags, list):
            return 0
        return sum(1 for tag in tags if tag in segment_tags)

    candidates['segment_score'] = candidates['tags'].apply(calc_segment_score)

    # Sort by combined score (anchor compatibility + segment preference)
    candidates['total_score'] = candidates['anchor_match'] * 2 + candidates['segment_score']
    candidates = candidates.sort_values('total_score', ascending=False)

    return candidates


def score_combo(ingredients: List[str], matches_df: pd.DataFrame) -> float:
    """
    Calculate combination score based on MatchValue relationships
    Weights: 3>2>1, with triangulation bonuses
    """
    if len(ingredients) < 2:
        return 0.0

    total_score = 0.0
    pair_count = 0

    # Score all pairs
    for i in range(len(ingredients)):
        for j in range(i + 1, len(ingredients)):
            ing_a, ing_b = ingredients[i], ingredients[j]

            # Find match value
            match = matches_df[
                ((matches_df['A'] == ing_a) & (matches_df['B'] == ing_b)) |
                ((matches_df['A'] == ing_b) & (matches_df['B'] == ing_a))
            ]

            if not match.empty:
                match_value = match.iloc[0]['MatchValue']
                # Weight: 3=3.0, 2=2.0, 1=1.0
                total_score += float(match_value)
                pair_count += 1
            else:
                # No explicit match = neutral (1.0)
                total_score += 1.0
                pair_count += 1

    # Calculate triangulation bonus
    triangle_bonus = _count_triangles(ingredients, matches_df) * 0.5

    return (total_score / max(pair_count, 1)) + triangle_bonus


def balance_penalty(flavor_profile: Dict[str, int]) -> float:
    """
    Soft penalty for unbalanced flavor profiles
    """
    if not flavor_profile:
        return 0.0

    values = [v for v in flavor_profile.values() if v > 0]
    if len(values) < 2:
        return 0.3  # Too simple

    # Check if any flavor dominates too much
    max_val = max(values)
    median_val = sorted(values)[len(values) // 2] if values else 1

    if max_val > 2.5 * median_val and median_val > 0:
        # Check for compensations
        salt = flavor_profile.get('SALT', 0)
        acid = flavor_profile.get('ACID', 0)
        fat = flavor_profile.get('FAT', 0)
        sweet = flavor_profile.get('SWEET', 0)

        # SALT:ACID ratio check
        if salt > 0 and acid > 0:
            salt_acid_ratio = salt / acid
            if salt_acid_ratio > 3 and fat == 0 and sweet == 0:
                return 0.4  # Uncompensated salt dominance

        return 0.2  # Mild imbalance

    return 0.0  # Balanced


def role_assignment(template: str, anchor: str, others: List[str],
                   ingredients_df: pd.DataFrame) -> Dict[str, str]:
    """
    Assign roles to ingredients: hero/complement/seasoning/fat/cheese/base
    """
    roles = {anchor: "hero"}

    # Get ingredient data for role assignment
    ing_data = {}
    for ing in [anchor] + others:
        ing_row = ingredients_df[ingredients_df['name'] == ing]
        if not ing_row.empty:
            ing_data[ing] = ing_row.iloc[0]

    # Assign roles based on tags and template context
    template_lower = template.lower()
    remaining = others.copy()

    # Assign base ingredients for pasta/rice templates
    if any(carb in template_lower for carb in ['pasta', 'rice', 'risotto', 'gnocchi', 'lasagne']):
        for ing in remaining[:]:
            if ing in ing_data:
                tags = ing_data[ing].get('tags', [])
                if isinstance(tags, list) and any(tag in tags for tag in ['Pasta', 'Rice', 'Carbs']):
                    roles[ing] = "base"
                    remaining.remove(ing)
                    break

    # Assign fat sources
    for ing in remaining[:]:
        if ing in ing_data:
            tags = ing_data[ing].get('tags', [])
            if isinstance(tags, list) and any(tag in tags for tag in ['Oil', 'Butter', 'Fat']):
                roles[ing] = "fat"
                remaining.remove(ing)
                break

    # Assign cheese
    for ing in remaining[:]:
        if ing in ing_data:
            tags = ing_data[ing].get('tags', [])
            if isinstance(tags, list) and 'Cheese' in tags:
                roles[ing] = "cheese"
                remaining.remove(ing)
                break

    # Assign seasonings and herbs
    seasoning_count = 0
    for ing in remaining[:]:
        if ing in ing_data:
            tags = ing_data[ing].get('tags', [])
            if isinstance(tags, list) and any(tag in tags for tag in ['Herbs', 'Spices', 'Seasoning', 'Condiment']):
                roles[ing] = "seasoning"
                remaining.remove(ing)
                seasoning_count += 1
                if seasoning_count >= 2:  # Limit seasonings
                    break

    # Remaining ingredients are complements
    for ing in remaining:
        roles[ing] = "complement"

    return roles


def _generate_single_variant(anchor_name: str, anchor_row: pd.Series,
                           candidate_pool: pd.DataFrame, template: str,
                           template_category: str, segment: Dict[str, Any],
                           min_ing: int, max_ing: int, matches_df: pd.DataFrame,
                           style: str, variant_index: int) -> RecipeVariant:
    """Generate a single recipe variant with specific style"""

    # Determine target ingredient count
    target_count = random.randint(min_ing, min(max_ing, min_ing + 4))
    needed_ingredients = target_count - 1  # Excluding anchor

    # Style-specific selection strategy
    if style == "fresco":
        # Prioritize acidic and fresh ingredients
        style_candidates = candidate_pool[
            candidate_pool['tags'].apply(
                lambda tags: any(tag in tags for tag in ['Acid', 'Citrus', 'Herbs', 'Vegetables'])
                if isinstance(tags, list) else False
            )
        ]
        if len(style_candidates) < needed_ingredients // 2:
            style_candidates = candidate_pool
    elif style == "umami":
        # Prioritize umami and fat sources
        style_candidates = candidate_pool[
            candidate_pool['tags'].apply(
                lambda tags: any(tag in tags for tag in ['Cheese', 'Meat', 'Mushroom', 'Tomato', 'Fat'])
                if isinstance(tags, list) else False
            )
        ]
        if len(style_candidates) < needed_ingredients // 2:
            style_candidates = candidate_pool
    else:  # classico
        style_candidates = candidate_pool

    # Select ingredients with some randomness to avoid identical variants
    selected_ingredients = [anchor_name]

    # Take top candidates but add some variety for different variants
    start_idx = variant_index * 2  # Offset for variety
    available_candidates = style_candidates.iloc[start_idx:start_idx + needed_ingredients * 3]

    if len(available_candidates) < needed_ingredients:
        available_candidates = candidate_pool.head(needed_ingredients * 2)

    # Select with weighted randomness
    weights = available_candidates['total_score'].tolist()
    if weights:
        selected_names = available_candidates['name'].tolist()
        for _ in range(min(needed_ingredients, len(selected_names))):
            if not selected_names:
                break

            # Weighted selection
            total_weight = sum(weights)
            if total_weight <= 0:
                chosen_idx = 0
            else:
                rand_val = random.random() * total_weight
                chosen_idx = 0
                cumsum = 0
                for i, w in enumerate(weights):
                    cumsum += w
                    if rand_val <= cumsum:
                        chosen_idx = i
                        break

            chosen_name = selected_names.pop(chosen_idx)
            weights.pop(chosen_idx)
            selected_ingredients.append(chosen_name)

    # Calculate flavor profile
    flavor_profile = _calculate_flavor_profile(selected_ingredients, candidate_pool.append(pd.Series(anchor_row)).reset_index(drop=True))

    # Calculate compatibility metrics
    compatibility_avg = score_combo(selected_ingredients, matches_df)
    triangles = _count_triangles(selected_ingredients, matches_df)

    # Assign roles
    roles = role_assignment(template, anchor_name, selected_ingredients[1:],
                          pd.concat([candidate_pool, pd.DataFrame([anchor_row])]))

    # Generate notes
    notes = f"Variante {style}: {len(selected_ingredients)} ingredienti, "
    notes += f"compatibilità media {compatibility_avg:.1f}, {triangles} triangoli"

    return RecipeVariant(
        ingredients=selected_ingredients,
        roles=roles,
        tiers={},  # Will be filled by pricing module
        flavor_profile=flavor_profile,
        compatibility_avg=compatibility_avg,
        triangles=triangles,
        notes=notes,
        style=style
    )


def _get_template_category(template: str) -> str:
    """Get template category for ingredient range rules"""
    from templates_catalog import TEMPLATES_CATALOG
    if template in TEMPLATES_CATALOG:
        return TEMPLATES_CATALOG[template].category
    return "Unknown"


def _get_ingredient_range(category: str) -> Tuple[int, int]:
    """Get ingredient count range for template category"""
    ranges = {
        "Pasta & Riso": (6, 12),
        "Carne": (5, 10),
        "Pesce": (5, 10),
        "Vegetariano": (4, 8),
        "Dessert": (5, 9),
        "Burger": (4, 7)
    }
    return ranges.get(category, (5, 8))


def _calculate_flavor_profile(ingredients: List[str], ingredients_df: pd.DataFrame) -> Dict[str, int]:
    """Calculate combined flavor profile for ingredient list"""
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


def _count_triangles(ingredients: List[str], matches_df: pd.DataFrame) -> int:
    """Count strong triangular relationships (all 3 pairs have MatchValue >= 2)"""
    if len(ingredients) < 3:
        return 0

    triangles = 0

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

    return triangles