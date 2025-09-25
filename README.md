# 👨‍🍳 Chef Planner MVP 0.3.1

A Streamlit web application for planning recipes and optimizing menus based on customer segments, template unlocks, and ingredient compatibility - built specifically for *Chef: A Restaurant Tycoon Game*.

## 🎯 Current Features (MVP 0.3.1 - UI Refactor)

### 🆕 **Quick Start Wizard** *(NEW in 0.3.1)*
- **4-step guided workflow**: Clientela → Sezione → Template → Ingrediente
- **Visual customer cards**: Easy segment selection with preferences and focus display
- **Smart template suggestions**: Shows compatible templates for selected section
- **Ingredient compatibility**: Real-time compatibility checking with visual indicators
- **Auto-recipe generation**: Generates 3 recipe variants at the final step

### 🆕 **Recipe Studio** *(NEW in 0.3.1)*
- **2-column layout**: Configuration on left, preview on right
- **Advanced controls**: Full control over customer, section, template, and ingredient
- **Real-time validation**: Template-ingredient compatibility warnings
- **Multiple variants**: Generate and compare Classico, Fresco, and Umami styles
- **One-click addition**: Add any variant directly to your menu

### 🆕 **Simplified Menu Builder** *(NEW in 0.3.1)*
- **Essential KPIs**: Menu health, rating, fit, and coherence in clear metrics
- **Quick management**: Simple recipe list with expand/collapse details
- **Three export formats**: CSV for Excel, JSON for technical use, comprehensive reports
- **Smart recommendations**: Top 3 warnings and improvement suggestions

### 🆕 **Expert Mode** *(NEW in 0.3.1)*
- **All advanced features**: Complete access to original MVP 0.3 functionality
- **Three sub-tabs**: Advanced Configuration, Deep Analytics, Ingredient Database
- **Power user interface**: For users who need full control and detailed analysis

## 🎯 Established Features (MVP 0.3)

### 🆕 **Advanced Menu Builder** *(NEW in 0.3)*
- **Complete menu management**: Edit, duplicate, delete recipes with one click
- **Advanced KPI dashboard**: Menu health score, rating trends, price coherence
- **Section coverage analysis**: Visual charts comparing actual vs expected distribution
- **Recipe management table**: Sortable view with all recipe details and actions

### 🆕 **Menu Intelligence & Analytics** *(NEW in 0.3)*
- **Variety warnings**: Smart detection of redundancies, gaps, and imbalances
- **Menu health scoring**: 0-100 composite score based on quality, fit, and coherence
- **Complexity analysis**: Ingredient count statistics and segment appropriateness
- **Tag coverage tracking**: Monitor favorite/expected tag representation

### 🆕 **Smart Unlock Recommendations** *(NEW in 0.3)*
- **Context-aware suggestions**: Templates recommended based on current menu gaps
- **Budget-conscious advice**: Recommendations within available point budget
- **Segment-specific priorities**: Suggestions tailored to customer segment preferences
- **Strategic guidance**: Signature dishes and section coverage improvements

### 🆕 **Professional Export System** *(NEW in 0.3)*
- **CSV export**: Structured data for spreadsheet analysis
- **JSON export**: Complete recipe data for integration and backup
- **Comprehensive reports**: Executive summaries with KPIs, warnings, and recommendations
- **Timestamped outputs**: All exports include generation metadata

## 🎯 Established Features (MVP 0.2)

### 🆕 **Recipe Variant Generation** *(NEW in 0.2)*
- **Auto-generate 2-3 recipe variants** from customer segment, section, template, and anchor ingredient
- **Smart ingredient selection** based on compatibility scores and segment preferences
- **3 distinct styles**: Classico, Fresco, Umami with different ingredient focus
- **Role-based ingredient assignment**: Hero, Base, Complement, Seasoning, Fat, Cheese

### 🆕 **Target-Based Pricing System** *(NEW in 0.2)*
- **Automatic tier selection** (Normal/First Choice/Gourmet) to match cost expectations
- **Strategic pricing** prioritizing hero ingredients and premium components
- **Real-time cost deviation tracking** with visual badges
- **Cost optimization** within ±15% of target price

### 🆕 **1-5 Star Rating System** *(NEW in 0.2)*
- **Comprehensive rating formula**: Base + Perks + Quality + Compatibility + Complexity
- **Active perk detection**: BalancedRecipe, SayCheese, VeggiesPower, ComplexAroma
- **Quality bonus** from ingredient tiers (up to +20 points)
- **Compatibility scoring** based on MatchValue triangulation

### 🆕 **Segment Fit Scoring** *(NEW in 0.2)*
- **Price Fit**: 100% at target cost, linear decay ±15%
- **Tag Fit**: Coverage of favorite and expected ingredient tags
- **Evaluation Fit**: Star rating normalized to percentage
- **Weighted total** using customer's price/tag/quality focus

