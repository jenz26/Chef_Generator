"""
Template Catalog for Chef Planner
Contains the 45 recipe templates with categories, point costs, and compatibility rules.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class Template:
    """Represents a recipe template"""
    name: str
    category: str
    points: int
    locked: bool = True

    def __str__(self):
        return f"{self.name} ({self.points} pts)"

# Template catalog with all 45 templates
TEMPLATES_CATALOG = {
    # Pasta & Riso (9)
    "Pasta": Template("Pasta", "Pasta & Riso", 0),
    "Gnocchi": Template("Gnocchi", "Pasta & Riso", 15),
    "Lasagne": Template("Lasagne", "Pasta & Riso", 5),
    "Stuffed Pasta": Template("Stuffed Pasta", "Pasta & Riso", 15),
    "Sautéed Rice": Template("Sautéed Rice", "Pasta & Riso", 0),
    "Risotto": Template("Risotto", "Pasta & Riso", 15),
    "Paella": Template("Paella", "Pasta & Riso", 15),
    "Rice Pie": Template("Rice Pie", "Pasta & Riso", 5),

    # Carne (9)
    "Grilled Meat": Template("Grilled Meat", "Carne", 0),
    "Meat Stew": Template("Meat Stew", "Carne", 0),
    "Roasted Meat": Template("Roasted Meat", "Carne", 5),
    "Boiled Meat": Template("Boiled Meat", "Carne", 5),
    "Stuffed Meat": Template("Stuffed Meat", "Carne", 15),
    "Meatballs": Template("Meatballs", "Carne", 5),
    "Braised Meat": Template("Braised Meat", "Carne", 15),
    "Meat Tartare": Template("Meat Tartare", "Carne", 15),
    "Fried Meat": Template("Fried Meat", "Carne", 15),

    # Pesce (6)
    "Grilled Fish": Template("Grilled Fish", "Pesce", 0),
    "Steamed Fish": Template("Steamed Fish", "Pesce", 0),
    "Roasted Fish": Template("Roasted Fish", "Pesce", 5),
    "Fish Soup": Template("Fish Soup", "Pesce", 5),
    "Fish Tartare": Template("Fish Tartare", "Pesce", 15),
    "Fried Fish": Template("Fried Fish", "Pesce", 15),

    # Vegetariano (8)
    "Sautéed Veggies": Template("Sautéed Veggies", "Vegetariano", 0),
    "Salad": Template("Salad", "Vegetariano", 0),
    "Grilled Veggies": Template("Grilled Veggies", "Vegetariano", 0),
    "Steamed Veggies": Template("Steamed Veggies", "Vegetariano", 5),
    "Roasted Veggies": Template("Roasted Veggies", "Vegetariano", 5),
    "Vegetable Soup": Template("Vegetable Soup", "Vegetariano", 5),
    "Velvety": Template("Velvety", "Vegetariano", 15),
    "Fried Veggies": Template("Fried Veggies", "Vegetariano", 15),

    # Dessert (9)
    "Pie": Template("Pie", "Dessert", 0),
    "Cookies": Template("Cookies", "Dessert", 0),
    "Semifreddo": Template("Semifreddo", "Dessert", 5),
    "Pastries": Template("Pastries", "Dessert", 5),
    "Cheesecake": Template("Cheesecake", "Dessert", 5),
    "Ice Cream": Template("Ice Cream", "Dessert", 15),
    "Fried Dessert": Template("Fried Dessert", "Dessert", 15),
    "Millefeuille": Template("Millefeuille", "Dessert", 15),

    # Burger (3)
    "Hamburger": Template("Hamburger", "Burger", 0),
    "Fish Burger": Template("Fish Burger", "Burger", 0),
    "Veggie Burger": Template("Veggie Burger", "Burger", 0),
}

def get_all_templates() -> Dict[str, Template]:
    """Get all templates as a dictionary"""
    return TEMPLATES_CATALOG.copy()

def get_templates_by_category() -> Dict[str, List[Template]]:
    """Group templates by category"""
    categories = {}
    for template in TEMPLATES_CATALOG.values():
        if template.category not in categories:
            categories[template.category] = []
        categories[template.category].append(template)

    # Sort templates within each category by points then name
    for category in categories:
        categories[category].sort(key=lambda t: (t.points, t.name))

    return categories

def get_unlocked_templates(available_points: int, unlocked_templates: List[str]) -> List[str]:
    """Get list of templates that can be unlocked with current points and already unlocked templates"""
    unlocked = set(unlocked_templates)

    for name, template in TEMPLATES_CATALOG.items():
        if name not in unlocked and template.points <= available_points:
            unlocked.add(name)

    return list(unlocked)

def get_unlock_suggestions(segment_name: str, section: str) -> Dict[str, str]:
    """Get template unlock suggestions for a specific segment and section (stub implementation)"""
    suggestions = {
        # Basic suggestions based on section
        "Appetizer": {
            "Salad": "Perfect fresh starter for any segment",
            "Grilled Veggies": "Light and healthy option",
            "Stuffed Pasta": "Premium appetizer for upscale segments",
        },
        "MainCourse": {
            "Pasta": "Universal crowd-pleaser",
            "Grilled Meat": "Classic main course",
            "Grilled Fish": "Healthy protein option",
            "Risotto": "Premium comfort food",
            "Paella": "Show-stopping signature dish",
        },
        "SideDish": {
            "Sautéed Veggies": "Essential healthy side",
            "Roasted Veggies": "Elevated vegetable preparation",
        },
        "Soup": {
            "Vegetable Soup": "Comforting starter",
            "Fish Soup": "Premium seafood option",
        },
        "Salad": {
            "Salad": "Essential fresh option",
        },
        "Dessert": {
            "Cookies": "Simple crowd-pleaser",
            "Ice Cream": "Premium frozen dessert",
            "Millefeuille": "Signature pastry for gourmet segments",
        }
    }

    return suggestions.get(section, {})

def check_template_compatibility(template_name: str, anchor_ingredient: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if an anchor ingredient is compatible with a template
    Returns (is_compatible, message)
    """
    if not anchor_ingredient:
        return False, "No anchor ingredient selected"

    anchor_tags = anchor_ingredient.get('tags', [])
    if isinstance(anchor_tags, str):
        anchor_tags = [tag.strip() for tag in anchor_tags.split(',')]

    template_name_lower = template_name.lower()

    # Fish templates require Seafood tag
    if 'fish' in template_name_lower:
        if 'Seafood' not in anchor_tags:
            return False, f"❌ {template_name} requires an ingredient with 'Seafood' tag"

    # Meat templates require Meat tag
    if any(meat_word in template_name_lower for meat_word in ['meat', 'meatballs']):
        if 'Meat' not in anchor_tags:
            return False, f"❌ {template_name} requires an ingredient with 'Meat' tag"

    # Vegetarian templates forbid Meat and Seafood
    if any(veggie_word in template_name_lower for veggie_word in ['veggies', 'vegetable', 'salad', 'velvety']):
        if 'Meat' in anchor_tags or 'Seafood' in anchor_tags:
            return False, f"❌ {template_name} (vegetarian) cannot use Meat or Seafood ingredients"

    # Veggie Burger forbids Meat and Seafood
    if template_name == 'Veggie Burger':
        if 'Meat' in anchor_tags or 'Seafood' in anchor_tags:
            return False, f"❌ Veggie Burger cannot use Meat or Seafood ingredients"

    # Pasta/Rice templates should have pasta or rice base (warning only)
    if any(carb_word in template_name_lower for carb_word in ['pasta', 'rice', 'risotto', 'paella', 'gnocchi', 'lasagne']):
        if not any(carb_tag in anchor_tags for carb_tag in ['Pasta', 'Rice', 'Carbs']):
            return True, f"⚠️ {template_name} usually needs a pasta/rice base ingredient"

    # Dessert templates forbid Seafood/Meat on anchor
    if template_name in ['Pie', 'Cookies', 'Semifreddo', 'Pastries', 'Cheesecake', 'Ice Cream', 'Fried Dessert', 'Millefeuille']:
        if 'Seafood' in anchor_tags or 'Meat' in anchor_tags:
            return False, f"❌ {template_name} (dessert) cannot use Meat or Seafood as main ingredient"

    return True, f"✅ {template_name} is compatible with this ingredient"

