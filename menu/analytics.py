"""
Menu Analytics for Chef Planner MVP 0.3
Advanced menu analysis, KPIs, variety warnings, and unlock recommendations.
"""

from typing import List, Dict, Any, Tuple, Set
import statistics
from collections import Counter, defaultdict


def menu_kpis(menu_items: List[Dict[str, Any]], segment: Dict[str, Any],
              sections_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive menu KPIs
    Returns dict with all key performance indicators
    """
    if not menu_items:
        return {
            'n_items': 0,
            'avg_stars': 0.0,
            'median_price': 0.0,
            'avg_price_deviation_pct': 0.0,
            'avg_fit_total': 0.0,
            'avg_fit_price': 0.0,
            'avg_fit_tags': 0.0,
            'avg_fit_eval': 0.0,
            'section_coverage': {},
            'tag_coverage': {},
            'complexity_stats': {'min': 0, 'avg': 0.0, 'max': 0},
            'cost_vs_target': {'avg_deviation': 0.0, 'distribution': {}}
        }

    n_items = len(menu_items)

    # Basic aggregations
    stars = [item.get('stars', 0.0) for item in menu_items]
    prices = [item.get('price', 0.0) for item in menu_items]
    fits = [item.get('segment_fit', 0.0) for item in menu_items]
    ingredient_counts = [len(item.get('ingredients', [])) for item in menu_items]

    avg_stars = statistics.mean(stars) if stars else 0.0
    median_price = statistics.median(prices) if prices else 0.0
    avg_fit_total = statistics.mean(fits) if fits else 0.0

    # Price deviation analysis
    price_deviations = []
    cost_deviations = []

    for item in menu_items:
        section = item.get('section', 'MainCourse')
        section_info = sections_meta.get(section, {})
        expected_cost = section_info.get('cost_expectation', 10.0)

        actual_price = item.get('price', 0.0)
        actual_cost = item.get('cost', 0.0)

        if expected_cost > 0:
            price_dev_pct = abs(actual_price - expected_cost) / expected_cost * 100
            cost_dev_pct = abs(actual_cost - expected_cost) / expected_cost * 100
            price_deviations.append(price_dev_pct)
            cost_deviations.append(cost_dev_pct)

    avg_price_deviation_pct = statistics.mean(price_deviations) if price_deviations else 0.0

    # Section coverage analysis
    section_counts = Counter(item.get('section', 'MainCourse') for item in menu_items)
    section_coverage = {}

    for section, count in section_counts.items():
        section_info = sections_meta.get(section, {})
        probability = section_info.get('probability', 0.5)
        expected_ratio = probability
        actual_ratio = count / n_items if n_items > 0 else 0

        section_coverage[section] = {
            'count': count,
            'actual_ratio': actual_ratio,
            'expected_ratio': expected_ratio,
            'deviation': abs(actual_ratio - expected_ratio)
        }

    # Tag coverage analysis
    all_tags = set()
    for item in menu_items:
        item_tags = item.get('tag_set', set())
        if isinstance(item_tags, list):
            all_tags.update(item_tags)
        elif isinstance(item_tags, set):
            all_tags.update(item_tags)

    favourite_tags = set(segment.get('favourite_tags', []))
    secondary_tags = set(segment.get('secondary_favourite_tags', []))
    expected_tags = set(segment.get('expectations', {}).keys())

    tag_coverage = {
        'total_unique_tags': len(all_tags),
        'favourite_coverage': len(all_tags.intersection(favourite_tags)),
        'favourite_total': len(favourite_tags),
        'secondary_coverage': len(all_tags.intersection(secondary_tags)),
        'secondary_total': len(secondary_tags),
        'expected_coverage': len(all_tags.intersection(expected_tags)),
        'expected_total': len(expected_tags),
        'favourite_coverage_pct': (len(all_tags.intersection(favourite_tags)) / len(favourite_tags) * 100) if favourite_tags else 100.0,
        'missing_favourites': list(favourite_tags - all_tags),
        'missing_expected': list(expected_tags - all_tags)
    }

    # Complexity statistics
    complexity_stats = {
        'min': min(ingredient_counts) if ingredient_counts else 0,
        'avg': statistics.mean(ingredient_counts) if ingredient_counts else 0.0,
        'max': max(ingredient_counts) if ingredient_counts else 0
    }

    # Cost vs target distribution
    cost_vs_target = {
        'avg_deviation': statistics.mean(cost_deviations) if cost_deviations else 0.0,
        'distribution': {
            'under_target': len([d for d in cost_deviations if d < -5]),
            'on_target': len([d for d in cost_deviations if -5 <= d <= 15]),
            'over_target': len([d for d in cost_deviations if d > 15])
        } if cost_deviations else {'under_target': 0, 'on_target': 0, 'over_target': 0}
    }

    # Fit breakdown (if available)
    fit_breakdowns = [item.get('fit_breakdown', {}) for item in menu_items if item.get('fit_breakdown')]

    if fit_breakdowns:
        avg_fit_price = statistics.mean([fb.get('price_fit', 0) for fb in fit_breakdowns])
        avg_fit_tags = statistics.mean([fb.get('tag_fit', 0) for fb in fit_breakdowns])
        avg_fit_eval = statistics.mean([fb.get('eval_fit', 0) for fb in fit_breakdowns])
    else:
        avg_fit_price = avg_fit_tags = avg_fit_eval = 0.0

    return {
        'n_items': n_items,
        'avg_stars': round(avg_stars, 2),
        'median_price': round(median_price, 2),
        'avg_price_deviation_pct': round(avg_price_deviation_pct, 1),
        'avg_fit_total': round(avg_fit_total, 1),
        'avg_fit_price': round(avg_fit_price, 1),
        'avg_fit_tags': round(avg_fit_tags, 1),
        'avg_fit_eval': round(avg_fit_eval, 1),
        'section_coverage': section_coverage,
        'tag_coverage': tag_coverage,
        'complexity_stats': complexity_stats,
        'cost_vs_target': cost_vs_target
    }


def variety_warnings(menu_items: List[Dict[str, Any]], segment: Dict[str, Any]) -> List[str]:
    """
    Generate variety and coherence warnings for the menu
    """
    warnings = []

    if not menu_items:
        return ["Menu vuoto - aggiungi delle ricette per vedere l'analisi"]

    n_items = len(menu_items)

    # Section imbalance warnings
    section_counts = Counter(item.get('section', 'MainCourse') for item in menu_items)

    # Check for section over-representation
    for section, count in section_counts.items():
        ratio = count / n_items
        if ratio > 0.6 and count > 3:  # More than 60% in one section with 3+ items
            warnings.append(f"⚠️ Troppi piatti nella sezione '{section}' ({count}/{n_items}, {ratio:.1%})")

    # Check for missing important sections based on segment probability
    segment_sections = segment.get('sections', {})
    for section, section_info in segment_sections.items():
        probability = section_info.get('probability', 0.0)
        if probability > 0.3 and section not in section_counts:
            warnings.append(f"🔍 Sezione '{section}' mancante (probabilità {probability:.1%} per questo segmento)")

    # Template + anchor redundancy
    template_anchor_combos = []
    for item in menu_items:
        template = item.get('template', '')
        anchor = item.get('anchor', '')
        ingredients = item.get('ingredients', [])
        anchor_tags = set()

        # Extract tags for the anchor ingredient (simplified approach)
        # In a real implementation, you'd look up the ingredient data
        if anchor:
            template_anchor_combos.append((template, anchor))

    combo_counts = Counter(template_anchor_combos)
    for (template, anchor), count in combo_counts.items():
        if count >= 3:
            warnings.append(f"🔄 Ridondanza: {count} piatti simili con template '{template}' e ingrediente '{anchor}'")

    # Tag imbalance analysis
    favourite_tags = set(segment.get('favourite_tags', []))
    secondary_tags = set(segment.get('secondary_favourite_tags', []))

    # Count tag occurrences across menu
    tag_counter = Counter()
    for item in menu_items:
        item_tags = item.get('tag_set', [])
        if isinstance(item_tags, (list, set)):
            tag_counter.update(item_tags)

    # Check for missing favourite tags
    all_menu_tags = set(tag_counter.keys())
    missing_favourites = favourite_tags - all_menu_tags
    if missing_favourites and len(missing_favourites) > len(favourite_tags) * 0.5:
        missing_list = ', '.join(list(missing_favourites)[:3])
        warnings.append(f"📋 Tag preferiti mancanti: {missing_list}")

    # Check for tag over-concentration
    for tag, count in tag_counter.items():
        if count / n_items > 0.6 and count > 2:  # More than 60% of dishes have this tag
            warnings.append(f"⚡ Eccesso tag '{tag}': presente in {count}/{n_items} piatti ({count/n_items:.1%})")

    # Price coherence analysis
    incoherent_prices = 0
    for item in menu_items:
        section = item.get('section', 'MainCourse')
        section_info = segment_sections.get(section, {})
        expected_cost = section_info.get('cost_expectation', 10.0)
        actual_price = item.get('price', 0.0)

        if expected_cost > 0:
            deviation_pct = abs(actual_price - expected_cost) / expected_cost * 100
            if deviation_pct > 20:  # More than 20% deviation
                incoherent_prices += 1

    if incoherent_prices / n_items > 0.3:  # More than 30% of dishes
        warnings.append(f"💰 Prezzi incoerenti: {incoherent_prices}/{n_items} piatti fuori target (>±20%)")

    # Complexity mismatch analysis
    ingredient_counts = [len(item.get('ingredients', [])) for item in menu_items]
    if ingredient_counts:
        avg_complexity = statistics.mean(ingredient_counts)

        # Determine expected complexity range based on segment
        segment_name = segment.get('name', '').lower()
        if 'gourmet' in segment_name or 'premium' in segment_name:
            expected_range = (6, 10)
        elif 'family' in segment_name or 'casual' in segment_name:
            expected_range = (4, 8)
        else:
            expected_range = (5, 8)

        if avg_complexity < expected_range[0] - 1:
            warnings.append(f"🔧 Menu troppo semplice per il segmento (media {avg_complexity:.1f} ingredienti)")
        elif avg_complexity > expected_range[1] + 1:
            warnings.append(f"🎯 Menu troppo complesso per il segmento (media {avg_complexity:.1f} ingredienti)")

    return warnings


def unlock_recommendations(menu_items: List[Dict[str, Any]], segment: Dict[str, Any],
                          templates_catalog: Dict[str, Any], unlocked_set: Set[str],
                          points_budget: int) -> List[Dict[str, Any]]:
    """
    Generate smart template unlock recommendations to improve the menu
    """
    recommendations = []

    if not menu_items:
        # No menu yet - recommend basic templates
        basic_recommendations = [
            {'template': 'Pasta', 'points': 0, 'reason': 'Template universale per iniziare'},
            {'template': 'Grilled Meat', 'points': 0, 'reason': 'Piatto principale classico'},
            {'template': 'Salad', 'points': 0, 'reason': 'Opzione leggera essenziale'}
        ]
        return [r for r in basic_recommendations if r['template'] not in unlocked_set]

    # Analyze current menu gaps
    section_counts = Counter(item.get('section', 'MainCourse') for item in menu_items)
    segment_sections = segment.get('sections', {})

    # Find under-represented sections
    under_represented = []
    for section, section_info in segment_sections.items():
        probability = section_info.get('probability', 0.0)
        current_count = section_counts.get(section, 0)
        expected_count = probability * len(menu_items)

        if probability > 0.2 and current_count < expected_count * 0.5:
            under_represented.append((section, probability))

    # Template mapping to likely sections (simplified)
    template_to_sections = {
        'Salad': ['Appetizer', 'SideDish'],
        'Vegetable Soup': ['Soup', 'Appetizer'],
        'Grilled Fish': ['MainCourse'],
        'Roasted Fish': ['MainCourse'],
        'Grilled Meat': ['MainCourse'],
        'Roasted Meat': ['MainCourse'],
        'Pasta': ['MainCourse'],
        'Risotto': ['MainCourse'],
        'Ice Cream': ['Dessert'],
        'Cookies': ['Dessert'],
        'Cheesecake': ['Dessert']
    }

    # Recommend templates for under-represented sections
    for section, probability in under_represented[:2]:  # Max 2 section recommendations
        suitable_templates = []
        for template, sections in template_to_sections.items():
            if section in sections and template not in unlocked_set:
                template_info = templates_catalog.get(template)
                if template_info and template_info.points <= points_budget:
                    suitable_templates.append((template, template_info.points))

        # Pick cheapest suitable template
        if suitable_templates:
            suitable_templates.sort(key=lambda x: x[1])
            template, points = suitable_templates[0]
            reason = f"Migliora copertura sezione '{section}' (probabilità {probability:.1%})"
            recommendations.append({'template': template, 'points': points, 'reason': reason})

    # Find missing favourite tags
    favourite_tags = set(segment.get('favourite_tags', []))
    menu_tags = set()
    for item in menu_items:
        item_tags = item.get('tag_set', [])
        if isinstance(item_tags, (list, set)):
            menu_tags.update(item_tags)

    missing_favourites = favourite_tags - menu_tags

    # Simplified tag to template mapping
    tag_to_templates = {
        'Seafood': ['Grilled Fish', 'Fish Soup', 'Fish Tartare'],
        'Meat': ['Grilled Meat', 'Meatballs', 'Meat Stew'],
        'Cheese': ['Cheesecake', 'Lasagne'],
        'Wine': ['Risotto', 'Braised Meat'],
        'Vegetables': ['Salad', 'Vegetable Soup', 'Grilled Veggies']
    }

    for missing_tag in list(missing_favourites)[:2]:  # Max 2 tag recommendations
        if missing_tag in tag_to_templates:
            suitable_templates = []
            for template in tag_to_templates[missing_tag]:
                if template not in unlocked_set and template in templates_catalog:
                    template_info = templates_catalog[template]
                    if template_info.points <= points_budget:
                        suitable_templates.append((template, template_info.points))

            if suitable_templates:
                suitable_templates.sort(key=lambda x: x[1])
                template, points = suitable_templates[0]
                reason = f"Copre tag preferito '{missing_tag}' mancante"
                recommendations.append({'template': template, 'points': points, 'reason': reason})

    # Recommend signature dishes if budget allows
    if points_budget >= 15:
        signature_templates = [name for name, tmpl in templates_catalog.items()
                              if tmpl.points == 15 and name not in unlocked_set]

        if signature_templates:
            # Pick one based on segment preference
            segment_name = segment.get('name', '').lower()
            preferred = None

            if 'gourmet' in segment_name:
                for template in ['Risotto', 'Fish Tartare', 'Millefeuille']:
                    if template in signature_templates:
                        preferred = template
                        break
            elif 'meat' in segment_name or 'family' in segment_name:
                for template in ['Stuffed Meat', 'Braised Meat']:
                    if template in signature_templates:
                        preferred = template
                        break

            if preferred:
                reason = f"Piatto signature (15 pts) adatto al segmento {segment.get('name', '')}"
                recommendations.append({'template': preferred, 'points': 15, 'reason': reason})
            elif signature_templates:
                # Fallback to first available signature dish
                template = signature_templates[0]
                reason = "Piatto signature (15 pts) per distinguere il menu"
                recommendations.append({'template': template, 'points': 15, 'reason': reason})

    # Sort by points (cheapest first) and limit to 5
    recommendations.sort(key=lambda x: x['points'])
    return recommendations[:5]


def menu_health_score(kpis: Dict[str, Any], warnings_count: int) -> int:
    """
    Calculate overall menu health score (0-100)
    """
    if kpis['n_items'] == 0:
        return 0

    # Base score components
    stars_score = (kpis['avg_stars'] / 5.0) * 30  # Max 30 points
    fit_score = (kpis['avg_fit_total'] / 100.0) * 25  # Max 25 points

    # Price coherence score (inverted deviation)
    price_coherence = max(0, 20 - kpis['avg_price_deviation_pct'] * 0.5)  # Max 20 points
    price_coherence = min(20, price_coherence)

    # Section balance score
    section_balance = 15  # Start with max
    for section_info in kpis['section_coverage'].values():
        deviation = section_info['deviation']
        if deviation > 0.3:  # 30% deviation penalty
            section_balance -= 5
    section_balance = max(0, section_balance)

    # Tag coverage score
    tag_coverage_pct = kpis['tag_coverage'].get('favourite_coverage_pct', 0)
    tag_score = (tag_coverage_pct / 100.0) * 10  # Max 10 points

    # Warning penalty
    warning_penalty = min(warnings_count * 3, 20)  # Max 20 point penalty

    # Calculate final score
    total_score = stars_score + fit_score + price_coherence + section_balance + tag_score - warning_penalty

    return max(0, min(100, int(total_score)))


def get_menu_variety_stats(menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get detailed variety statistics for the menu
    """
    if not menu_items:
        return {'templates': {}, 'sections': {}, 'styles': {}, 'unique_ingredients': 0}

    template_counts = Counter(item.get('template', 'Unknown') for item in menu_items)
    section_counts = Counter(item.get('section', 'Unknown') for item in menu_items)
    style_counts = Counter(item.get('style', 'classico') for item in menu_items)

    # Count unique ingredients
    all_ingredients = set()
    for item in menu_items:
        ingredients = item.get('ingredients', [])
        all_ingredients.update(ingredients)

    return {
        'templates': dict(template_counts),
        'sections': dict(section_counts),
        'styles': dict(style_counts),
        'unique_ingredients': len(all_ingredients)
    }