### 🆕 **Interactive Menu Builder** *(NEW in 0.2)*
- **Add recipes to menu** with one click from variant cards
- **Menu preview tab** showing all saved recipes
- **Menu analytics**: Total cost, average rating, average segment fit
- **Recipe management**: View details, clear menu

## 🎯 Legacy Features (MVP 0.1)

### ✅ **Core Data Management**
- **Load & validate** 3 JSON data files (customer types, ingredients, compatibility matches)
- **Graceful error handling** with warnings for missing/malformed data
- **Demo mode** when data files are unavailable

### ✅ **Template Unlock System**
- **45 recipe templates** organized in 6 categories
- **Points-based unlock system** (0, 5, 15 point tiers)
- **Budget management** with real-time spending tracking
- **Template compatibility checks** with anchor ingredients

### ✅ **Customer Segment Analysis**
- **12 customer types** with preferences and expectations
- **Section-based cost expectations** (Appetizer, Main, etc.)
- **Customer priority visualization** (price vs quality vs tags)

### ✅ **Ingredient Compatibility Explorer**
- **Ingredient search** with autocomplete
- **Top 10 partner matches** for any ingredient
- **Flavor profile radar charts**
- **Template-ingredient compatibility warnings**

### ✅ **Interactive UI**
- **Wide layout** with sidebar controls
- **4 main tabs**: Configurator, Ingredients Explorer, Menu Preview, Settings
- **Real-time template unlock management**
- **Ingredient search and filtering**

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Streamlit

### Installation

1. **Navigate to the app directory:**
   ```bash
   cd chef_menu_generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data files:**
   - Place `customer_types.json`, `ingredients_data.json`, and `matches_data.json` in the same directory
   - Or use the file path inputs in the app to specify different locations

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser:**
   - The app will automatically open at `http://localhost:8501`

## 📁 Project Structure

```
chef_menu_generator/
├── app.py                 # Main Streamlit application
├── data_loaders.py        # JSON loading and validation
├── templates_catalog.py   # 45 recipe templates definition
├── domain_utils.py        # Helper functions for data processing
├── logic/                 # MVP 0.2 business logic modules
│   ├── __init__.py       # Package marker
│   ├── generator.py      # Recipe variant generation engine
│   ├── pricing.py        # Target-based pricing and tier selection
│   └── rating.py         # Rating system and segment fit scoring
├── menu/                  # MVP 0.3 advanced menu management
│   ├── __init__.py       # Package marker
│   ├── analytics.py      # Menu KPIs, warnings, and recommendations
│   └── serializer.py     # Export functionality (CSV/JSON/Report)
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── [data files]          # Your JSON data files
```

## 📊 Data File Requirements

### `customer_types.json`
Array of customer segments with:
```json
[
  {
    "name": "Gourmet",
    "favourite_tags": ["Wine", "Seafood"],
    "secondary_favourite_tags": ["Meat"],
    "tag_score_weight": 1.0,
    "price_score_weight": 0.0,
    "evaluation_score_weight": 1.0,
    "expectations": {"Wine": 0.8, "Seafood": 0.9},
    "sections": {
      "MainCourse": {
        "probability": 1.0,
        "cost_expectation": 25.0
      }
    }
  }
]
```

### `ingredients_data.json`
Array of ingredients with:
```json
[
  {
    "name": "Salmon",
    "tags": ["Seafood", "Premium"],
    "flavor_values": {
      "SOUR": 1, "SALT": 2, "ACID": 0,
      "SWEET": 0, "FAT": 4, "UMAMI": 3
    },
    "quality_costs": {
      "NORMAL": {"unit_cost": 3.0, "points_cost": 2},
      "FIRST_CHOICE": {"unit_cost": 5.0, "points_cost": 3},
      "GOURMET": {"unit_cost": 8.0, "points_cost": 4}
    }
  }
]
```

### `matches_data.json`
Array of ingredient compatibility pairs:
```json
[
  {
    "A": "Salmon",
    "B": "Lemon",
    "MatchValue": 3
  }
]
```

## 🎮 How to Use (MVP 0.3.1 - New Interface)

### 🚀 **Quick Start (Recommended for New Users)**
1. **Load Data**: Click "📁 File Dati" in sidebar, specify JSON file paths, click "🔄 Carica Dati"
2. **Start Wizard**: Click "🎯 Inizia Quick Start" button on the main screen
3. **4-Step Process**: Follow the guided wizard through Clientela → Sezione → Template → Ingrediente
4. **Generate & Add**: Choose from 3 recipe variants and add to your menu with one click