def get_template_description(template_name: str) -> str:
    """Get a description for a template"""
    descriptions = {
        "Pasta": "Classic pasta dishes with sauce and toppings",
        "Gnocchi": "Soft potato dumplings with rich sauces",
        "Lasagne": "Layered pasta with meat, cheese and sauce",
        "Stuffed Pasta": "Ravioli, tortellini and filled pasta",
        "Sautéed Rice": "Quick-cooked rice with vegetables and proteins",
        "Risotto": "Creamy Italian rice dish",
        "Paella": "Spanish rice dish with seafood or meat",
        "Rice Pie": "Baked rice dish with filling",

        "Grilled Meat": "Flame-grilled meat with seasonings",
        "Meat Stew": "Slow-cooked tender meat in sauce",
        "Roasted Meat": "Oven-roasted meat with herbs",
        "Boiled Meat": "Tender boiled meat preparations",
        "Stuffed Meat": "Meat rolls with filling",
        "Meatballs": "Seasoned ground meat balls",
        "Braised Meat": "Slow-braised meat in liquid",
        "Meat Tartare": "Raw seasoned meat delicacy",
        "Fried Meat": "Crispy fried meat preparations",

        "Grilled Fish": "Flame-grilled fish with herbs",
        "Steamed Fish": "Delicate steamed fish preparations",
        "Roasted Fish": "Oven-baked fish with vegetables",
        "Fish Soup": "Rich fish broth with seafood",
        "Fish Tartare": "Raw seasoned fish delicacy",
        "Fried Fish": "Crispy fried fish preparations",

        "Sautéed Veggies": "Pan-fried vegetables with seasonings",
        "Salad": "Fresh mixed vegetables and greens",
        "Grilled Veggies": "Flame-grilled vegetable medley",
        "Steamed Veggies": "Healthy steamed vegetable dishes",
        "Roasted Veggies": "Oven-roasted vegetable combinations",
        "Vegetable Soup": "Hearty vegetable broth",
        "Velvety": "Smooth cream-based vegetable soups",
        "Fried Veggies": "Crispy fried vegetable preparations",

        "Pie": "Sweet or savory baked pies",
        "Cookies": "Sweet baked cookie varieties",
        "Semifreddo": "Semi-frozen Italian dessert",
        "Pastries": "Delicate baked pastry items",
        "Cheesecake": "Rich cream cheese dessert",
        "Ice Cream": "Frozen dessert with mix-ins",
        "Fried Dessert": "Crispy fried sweet treats",
        "Millefeuille": "Layered puff pastry dessert",

        "Hamburger": "Classic beef burger with toppings",
        "Fish Burger": "Seafood burger with sauce",
        "Veggie Burger": "Plant-based burger patty",
    }

    return descriptions.get(template_name, "Recipe template")


