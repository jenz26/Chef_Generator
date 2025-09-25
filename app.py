"""
Chef Planner MVP 0.3
A Streamlit app for planning recipes based on customer segments, templates, and ingredients.
New in 0.3: Advanced menu builder, KPIs, variety analysis, recommendations, export functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Import our modules
from data_loaders import load_and_validate_data
from templates_catalog import (get_all_templates, get_templates_by_category,
                              get_unlock_suggestions, check_template_compatibility,
                              get_template_description)
from domain_utils import (find_ingredient_by_name, get_ingredient_names, build_matches_lookup,
                         get_top_partners, create_flavor_radar_data, get_section_names,
                         get_customer_section_info, format_customer_expectations,
                         format_customer_weights, search_ingredients, validate_template_unlock,
                         calculate_total_unlock_cost, template_category, is_gourmet_segment,
                         format_role_display, get_ingredient_display_info)

# Import MVP 0.2 modules
from logic.generator import generate_variants, RecipeVariant
from logic.pricing import target_based_tiering, get_cost_deviation_badge, get_tier_display_name
from logic.rating import get_rating_breakdown, segment_fit

# Import MVP 0.3 modules
from menu.analytics import menu_kpis, variety_warnings, unlock_recommendations, menu_health_score, get_menu_variety_stats
from menu.serializer import export_menu_csv, export_menu_json, export_report_text, get_export_filename

# Page configuration
st.set_page_config(
    page_title="Chef Planner MVP 0.3",
    page_icon="👨‍🍳",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'unlocked_templates' not in st.session_state:
        st.session_state.unlocked_templates = []
    if 'available_points' not in st.session_state:
        st.session_state.available_points = 50
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'customers' not in st.session_state:
        st.session_state.customers = []
    if 'ingredients' not in st.session_state:
        st.session_state.ingredients = []
    if 'matches' not in st.session_state:
        st.session_state.matches = []
    if 'matches_lookup' not in st.session_state:
        st.session_state.matches_lookup = {}
    # New in MVP 0.2
    if 'menu_items' not in st.session_state:
        st.session_state.menu_items = []
    if 'generated_variants' not in st.session_state:
        st.session_state.generated_variants = []
    # New in MVP 0.3
    if 'suggested_unlocks' not in st.session_state:
        st.session_state.suggested_unlocks = []
    if 'menu_analytics_cache' not in st.session_state:
        st.session_state.menu_analytics_cache = {}

def render_sidebar():
    """Render the sidebar with data loading and main controls"""
    st.sidebar.header("🎛️ Chef Planner Controls")

    # Data loading section
    st.sidebar.subheader("📁 Data Files")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        customers_path = st.text_input("Customer Types", value="customer_types.json", key="customers_path")
    with col2:
        if st.button("📂", help="Browse for customer types file", key="browse_customers"):
            st.info("File browser not implemented in this MVP")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        ingredients_path = st.text_input("Ingredients", value="ingredients_data.json", key="ingredients_path")
    with col2:
        if st.button("📂", help="Browse for ingredients file", key="browse_ingredients"):
            st.info("File browser not implemented in this MVP")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        matches_path = st.text_input("Matches", value="matches_data.json", key="matches_path")
    with col2:
        if st.button("📂", help="Browse for matches file", key="browse_matches"):
            st.info("File browser not implemented in this MVP")

    # Load data button
    if st.sidebar.button("🔄 Load Data", type="primary"):
        with st.spinner("Loading and validating data..."):
            customers, ingredients, matches, warnings = load_and_validate_data(
                customers_path, ingredients_path, matches_path
            )

            if customers and ingredients and matches:
                st.session_state.customers = customers
                st.session_state.ingredients = ingredients
                st.session_state.matches = matches
                st.session_state.matches_lookup = build_matches_lookup(matches)
                st.session_state.data_loaded = True
                st.sidebar.success(f"✅ Data loaded successfully!")
                st.sidebar.info(f"📊 {len(customers)} segments, {len(ingredients)} ingredients, {len(matches)} matches")

                if warnings:
                    with st.sidebar.expander("⚠️ Warnings"):
                        for warning in warnings[:10]:  # Show first 10 warnings
                            st.warning(warning)
            else:
                st.sidebar.error("❌ Failed to load data")

    # Show data status
    if st.session_state.data_loaded:
        st.sidebar.success("📊 Data Ready")

        # Customer segment selector
        if st.session_state.customers:
            customer_names = [customer['name'] for customer in st.session_state.customers]
            selected_customer_name = st.sidebar.selectbox(
                "👥 Customer Segment",
                customer_names,
                key="selected_customer"
            )

            # Find selected customer data
            selected_customer = next(
                (c for c in st.session_state.customers if c['name'] == selected_customer_name),
                None
            )

            if selected_customer:
                # Show customer info
                with st.sidebar.expander(f"ℹ️ {selected_customer_name} Info"):
                    fav_tags = selected_customer.get('favourite_tags', [])
                    sec_tags = selected_customer.get('secondary_favourite_tags', [])

                    st.write("**Favorite Tags:**")
                    if fav_tags:
                        st.write(", ".join(fav_tags))
                    else:
                        st.write("None specified")

                    st.write("**Secondary Tags:**")
                    if sec_tags:
                        st.write(", ".join(sec_tags))
                    else:
                        st.write("None specified")

                    st.write("**Priorities:**")
                    st.write(format_customer_weights(selected_customer))

                # Section selector
                sections = get_section_names()
                selected_section = st.sidebar.selectbox(
                    "🍽️ Menu Section",
                    sections,
                    key="selected_section"
                )

                # Show cost expectation
                if selected_section:
                    section_info = get_customer_section_info(selected_customer, selected_section)
                    cost_expectation = section_info.get('cost_expectation', 10.0)
                    probability = section_info.get('probability', 0.5)

                    st.sidebar.metric(
                        "💰 Expected Cost",
                        f"€{cost_expectation:.1f}",
                        help=f"Probability: {probability:.1%}"
                    )
    else:
        st.sidebar.warning("📁 Please load data files first")

    # Points and template unlock
    st.sidebar.subheader("🏆 Template Unlock System")

    available_points = st.sidebar.number_input(
        "Available Points",
        min_value=0,
        max_value=500,
        value=st.session_state.available_points,
        step=5,
        key="points_input"
    )
    st.session_state.available_points = available_points

    # Template unlock interface
    render_template_unlock_panel()

def render_template_unlock_panel():
    """Render the template unlock panel in sidebar"""
    templates = get_all_templates()
    templates_by_category = get_templates_by_category()

    # Calculate current spending
    current_spending = calculate_total_unlock_cost(st.session_state.unlocked_templates)
    remaining_points = st.session_state.available_points - current_spending

    st.sidebar.write(f"**Points Used:** {current_spending} / {st.session_state.available_points}")
    st.sidebar.write(f"**Remaining:** {remaining_points}")

    if remaining_points < 0:
        st.sidebar.error("❌ Over budget! Please unlock fewer templates.")

    # Template categories
    for category, category_templates in templates_by_category.items():
        with st.sidebar.expander(f"📋 {category} ({len(category_templates)} templates)"):
            for template in category_templates:
                template_name = template.name

                # Check if already unlocked
                is_unlocked = template_name in st.session_state.unlocked_templates

                # Check if can afford
                can_afford = template.points <= remaining_points or is_unlocked

                # Create checkbox
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_state = st.checkbox(
                        f"{template_name}",
                        value=is_unlocked,
                        disabled=not can_afford and not is_unlocked,
                        key=f"template_{template_name}"
                    )
                with col2:
                    if template.points == 0:
                        st.write("🆓")
                    else:
                        st.write(f"{template.points}pts")

                # Update state
                if new_state != is_unlocked:
                    if new_state:
                        st.session_state.unlocked_templates.append(template_name)
                    else:
                        st.session_state.unlocked_templates.remove(template_name)
                    st.rerun()

                # Show status
                if not can_afford and not is_unlocked:
                    st.write(f"⚠️ Need {template.points - remaining_points} more points")

def render_configurator_tab():
    """Render the main configurator tab"""
    st.header("👨‍🍳 Recipe Configurator")

    if not st.session_state.data_loaded:
        st.warning("⚠️ Please load data files from the sidebar first")
        return

    # Template selection
    st.subheader("🎯 Template Selection")

    # Filter templates
    unlocked_templates = [name for name in st.session_state.unlocked_templates]
    all_templates = get_all_templates()

    col1, col2 = st.columns(2)
    with col1:
        show_locked = st.checkbox("Show locked templates", value=False)

    if show_locked:
        available_templates = list(all_templates.keys())
    else:
        available_templates = unlocked_templates

    if not available_templates:
        st.warning("⚠️ No templates available. Please unlock some templates in the sidebar.")
        return

    # Template selector
    selected_template = st.selectbox(
        "Select Template",
        available_templates,
        format_func=lambda x: f"{x} {'🔒' if x not in unlocked_templates else '✅'} ({all_templates[x].points} pts)",
        key="selected_template"
    )

    if selected_template:
        template_obj = all_templates[selected_template]

        # Show template info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Category:** {template_obj.category}")
        with col2:
            st.info(f"**Points:** {template_obj.points}")
        with col3:
            if selected_template in unlocked_templates:
                st.success("✅ Unlocked")
            else:
                st.error("🔒 Locked")

        # Show template description
        description = get_template_description(selected_template)
        st.write(f"*{description}*")

        # Unlock suggestions if template is locked
        if selected_template not in unlocked_templates:
            st.warning(f"🔒 This template requires {template_obj.points} points to unlock")

            # Show unlock suggestions
            if st.session_state.customers and hasattr(st, 'session_state') and 'selected_customer' in st.session_state:
                selected_section = st.session_state.get('selected_section', 'MainCourse')
                suggestions = get_unlock_suggestions("Generic", selected_section)
                if selected_template in suggestions:
                    st.info(f"💡 **Why unlock this:** {suggestions[selected_template]}")

    # Ingredient selection
    st.subheader("🥕 Anchor Ingredient")

    if st.session_state.ingredients:
        ingredient_names = get_ingredient_names(st.session_state.ingredients)

        # Search/autocomplete for ingredients
        search_query = st.text_input(
            "Search for main ingredient",
            placeholder="Type ingredient name...",
            key="ingredient_search"
        )

        if search_query:
            matching_ingredients = search_ingredients(st.session_state.ingredients, search_query)
            if matching_ingredients:
                selected_ingredient_name = st.selectbox(
                    "Select from matches",
                    matching_ingredients,
                    key="ingredient_selector"
                )
            else:
                st.warning(f"No ingredients found matching '{search_query}'")
                selected_ingredient_name = None
        else:
            selected_ingredient_name = st.selectbox(
                "Or select from all ingredients",
                [""] + ingredient_names,
                key="ingredient_selector_all"
            )

        # Show ingredient and compatibility info
        if selected_ingredient_name:
            ingredient = find_ingredient_by_name(st.session_state.ingredients, selected_ingredient_name)

            if ingredient:
                render_readiness_panel(selected_template, ingredient)

def render_readiness_panel(template_name: str, ingredient: Dict[str, Any]):
    """Render the readiness panel showing compatibility and ingredient info"""
    st.subheader("📋 Recipe Readiness Check")

    col1, col2 = st.columns(2)

    with col1:
        # Template compatibility
        st.write("**🔧 Template Compatibility**")
        is_compatible, message = check_template_compatibility(template_name, ingredient)

        if is_compatible:
            if message.startswith("⚠️"):
                st.warning(message)
            else:
                st.success(message)
        else:
            st.error(message)

        # Customer expectations (if customer selected)
        if 'selected_customer' in st.session_state:
            customer_name = st.session_state.selected_customer
            selected_customer = next(
                (c for c in st.session_state.customers if c['name'] == customer_name),
                None
            )

            if selected_customer:
                st.write(f"**👥 {customer_name} Expectations**")
                expectations_text = format_customer_expectations(selected_customer)
                st.write(expectations_text)

    with col2:
        # Top ingredient partners
        st.write("**🤝 Top 10 Compatible Partners**")

        if st.session_state.matches_lookup:
            ingredient_name = ingredient.get('name', '')
            top_partners = get_top_partners(ingredient_name, st.session_state.matches_lookup, limit=10)

            if top_partners:
                partners_df = pd.DataFrame(top_partners, columns=['Partner', 'Match Value'])
                partners_df['Match Quality'] = partners_df['Match Value'].map({
                    3: '🔥 Excellent',
                    2: '👍 Good',
                    1: '👌 OK'
                })

                st.dataframe(
                    partners_df[['Partner', 'Match Quality', 'Match Value']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No compatibility data found for this ingredient")
        else:
            st.warning("No matches data loaded")

    # Flavor profile
    st.write("**🎨 Ingredient Flavor Profile**")
    flavor_data = create_flavor_radar_data(ingredient)

    if any(flavor_data.values()):
        # Create radar chart
        categories = list(flavor_data.keys())
        values = list(flavor_data.values())

        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=ingredient.get('name', 'Ingredient')
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) + 1] if max(values) > 0 else [0, 5]
                )),
            showlegend=False,
            title=f"Flavor Profile: {ingredient.get('name', 'Unknown')}",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        # Show as simple table if no flavor data
        flavor_df = pd.DataFrame([
            {"Flavor": k, "Intensity": v} for k, v in flavor_data.items()
        ])
        st.dataframe(flavor_df, use_container_width=True, hide_index=True)

    # Recipe variant generation (MVP 0.2)
    if is_compatible and 'selected_customer' in st.session_state and 'selected_section' in st.session_state:
        render_variant_generation_section(template_name, ingredient)
    st.write("- Template requirements")

def render_ingredients_tab():
    """Render the ingredients and matches exploration tab"""
    st.header("🥕 Ingredients & Compatibility Explorer")

    if not st.session_state.data_loaded:
        st.warning("⚠️ Please load data files from the sidebar first")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Ingredients Database")

        if st.session_state.ingredients:
            # Create ingredients dataframe
            ingredients_data = []
            for ingredient in st.session_state.ingredients:
                tags = ingredient.get('tags', [])
                if isinstance(tags, str):
                    tags = tags.split(',')

                ingredients_data.append({
                    'Name': ingredient.get('name', ''),
                    'Tags': ', '.join(tags),
                    'Primary Tag': tags[0] if tags else 'Unknown',
                })

            df = pd.DataFrame(ingredients_data)

            # Filters
            col_a, col_b = st.columns(2)
            with col_a:
                name_filter = st.text_input("Filter by name", key="ingredient_name_filter")
            with col_b:
                tag_filter = st.selectbox(
                    "Filter by primary tag",
                    ["All"] + list(df['Primary Tag'].unique()),
                    key="ingredient_tag_filter"
                )

            # Apply filters
            filtered_df = df.copy()
            if name_filter:
                filtered_df = filtered_df[filtered_df['Name'].str.contains(name_filter, case=False)]
            if tag_filter != "All":
                filtered_df = filtered_df[filtered_df['Primary Tag'] == tag_filter]

            # Show table
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Show stats
            st.info(f"📈 Showing {len(filtered_df)} of {len(df)} ingredients")

    with col2:
        st.subheader("🔍 Ingredient Analysis")

        if st.session_state.ingredients:
            # Select ingredient for analysis
            ingredient_names = get_ingredient_names(st.session_state.ingredients)
            selected_name = st.selectbox(
                "Analyze ingredient",
                ingredient_names,
                key="analyze_ingredient"
            )

            if selected_name:
                ingredient = find_ingredient_by_name(st.session_state.ingredients, selected_name)

                if ingredient:
                    # Show basic info
                    tags = ingredient.get('tags', [])
                    if isinstance(tags, str):
                        tags = tags.split(',')

                    st.write(f"**Tags:** {', '.join(tags)}")

                    # Show top partners
                    if st.session_state.matches_lookup:
                        top_partners = get_top_partners(selected_name, st.session_state.matches_lookup, limit=15)

                        if top_partners:
                            st.write(f"**🤝 Top Partners ({len(top_partners)}):**")

                            partners_data = []
                            for partner, match_value in top_partners:
                                match_quality = {3: "🔥", 2: "👍", 1: "👌"}[match_value]
                                partners_data.append({
                                    'Partner': partner,
                                    'Quality': match_quality,
                                    'Value': match_value
                                })

                            partners_df = pd.DataFrame(partners_data)
                            st.dataframe(partners_df, use_container_width=True, hide_index=True)

                            # Show match value distribution
                            match_counts = pd.Series([mv for _, mv in top_partners]).value_counts().sort_index()

                            fig = px.pie(
                                values=match_counts.values,
                                names=[f"Level {i}" for i in match_counts.index],
                                title="Match Quality Distribution"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        else:
                            st.info("No compatibility data for this ingredient")

def render_settings_tab():
    """Render the settings tab (placeholder for future features)"""
    st.header("⚙️ Settings")

    st.info("🚧 **Settings Panel - Coming Soon!**")

    st.write("This section will include:")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Rating & Scoring:**")
        st.write("- Recipe rating algorithm parameters")
        st.write("- Perk bonus weights")
        st.write("- Quality multipliers")
        st.write("- Compatibility scoring")

        st.write("**Recipe Generation:**")
        st.write("- Ingredient count ranges by template category")
        st.write("- Flavor balance rules")
        st.write("- Target-based pricing sensitivity")

    with col2:
        st.write("**UI Preferences:**")
        st.write("- Default customer segment")
        st.write("- Show/hide advanced features")
        st.write("- Explanation detail level")

        st.write("**Data Export:**")
        st.write("- Menu export formats")
        st.write("- Recipe sharing options")
        st.write("- Data backup/restore")

    # Temporary settings for this version
    st.subheader("🔧 Current Session Settings")

    col1, col2 = st.columns(2)
    with col1:
        debug_mode = st.checkbox("Debug Mode", value=False, help="Show additional debugging information")
        st.session_state.debug_mode = debug_mode

    with col2:
        explanations = st.checkbox("Show Explanations", value=True, help="Show detailed explanations throughout the app")
        st.session_state.show_explanations = explanations


def render_variant_generation_section(template_name: str, ingredient: Dict[str, Any]):
    """Render recipe variant generation section (MVP 0.2)"""
    st.subheader("🍽️ Generate Recipe Variants")

    # Get current selection from session state
    customer_name = st.session_state.selected_customer
    section = st.session_state.selected_section

    # Find customer data
    selected_customer = next(
        (c for c in st.session_state.customers if c['name'] == customer_name),
        None
    )

    if not selected_customer:
        st.error("Customer data not found")
        return

    # Get cost expectation
    section_info = get_customer_section_info(selected_customer, section)
    cost_expectation = section_info.get('cost_expectation', 10.0)

    st.write(f"**Generating variants for:** {customer_name} → {section} → {template_name} → {ingredient.get('name', 'Unknown')}")
    st.write(f"**Target cost:** €{cost_expectation:.1f}")

    # Generate variants button
    if st.button("🚀 Generate 3 Variants", type="primary", use_container_width=True):
        with st.spinner("Generating recipe variants..."):
            try:
                # Convert data to DataFrames for the logic modules
                ingredients_df = pd.DataFrame(st.session_state.ingredients)
                matches_df = pd.DataFrame(st.session_state.matches)

                # Generate variants
                variants = generate_variants(
                    segment=selected_customer,
                    section=section,
                    template=template_name,
                    anchor_name=ingredient.get('name', ''),
                    ingredients_df=ingredients_df,
                    matches_df=matches_df,
                    templates_meta={},  # Not used in current implementation
                    n_variants=3
                )

                st.session_state.generated_variants = variants
                st.success(f"✅ Generated {len(variants)} recipe variants!")

            except Exception as e:
                st.error(f"❌ Error generating variants: {str(e)}")
                return

    # Display generated variants
    if st.session_state.generated_variants:
        st.subheader("🎨 Recipe Variants")

        for i, variant in enumerate(st.session_state.generated_variants):
            render_variant_card(variant, i, selected_customer, section, cost_expectation, template_name)


def render_variant_card(variant: RecipeVariant, variant_idx: int, customer: Dict[str, Any],
                       section: str, cost_expectation: float, template_name: str):
    """Render a single recipe variant card"""

    with st.container():
        st.markdown(f"### 🍽️ Variante {variant_idx + 1}: {variant.style.title()}")

        # Convert data for processing
        ingredients_df = pd.DataFrame(st.session_state.ingredients)
        matches_df = pd.DataFrame(st.session_state.matches)

        try:
            # Calculate pricing and tiers
            tiers, actual_cost, suggested_price = target_based_tiering(
                variant, customer, section, ingredients_df, cost_expectation
            )
            variant.tiers = tiers

            # Calculate rating
            category = template_category(template_name)
            is_gourmet = is_gourmet_segment(customer.get('name', ''), customer)
            rating_breakdown = get_rating_breakdown(variant, tiers, category, ingredients_df, is_gourmet)

            # Calculate segment fit
            fit_scores = segment_fit(
                rating_breakdown['stars'], customer, section, suggested_price, variant, ingredients_df
            )

            # Display in columns
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                # Ingredients list with roles and tiers
                st.write("**🥘 Ingredienti:**")
                ingredient_info = []

                for ing_name in variant.ingredients:
                    role = variant.roles.get(ing_name, 'complement')
                    tier = tiers.get(ing_name, 'NORMAL')
                    ing_info = get_ingredient_display_info(ing_name, ingredients_df, role, tier)
                    ingredient_info.append({
                        'Ingrediente': ing_name,
                        'Ruolo': format_role_display(role),
                        'Qualità': get_tier_display_name(tier),
                        'Costo': f"€{ing_info['cost']:.2f}"
                    })

                ingredients_table = pd.DataFrame(ingredient_info)
                st.dataframe(ingredients_table, use_container_width=True, hide_index=True)

                # Cost and pricing
                cost_badge, badge_color = get_cost_deviation_badge(actual_cost, cost_expectation)
                st.write(f"**💰 Costo totale:** €{actual_cost:.2f}")
                st.write(f"**🎯 Prezzo suggerito:** €{suggested_price:.2f}")
                if badge_color == "success":
                    st.success(f"✅ {cost_badge}")
                elif badge_color == "warning":
                    st.warning(f"⚠️ {cost_badge}")
                elif badge_color == "danger":
                    st.error(f"❌ {cost_badge}")
                else:
                    st.info(f"ℹ️ {cost_badge}")

            with col2:
                # Rating breakdown
                stars = rating_breakdown['stars']
                st.metric("⭐ Rating", f"{stars:.1f}/5.0")

                with st.expander("📊 Rating Breakdown"):
                    st.write(f"**Base:** {rating_breakdown['evaluation_base']}")
                    st.write(f"**Perk Bonus:** +{rating_breakdown['perk_bonus']}")
                    st.write(f"**Quality Bonus:** +{rating_breakdown['quality_bonus']}")
                    st.write(f"**Compatibility:** +{rating_breakdown['compatibility_bonus']}")
                    st.write(f"**Complexity:** {rating_breakdown['complexity_tuning']:+.1f}")
                    st.write(f"**Total:** {rating_breakdown['total_score']:.1f}/20")

                # Active perks
                if rating_breakdown['active_perks']:
                    st.write("**🏆 Perk Attivi:**")
                    for perk in rating_breakdown['active_perks']:
                        st.write(f"• {perk}")

            with col3:
                # Segment fit
                total_fit = fit_scores['total_fit']
                st.metric("🎯 Segment Fit", f"{total_fit:.0f}%")

                with st.expander("📈 Fit Breakdown"):
                    st.write(f"**Price Fit:** {fit_scores['price_fit']:.0f}%")
                    st.write(f"**Tag Fit:** {fit_scores['tag_fit']:.0f}%")
                    st.write(f"**Eval Fit:** {fit_scores['eval_fit']:.0f}%")

                # Add to menu button
                if st.button(f"📋 Aggiungi al Menu", key=f"add_variant_{variant_idx}", use_container_width=True):
                    # Collect tags for analytics
                    from domain_utils import collect_tags
                    ingredient_tags = collect_tags(variant.ingredients, ingredients_df)

                    menu_item = {
                        'template': template_name,
                        'anchor': variant.ingredients[0],
                        'style': variant.style,
                        'ingredients': variant.ingredients,
                        'roles': variant.roles,
                        'tiers': tiers,
                        'cost': actual_cost,
                        'price': suggested_price,
                        'stars': stars,
                        'segment_fit': total_fit,
                        'customer': customer.get('name', ''),
                        'section': section,
                        'notes': variant.notes,
                        'tag_set': ingredient_tags,
                        'fit_breakdown': fit_scores
                    }
                    st.session_state.menu_items.append(menu_item)
                    st.success("✅ Aggiunto al menu!")

            # Recipe notes
            st.write(f"**📝 Note:** {variant.notes}")

        except Exception as e:
            st.error(f"Error processing variant: {str(e)}")

        st.markdown("---")


def render_menu_preview_tab():
    """Render the advanced Menu Builder tab (MVP 0.3)"""
    st.header("📋 Menu Builder Avanzato")

    if not st.session_state.menu_items:
        st.info("📝 **Menu vuoto** - Aggiungi delle ricette dal Configurator per iniziare!")

        if st.session_state.data_loaded:
            st.write("**Come costruire il tuo menu:**")
            st.write("1. 🎯 Vai al **Configurator** e seleziona segmento cliente + sezione")
            st.write("2. 🍽️ Genera varianti e aggiungi quelle che preferisci")
            st.write("3. 📊 Ritorna qui per vedere KPI, warnings e suggerimenti")
            st.write("4. 📤 Esporta il menu finale in CSV/JSON/Report")
        return

    # Get current customer context for analytics
    current_customer = None
    current_segment_name = "Menu"
    if 'selected_customer' in st.session_state and st.session_state.customers:
        customer_name = st.session_state.selected_customer
        current_customer = next((c for c in st.session_state.customers if c['name'] == customer_name), None)
        current_segment_name = customer_name

    # Prepare sections metadata for KPI calculation
    sections_meta = {}
    if current_customer:
        customer_sections = current_customer.get('sections', {})
        for section, info in customer_sections.items():
            sections_meta[section] = info

    # Calculate KPIs and analytics
    kpis = menu_kpis(st.session_state.menu_items, current_customer or {}, sections_meta)
    warnings = variety_warnings(st.session_state.menu_items, current_customer or {})

    # Menu Health Score
    health_score = menu_health_score(kpis, len(warnings))

    # Header with health score
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"📋 **Menu: {kpis['n_items']} ricette** | **Segmento:** {current_segment_name}")
    with col2:
        color = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
        st.metric("🏆 Menu Health", f"{color} {health_score}/100")

    # KPI Cards
    st.subheader("📊 KPI Dashboard")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        stars_color = "🟢" if kpis['avg_stars'] >= 4.0 else "🟡" if kpis['avg_stars'] >= 3.0 else "🔴"
        st.metric("⭐ Rating Medio", f"{kpis['avg_stars']:.1f}/5.0", delta=None, help=f"{stars_color} Qualità media dei piatti")

    with kpi_col2:
        fit_color = "🟢" if kpis['avg_fit_total'] >= 80 else "🟡" if kpis['avg_fit_total'] >= 60 else "🔴"
        st.metric("🎯 Segment Fit", f"{kpis['avg_fit_total']:.0f}%", delta=None, help=f"{fit_color} Adattamento al segmento")

    with kpi_col3:
        price_color = "🟢" if kpis['avg_price_deviation_pct'] <= 10 else "🟡" if kpis['avg_price_deviation_pct'] <= 20 else "🔴"
        st.metric("💶 Coerenza Prezzi", f"{kpis['avg_price_deviation_pct']:.1f}%", delta=None, help=f"{price_color} Deviazione dai target")

    with kpi_col4:
        complexity = kpis['complexity_stats']['avg']
        complexity_desc = f"{complexity:.1f} ing/ricetta"
        st.metric("🔧 Complessità", complexity_desc, delta=None, help="Media ingredienti per ricetta")

    # Section Coverage Chart (if we have customer data)
    if current_customer and sections_meta:
        st.subheader("📈 Copertura Sezioni vs Atteso")

        chart_data = []
        for section, info in kpis['section_coverage'].items():
            chart_data.append({
                'Sezione': section,
                'Attuale': info['actual_ratio'] * 100,
                'Atteso': info['expected_ratio'] * 100,
                'Tipo': 'Attuale'
            })

        if chart_data:
            chart_df = pd.DataFrame(chart_data)

            # Create comparison chart
            fig = px.bar(
                chart_df,
                x='Sezione',
                y=['Attuale', 'Atteso'],
                title="Distribuzione Sezioni: Attuale vs Atteso (%)",
                barmode='group',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    # Advanced Recipe Management Table
    st.subheader("🍽️ Gestione Ricette")

    render_recipe_management_table(st.session_state.menu_items)

    # Warnings and Recommendations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚠️ Avvisi Menu")
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("✅ Nessun avviso - menu equilibrato!")

    with col2:
        st.subheader("💡 Suggerimenti Sblocco")
        render_unlock_recommendations_panel(current_customer or {})

    # Export Section
    st.subheader("📤 Esportazione Menu")
    render_export_section(st.session_state.menu_items, kpis, warnings, current_segment_name)


def render_recipe_management_table(menu_items: List[Dict[str, Any]]):
    """Render the advanced recipe management table with edit/delete/duplicate"""

    if not menu_items:
        return

    # Create enhanced table data
    table_data = []
    for i, item in enumerate(menu_items):
        table_data.append({
            'ID': i,
            'Nome': f"{item.get('template', 'N/A')} con {item.get('anchor', 'N/A')}",
            'Sezione': item.get('section', 'N/A'),
            'Template': item.get('template', 'N/A'),
            'Rating': f"{item.get('stars', 0):.1f}⭐",
            'Prezzo': f"€{item.get('price', 0):.2f}",
            'Costo': f"€{item.get('cost', 0):.2f}",
            'Fit': f"{item.get('segment_fit', 0):.0f}%",
            'Ingredienti': len(item.get('ingredients', [])),
            'Stile': item.get('style', 'classico').title(),
            'Tags': ', '.join(list(item.get('tag_set', set()))[:3]) if item.get('tag_set') else 'N/A'
        })

    if table_data:
        df = pd.DataFrame(table_data)

        # Display table
        st.dataframe(df.drop('ID', axis=1), use_container_width=True, hide_index=True)

        # Action buttons row
        st.write("**Azioni Ricette:**")
        action_cols = st.columns([2, 2, 2, 2, 2])

        with action_cols[0]:
            recipe_to_edit = st.selectbox(
                "Modifica ricetta",
                options=[-1] + list(range(len(menu_items))),
                format_func=lambda x: "Seleziona..." if x == -1 else f"{menu_items[x]['template']} ({x+1})",
                key="edit_recipe_selector"
            )

        with action_cols[1]:
            if recipe_to_edit >= 0 and st.button("✏️ Edit", key="edit_recipe_btn"):
                render_edit_recipe_modal(recipe_to_edit)

        with action_cols[2]:
            recipe_to_duplicate = st.selectbox(
                "Duplica ricetta",
                options=[-1] + list(range(len(menu_items))),
                format_func=lambda x: "Seleziona..." if x == -1 else f"{menu_items[x]['template']} ({x+1})",
                key="duplicate_recipe_selector"
            )

        with action_cols[3]:
            if recipe_to_duplicate >= 0 and st.button("📄 Duplica", key="duplicate_recipe_btn"):
                duplicate_recipe(recipe_to_duplicate)

        with action_cols[4]:
            if st.button("🗑️ Svuota Tutto", type="secondary", key="clear_menu_btn"):
                st.session_state.menu_items = []
                st.rerun()


def render_edit_recipe_modal(recipe_index: int):
    """Render inline recipe editing interface"""
    if recipe_index >= len(st.session_state.menu_items):
        return

    recipe = st.session_state.menu_items[recipe_index]

    st.subheader(f"✏️ Modifica: {recipe.get('template', 'N/A')}")

    with st.container():
        edit_col1, edit_col2 = st.columns(2)

        with edit_col1:
            # Hero tier override
            hero_ingredient = recipe.get('ingredients', [''])[0] if recipe.get('ingredients') else ''
            current_hero_tier = recipe.get('tiers', {}).get(hero_ingredient, 'NORMAL')

            new_hero_tier = st.selectbox(
                f"Qualità {hero_ingredient}:",
                options=['NORMAL', 'FIRST_CHOICE', 'GOURMET'],
                index=['NORMAL', 'FIRST_CHOICE', 'GOURMET'].index(current_hero_tier),
                key=f"edit_hero_tier_{recipe_index}"
            )

        with edit_col2:
            # Notes
            current_notes = recipe.get('notes', '')
            new_notes = st.text_area(
                "Note:",
                value=current_notes,
                max_chars=200,
                key=f"edit_notes_{recipe_index}"
            )

        # Action buttons
        save_col, cancel_col = st.columns(2)

        with save_col:
            if st.button("💾 Salva Modifiche", key=f"save_edit_{recipe_index}", type="primary"):
                # Apply changes
                if recipe.get('tiers') and hero_ingredient:
                    recipe['tiers'][hero_ingredient] = new_hero_tier
                recipe['notes'] = new_notes

                st.success("✅ Ricetta aggiornata!")
                st.rerun()

        with cancel_col:
            if st.button("❌ Annulla", key=f"cancel_edit_{recipe_index}"):
                st.rerun()


def duplicate_recipe(recipe_index: int):
    """Duplicate a recipe in the menu"""
    if recipe_index >= len(st.session_state.menu_items):
        return

    original_recipe = st.session_state.menu_items[recipe_index]

    # Create duplicate with modifications
    duplicate = original_recipe.copy()
    duplicate['notes'] = f"Copia di: {duplicate.get('notes', '')}"

    # Add to menu
    st.session_state.menu_items.append(duplicate)
    st.success(f"✅ Ricetta duplicata! Ora hai {len(st.session_state.menu_items)} ricette.")
    st.rerun()


def render_unlock_recommendations_panel(segment: Dict[str, Any]):
    """Render unlock recommendations based on current menu"""
    if not st.session_state.data_loaded:
        st.info("Carica i dati per vedere i suggerimenti di sblocco")
        return

    # Get available data
    templates_catalog = get_all_templates()
    unlocked_set = set(st.session_state.unlocked_templates)
    points_budget = st.session_state.available_points - calculate_total_unlock_cost(st.session_state.unlocked_templates)

    # Generate recommendations
    recommendations = unlock_recommendations(
        st.session_state.menu_items,
        segment,
        templates_catalog,
        unlocked_set,
        points_budget
    )

    if recommendations:
        for i, rec in enumerate(recommendations):
            template = rec['template']
            points = rec['points']
            reason = rec['reason']

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{template}** ({points} pts)")
                st.caption(reason)
            with col2:
                if st.button("➕ Segna", key=f"suggest_{i}", help="Segna per sblocco futuro"):
                    if template not in st.session_state.suggested_unlocks:
                        st.session_state.suggested_unlocks.append(template)
                        st.success(f"✅ {template} aggiunto ai suggeriti")
    else:
        st.info("🎉 Menu completo - nessun template aggiuntivo raccomandato!")

    # Show suggested unlocks
    if st.session_state.suggested_unlocks:
        st.write("**🔖 Template Suggeriti:**")
        for template in st.session_state.suggested_unlocks:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {template}")
            with col2:
                if st.button("❌", key=f"remove_suggest_{template}", help="Rimuovi suggerimento"):
                    st.session_state.suggested_unlocks.remove(template)
                    st.rerun()


def render_export_section(menu_items: List[Dict[str, Any]], kpis: Dict[str, Any],
                         warnings: List[str], segment_name: str):
    """Render export functionality section"""

    export_col1, export_col2, export_col3 = st.columns(3)

    # Generate data for exports
    recommendations = []
    if st.session_state.data_loaded and 'selected_customer' in st.session_state:
        customer = next((c for c in st.session_state.customers
                        if c['name'] == st.session_state.selected_customer), {})
        templates_catalog = get_all_templates()
        unlocked_set = set(st.session_state.unlocked_templates)
        points_budget = st.session_state.available_points - calculate_total_unlock_cost(st.session_state.unlocked_templates)
        recommendations = unlock_recommendations(menu_items, customer, templates_catalog, unlocked_set, points_budget)

    with export_col1:
        if st.button("📊 Export CSV", use_container_width=True):
            if menu_items:
                csv_data = export_menu_csv(menu_items)
                filename = get_export_filename('csv', segment_name)
                st.download_button(
                    label="⬇️ Scarica CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                st.warning("Menu vuoto - niente da esportare")

    with export_col2:
        if st.button("📋 Export JSON", use_container_width=True):
            if menu_items:
                json_data = export_menu_json(menu_items)
                filename = get_export_filename('json', segment_name)
                st.download_button(
                    label="⬇️ Scarica JSON",
                    data=json_data,
                    file_name=filename,
                    mime="application/json"
                )
            else:
                st.warning("Menu vuoto - niente da esportare")

    with export_col3:
        if st.button("📄 Export Report", use_container_width=True):
            if menu_items:
                report_data = export_report_text(menu_items, kpis, warnings, recommendations, segment_name)
                filename = get_export_filename('report', segment_name)
                st.download_button(
                    label="⬇️ Scarica Report",
                    data=report_data,
                    file_name=filename,
                    mime="text/plain"
                )
            else:
                st.warning("Menu vuoto - niente da esportare")

    # Report preview
    if menu_items:
        with st.expander("👁️ Anteprima Report"):
            report_preview = export_report_text(menu_items, kpis, warnings, recommendations, segment_name)
            st.text(report_preview[:2000] + "..." if len(report_preview) > 2000 else report_preview)


def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()

    # App header
    st.title("👨‍🍳 Chef Planner MVP 0.3")
    st.markdown("*Advanced menu builder with KPIs, variety analysis, and export functionality*")

    # Render sidebar
    render_sidebar()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Configurator", "🥕 Ingredients & Matches", "📋 Menu Preview", "⚙️ Settings"])

    with tab1:
        render_configurator_tab()

    with tab2:
        render_ingredients_tab()

    with tab3:
        render_menu_preview_tab()

    with tab4:
        render_settings_tab()

    # Footer
    st.markdown("---")
    st.markdown("*Chef Planner MVP 0.3 - Advanced menu builder with KPIs, variety analysis, and export functionality*")

if __name__ == "__main__":
    main()