### 🧪 **Recipe Studio (For Advanced Control)**
1. **Configure Left Panel**: Select customer segment, menu section, template, and ingredient
2. **Real-time Validation**: See compatibility warnings and suggestions as you select
3. **Generate Variants**: Click "🎨 Genera Ricette" to create 3 different styles
4. **Preview & Add**: Review ingredient lists, ratings, and pricing on the right panel

### 🎯 **Menu Builder (Manage Your Menu)**
1. **View KPIs**: See menu health score, rating average, and coherence metrics
2. **Quick Management**: Expand recipe cards to view details and delete unwanted items
3. **Export Options**: Download as CSV (Excel), JSON (technical), or comprehensive report

### 👨‍💼 **Expert Mode (Power Users)**
- **Advanced Configuration**: Access to all original configurator features
- **Deep Analytics**: Complete KPI dashboard with charts and detailed analysis
- **Ingredient Database**: Full ingredient explorer with compatibility charts

---

## 🎮 Detailed Usage Instructions (All Versions)

### 1. **Load Your Data**
- Use the sidebar to specify paths to your 3 JSON files
- Click "🔄 Carica Dati" to import and validate
- Check for any warnings about missing fields

### 2. **Select Customer & Section**
- Choose a customer segment from the dropdown
- Select a menu section (Appetizer, Main Course, etc.)
- Note the expected cost for that segment/section

### 3. **Manage Template Unlocks**
- Set your available points budget
- Unlock templates by checking boxes in each category
- Monitor spending vs budget in real-time

### 4. **Configure Recipe**
- Select an unlocked template (or show locked ones)
- Search for a main ingredient using the search box
- View compatibility warnings and suggestions

### 5. **Generate Recipe Variants** *(NEW in 0.2)*
- Click "🚀 Generate 3 Variants" when template + ingredient are compatible
- Review 3 different recipe styles: Classico, Fresco, Umami
- Each variant shows: ingredient list with roles, pricing, star rating, segment fit
- Check the rating breakdown to understand scoring
- View active perks (BalancedRecipe, SayCheese, etc.)

### 6. **Add Recipes to Menu** *(NEW in 0.2)*
- Click "📋 Aggiungi al Menu" on your preferred variant
- Switch to "📋 Menu Preview" tab to see all saved recipes
- Monitor menu analytics: total cost, average rating, segment fit
- Clear menu when ready to start fresh

### 7. **Manage Your Menu** *(NEW in 0.3)*
- Switch to "📋 Menu Builder Avanzato" tab to see comprehensive analytics
- Review KPI dashboard: health score, rating, price coherence, complexity
- Check variety warnings and recommendations for menu improvements
- Use section coverage chart to balance menu distribution

### 8. **Advanced Menu Management** *(NEW in 0.3)*
- **Edit recipes**: Change ingredient quality tiers and add notes
- **Duplicate recipes**: Create variations of successful recipes
- **Delete recipes**: Remove unwanted items from menu
- **Export menu**: Download as CSV, JSON, or comprehensive report

### 9. **Export & Analysis** *(NEW in 0.3)*
- **CSV export**: Import into Excel/Sheets for further analysis
- **JSON export**: Technical format for integration or backup
- **Professional report**: Executive summary with KPIs and recommendations
- **Preview reports** before downloading to review content

### 10. **Browse Ingredients & Matches**
- Filter ingredients by name or tag
- Analyze any ingredient's compatibility network
- View match quality distributions

## 🔧 Template Categories & Point Costs

### 🍝 **Pasta & Riso** (9 templates)
- **0 pts:** Pasta, Sautéed Rice
- **5 pts:** Lasagne, Rice Pie
- **15 pts:** Gnocchi, Stuffed Pasta, Risotto, Paella

### 🥩 **Carne** (9 templates)
- **0 pts:** Grilled Meat, Meat Stew
- **5 pts:** Roasted Meat, Boiled Meat, Meatballs
- **15 pts:** Stuffed Meat, Braised Meat, Meat Tartare, Fried Meat

### 🐟 **Pesce** (6 templates)
- **0 pts:** Grilled Fish, Steamed Fish
- **5 pts:** Roasted Fish, Fish Soup
- **15 pts:** Fish Tartare, Fried Fish

### 🥬 **Vegetariano** (8 templates)
- **0 pts:** Sautéed Veggies, Salad, Grilled Veggies
- **5 pts:** Steamed Veggies, Roasted Veggies, Vegetable Soup
- **15 pts:** Velvety, Fried Veggies

### 🍰 **Dessert** (9 templates)
- **0 pts:** Pie, Cookies
- **5 pts:** Semifreddo, Pastries, Cheesecake
- **15 pts:** Ice Cream, Fried Dessert, Millefeuille