# Template rules for MVP 0.2
TEMPLATE_RULES = {
    # Ingredient count ranges per category
    "ingredient_ranges": {
        "Pasta & Riso": (6, 12),
        "Carne": (5, 10),
        "Pesce": (5, 10),
        "Vegetariano": (4, 8),
        "Dessert": (5, 9),
        "Burger": (4, 7)
    },

    # Compatibility rules
    "compatibility_rules": {
        # Fish templates require Seafood tag
        "fish_templates": [
            "Grilled Fish", "Steamed Fish", "Roasted Fish",
            "Fish Soup", "Fish Tartare", "Fried Fish", "Fish Burger"
        ],
        "fish_required_tags": ["Seafood"],

        # Meat templates require Meat tag
        "meat_templates": [
            "Grilled Meat", "Meat Stew", "Roasted Meat", "Boiled Meat",
            "Stuffed Meat", "Meatballs", "Braised Meat", "Meat Tartare",
            "Fried Meat", "Hamburger"
        ],
        "meat_required_tags": ["Meat"],

        # Vegetarian templates forbid Meat and Seafood
        "vegetarian_templates": [
            "Sautéed Veggies", "Salad", "Grilled Veggies", "Steamed Veggies",
            "Roasted Veggies", "Vegetable Soup", "Velvety", "Fried Veggies",
            "Veggie Burger"
        ],
        "vegetarian_forbidden_tags": ["Meat", "Seafood"],

        # Dessert templates forbid Meat/Seafood as main ingredient
        "dessert_templates": [
            "Pie", "Cookies", "Semifreddo", "Pastries", "Cheesecake",
            "Ice Cream", "Fried Dessert", "Millefeuille"
        ],
        "dessert_forbidden_main_tags": ["Meat", "Seafood"],

        # Pasta/Rice templates should have carb base (warning only)
        "carb_templates": [
            "Pasta", "Gnocchi", "Lasagne", "Stuffed Pasta",
            "Sautéed Rice", "Risotto", "Paella", "Rice Pie"
        ],
        "carb_preferred_tags": ["Pasta", "Rice", "Carbs"]
    }
}


def get_template_rules() -> Dict[str, Any]:
    """Get template rules for MVP 0.2 logic"""
    return TEMPLATE_RULES.copy()


def get_ingredient_range_for_category(category: str) -> Tuple[int, int]:
    """Get ingredient count range for a template category"""
    return TEMPLATE_RULES["ingredient_ranges"].get(category, (5, 8))


def get_template_compatibility_type(template_name: str) -> str:
    """
    Get compatibility type for a template
    Returns: 'fish', 'meat', 'vegetarian', 'dessert', 'carb', or 'neutral'
    """
    rules = TEMPLATE_RULES["compatibility_rules"]

    if template_name in rules["fish_templates"]:
        return 'fish'
    elif template_name in rules["meat_templates"]:
        return 'meat'
    elif template_name in rules["vegetarian_templates"]:
        return 'vegetarian'
    elif template_name in rules["dessert_templates"]:
        return 'dessert'
    elif template_name in rules["carb_templates"]:
        return 'carb'
    else:
        return 'neutral'