### 🍔 **Burger** (3 templates)
- **0 pts:** Hamburger, Fish Burger, Veggie Burger

## ⚠️ Template Compatibility Rules

- **Fish Templates** → Require ingredients with "Seafood" tag
- **Meat Templates** → Require ingredients with "Meat" tag
- **Veggie Templates** → Forbid Meat/Seafood ingredients
- **Dessert Templates** → Forbid Meat/Seafood as main ingredient
- **Pasta/Rice Templates** → Warn if no carb base ingredient

## 🚧 Coming in Future Iterations

This is **MVP 0.3** with advanced menu management, KPIs, and export functionality! Future versions will add:

- **🍽️ Multi-Menu Management**: Compare and manage multiple menu versions
- **📊 Advanced Business Analytics**: ROI analysis, profit margin optimization, seasonal trends
- **🎯 Customer Flow Simulation**: Predict order patterns and kitchen workflow
- **🤖 AI-Powered Optimization**: Machine learning for ingredient substitutions and cost optimization
- **🎮 Game Integration**: Direct export to Chef game format and real-time data sync
- **👥 Team Collaboration**: Share menus, collaborative editing, and team feedback
- **📱 Mobile Companion**: iOS/Android app for on-the-go menu management

## 🐛 Troubleshooting

### "No data files found"
- Ensure JSON files are in the correct location
- Check file names match exactly: `customer_types.json`, `ingredients_data.json`, `matches_data.json`
- The app will show demo data if files are missing

### "Template unlock not working"
- Check you have enough available points
- Verify the template isn't already unlocked
- Try refreshing the page if state gets confused

### "Ingredient search not working"
- Ensure ingredients data is loaded successfully
- Try typing partial names (search is case-insensitive)
- Check for typos in ingredient names

### "Compatibility warnings"
- These are helpful guidance, not errors
- Red warnings mean incompatible combinations
- Yellow warnings are suggestions (e.g., "add pasta base")

### "Export not working"
- Menu must contain at least one recipe to export
- Check browser download settings if files don't download
- Report previews are available in expanders before download

### "Menu health score seems wrong"
- Score is calculated from multiple factors: ratings, fit, price coherence, warnings
- Add more recipes to get more accurate scoring
- Review warnings panel for specific improvement areas

### "KPIs showing unexpected values"
- Ensure customer segment is selected for accurate analysis
- KPIs are calculated based on current menu and segment expectations
- Some metrics require minimum number of recipes for meaningful results

## 🔄 Version History

### MVP 0.3.1 (Current) - UI Refactor
- ✅ **Quick Start Wizard**: 4-step guided workflow with visual customer cards and auto-generation
- ✅ **Recipe Studio**: 2-column layout with advanced controls and real-time validation
- ✅ **Simplified Menu Builder**: Essential KPIs dashboard with quick management and export
- ✅ **Expert Mode**: All advanced features organized in dedicated expert interface
- ✅ **Improved UX**: Better microcopy, Italian localization, intuitive navigation
- ✅ **Guided Experience**: Smart onboarding for new users with contextual help

### MVP 0.3
- ✅ **Advanced Menu Builder**: Complete recipe management with edit/duplicate/delete
- ✅ **Menu Intelligence**: KPI dashboard with health scoring (0-100 points)
- ✅ **Variety Analysis**: Smart warnings for redundancies, gaps, and imbalances
- ✅ **Smart Recommendations**: Context-aware template unlock suggestions
- ✅ **Professional Exports**: CSV, JSON, and comprehensive report generation
- ✅ **Section Analytics**: Visual charts comparing actual vs expected distribution
- ✅ **Enhanced UI**: 4-tab interface with advanced menu management capabilities

### MVP 0.2
- ✅ Recipe variant generation engine with 3 distinct styles (Classico, Fresco, Umami)
- ✅ Target-based pricing with automatic tier selection (Normal/First Choice/Gourmet)
- ✅ Comprehensive 1-5 star rating system with perk detection
- ✅ Segment fit scoring (Price/Tag/Evaluation weighted)
- ✅ Interactive menu builder with recipe cards and analytics
- ✅ 4-tab UI with dedicated Menu Preview section

### MVP 0.1
- ✅ Data loading and validation system
- ✅ Template unlock management (45 templates)
- ✅ Customer segment selection and analysis
- ✅ Ingredient compatibility explorer
- ✅ Template-ingredient compatibility checking
- ✅ Interactive UI with sidebar controls

### Planned Future Versions
- 🔜 Multi-menu management and comparison tools
- 🔜 Advanced business analytics and ROI optimization
- 🔜 AI-powered recommendations and optimization
- 🔜 Game integration and mobile companion app

---

**Built for the Chef: A Restaurant Tycoon Game community** 🎮👨‍🍳