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
    page_title="Chef Planner MVP 0.3.1",
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
    # New in MVP 0.3.1 - UI Refactor
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1
    if 'wizard_customer' not in st.session_state:
        st.session_state.wizard_customer = None
    if 'wizard_section' not in st.session_state:
        st.session_state.wizard_section = None
    if 'wizard_template' not in st.session_state:
        st.session_state.wizard_template = None
    if 'wizard_ingredient' not in st.session_state:
        st.session_state.wizard_ingredient = None
    if 'show_wizard' not in st.session_state:
        st.session_state.show_wizard = True

def render_sidebar():
    """Render the sidebar with data loading and main controls"""
    st.sidebar.header("⚙️ Impostazioni")

    # Data loading section
    with st.sidebar.expander("📁 File Dati", expanded=not st.session_state.data_loaded):
        st.markdown("*Carica i file JSON del gioco*")

        customers_path = st.text_input("👥 Clienti", value="customer_types.json", key="customers_path", help="File con i tipi di clientela")
        ingredients_path = st.text_input("🥘 Ingredienti", value="ingredients_data.json", key="ingredients_path", help="Database ingredienti completo")
        matches_path = st.text_input("🤝 Compatibilità", value="matches_data.json", key="matches_path", help="Abbinamenti ingredienti")

        # Load data button
        if st.button("🔄 Carica Dati", type="primary", help="Carica e valida i file JSON"):
            with st.spinner("Caricamento in corso..."):
                customers, ingredients, matches, warnings = load_and_validate_data(
                    customers_path, ingredients_path, matches_path
                )

            if customers and ingredients and matches:
                st.session_state.customers = customers
                st.session_state.ingredients = ingredients
                st.session_state.matches = matches
                st.session_state.matches_lookup = build_matches_lookup(matches)
                st.session_state.data_loaded = True
                st.sidebar.success(f"✅ Dati caricati con successo!")
                st.sidebar.info(f"📊 {len(customers)} segmenti, {len(ingredients)} ingredienti, {len(matches)} abbinamenti")

                if warnings:
                    with st.sidebar.expander("⚠️ Avvisi"):
                        for warning in warnings[:10]:  # Show first 10 warnings
                            st.warning(warning)
            else:
                st.sidebar.error("❌ Errore nel caricamento dei dati")

    # Status overview
    st.sidebar.markdown("---")
    if st.session_state.data_loaded:
        st.sidebar.success("🟢 Sistema Pronto")
        menu_count = len(st.session_state.menu_items)
        if menu_count > 0:
            st.sidebar.info(f"📋 Menu: {menu_count} ricette")
        else:
            st.sidebar.info("📋 Menu vuoto")

        # Customer segment selector
        with st.sidebar.expander("🎯 Analisi per Segmento", expanded=False):
            if st.session_state.customers:
                customer_names = [customer['name'] for customer in st.session_state.customers]
                selected_customer_name = st.selectbox(
                    "👥 Segmento Cliente",
                    customer_names,
                    key="selected_customer",
                    help="Seleziona per analisi mirate"
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


# ====== QUICK START WIZARD FUNCTIONS (MVP 0.3.1) ======

def render_quick_start_wizard():
    """Render the 4-step Quick Start wizard"""
    if not st.session_state.data_loaded:
        st.warning("⚠️ Carica prima i dati dal sidebar per iniziare")
        return

    st.header("🚀 Quick Start - Crea la tua prima ricetta")
    st.markdown("*Seguimi in 4 semplici passaggi per creare una ricetta perfetta*")

    # Progress bar
    progress = st.session_state.wizard_step / 4.0
    st.progress(progress)

    # Step indicator
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        emoji = "✅" if st.session_state.wizard_step > 1 else "🔄" if st.session_state.wizard_step == 1 else "⭕"
        st.markdown(f"{emoji} **Step 1**: Clientela")
    with col2:
        emoji = "✅" if st.session_state.wizard_step > 2 else "🔄" if st.session_state.wizard_step == 2 else "⭕"
        st.markdown(f"{emoji} **Step 2**: Sezione")
    with col3:
        emoji = "✅" if st.session_state.wizard_step > 3 else "🔄" if st.session_state.wizard_step == 3 else "⭕"
        st.markdown(f"{emoji} **Step 3**: Template")
    with col4:
        emoji = "✅" if st.session_state.wizard_step > 4 else "🔄" if st.session_state.wizard_step == 4 else "⭕"
        st.markdown(f"{emoji} **Step 4**: Ingrediente")

    st.markdown("---")

    if st.session_state.wizard_step == 1:
        render_wizard_step_1()
    elif st.session_state.wizard_step == 2:
        render_wizard_step_2()
    elif st.session_state.wizard_step == 3:
        render_wizard_step_3()
    elif st.session_state.wizard_step == 4:
        render_wizard_step_4()

def render_wizard_step_1():
    """Step 1: Clientela selection with cards"""
    st.subheader("👥 Step 1: Scegli la tua clientela")
    st.markdown("*Seleziona il tipo di clienti che vuoi attrarre. Ogni segmento ha gusti e budget diversi.*")

    if not st.session_state.customers:
        st.error("Nessun dato clientela disponibile")
        return

    # Display customer cards in a grid
    cols = st.columns(3)
    for idx, customer in enumerate(st.session_state.customers[:9]):  # Show max 9 customers
        with cols[idx % 3]:
            # Create customer card
            with st.container():
                st.markdown("---")

                # Customer name and emoji
                customer_emojis = {
                    "Gourmet": "🍷", "Families": "👨‍👩‍👧‍👦", "Students": "🎓",
                    "Workers": "💼", "Tourists": "🎒", "Seniors": "👴",
                    "Health": "🥗", "Vegetarian": "🌱", "Fast": "⚡"
                }
                emoji = customer_emojis.get(customer['name'], "👤")
                st.markdown(f"### {emoji} {customer['name']}")

                # Key preferences
                fav_tags = customer.get('favourite_tags', [])[:2]  # Show top 2
                if fav_tags:
                    st.markdown(f"**Preferisce**: {', '.join(fav_tags)}")

                # Price vs Quality focus
                price_weight = customer.get('price_score_weight', 0)
                eval_weight = customer.get('evaluation_score_weight', 0)

                if price_weight > eval_weight:
                    st.markdown("💰 **Focus**: Prezzo conveniente")
                elif eval_weight > price_weight:
                    st.markdown("⭐ **Focus**: Alta qualità")
                else:
                    st.markdown("⚖️ **Focus**: Equilibrato")

                # Selection button
                if st.button(f"Scegli {customer['name']}", key=f"select_customer_{idx}"):
                    st.session_state.wizard_customer = customer['name']
                    st.session_state.wizard_step = 2
                    st.rerun()

    # Back to menu button
    st.markdown("---")
    if st.button("🔙 Torna al Menu Principale"):
        st.session_state.show_wizard = False
        st.rerun()

def render_wizard_step_2():
    """Step 2: Sezione selection"""
    st.subheader("🍽️ Step 2: Scegli la sezione del menu")
    st.markdown(f"*Per la clientela **{st.session_state.wizard_customer}**, seleziona che tipo di piatto vuoi creare*")

    # Get selected customer data
    customer = next((c for c in st.session_state.customers if c['name'] == st.session_state.wizard_customer), None)
    if not customer:
        st.error("Errore: cliente non trovato")
        return

    # Show available sections for this customer
    sections = customer.get('sections', {})
    if not sections:
        st.error("Nessuna sezione disponibile per questo cliente")
        return

    st.markdown("**Sezioni disponibili e budget atteso:**")

    # Display section cards
    cols = st.columns(2)
    section_names = {
        'Appetizer': '🥗 Antipasto',
        'MainCourse': '🍖 Piatto Principale',
        'Dessert': '🍰 Dessert',
        'Burger': '🍔 Burger'
    }

    for idx, (section, info) in enumerate(sections.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown("---")
                display_name = section_names.get(section, section)
                cost = info.get('cost_expectation', 0)
                probability = info.get('probability', 0)

                st.markdown(f"### {display_name}")
                st.markdown(f"💰 **Budget atteso**: €{cost:.2f}")
                st.markdown(f"📊 **Popolarità**: {probability:.0%}")

                if st.button(f"Scegli {display_name}", key=f"select_section_{section}"):
                    st.session_state.wizard_section = section
                    st.session_state.wizard_step = 3
                    st.rerun()

    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Torna al Step 1"):
            st.session_state.wizard_step = 1
            st.rerun()
    with col2:
        if st.button("❌ Esci dal Wizard"):
            st.session_state.show_wizard = False
            st.rerun()

def render_wizard_step_3():
    """Step 3: Template selection"""
    st.subheader("📋 Step 3: Scegli il template di ricetta")
    st.markdown(f"*Cliente: **{st.session_state.wizard_customer}** | Sezione: **{st.session_state.wizard_section}***")

    # Get available templates
    all_templates = get_all_templates()
    unlocked = st.session_state.unlocked_templates

    # Filter compatible templates for the section
    compatible_templates = []
    section_compatible = {
        'Appetizer': ['Salad', 'Sautéed Veggies', 'Grilled Veggies'],
        'MainCourse': ['Pasta', 'Grilled Meat', 'Grilled Fish', 'Risotto'],
        'Dessert': ['Pie', 'Cookies', 'Ice Cream'],
        'Burger': ['Hamburger', 'Fish Burger', 'Veggie Burger']
    }

    preferred_for_section = section_compatible.get(st.session_state.wizard_section, [])

    # Show unlocked templates first
    st.markdown("**✅ Template già sbloccati:**")
    unlocked_shown = False

    for template in all_templates:
        if template.name in unlocked:
            if template.name in preferred_for_section or not preferred_for_section:
                unlocked_shown = True
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{template.name}** ({template.category})")
                    st.markdown(f"*{get_template_description(template.name)}*")
                with col2:
                    if st.button(f"Scegli", key=f"select_template_{template.name}"):
                        st.session_state.wizard_template = template.name
                        st.session_state.wizard_step = 4
                        st.rerun()

    if not unlocked_shown:
        st.info("Nessun template sbloccato compatibile. Sblocca template nella sezione Esperto.")

    # Show locked templates with unlock option
    st.markdown("**🔒 Template da sbloccare:**")

    budget = st.session_state.available_points
    st.markdown(f"*Punti disponibili: {budget}*")

    for template in all_templates[:6]:  # Show first 6 locked templates
        if template.name not in unlocked:
            if template.name in preferred_for_section or not preferred_for_section:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{template.name}** ({template.category})")
                    st.markdown(f"*Costo: {template.points} punti*")
                with col2:
                    can_afford = template.points <= budget
                    if can_afford:
                        if st.button(f"Sblocca ({template.points}p)", key=f"unlock_{template.name}"):
                            st.session_state.unlocked_templates.append(template.name)
                            st.session_state.available_points -= template.points
                            st.success(f"✅ {template.name} sbloccato!")
                            st.rerun()
                    else:
                        st.markdown(f"❌ Servono {template.points}p")
                with col3:
                    if template.name in st.session_state.unlocked_templates:
                        if st.button(f"Scegli", key=f"select_locked_{template.name}"):
                            st.session_state.wizard_template = template.name
                            st.session_state.wizard_step = 4
                            st.rerun()

    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Torna al Step 2"):
            st.session_state.wizard_step = 2
            st.rerun()
    with col2:
        if st.button("❌ Esci dal Wizard"):
            st.session_state.show_wizard = False
            st.rerun()

def render_wizard_step_4():
    """Step 4: Ingrediente selection and recipe generation"""
    st.subheader("🥘 Step 4: Scegli l'ingrediente principale")
    st.markdown(f"*Cliente: **{st.session_state.wizard_customer}** | Sezione: **{st.session_state.wizard_section}** | Template: **{st.session_state.wizard_template}***")

    # Ingredient search
    search_term = st.text_input("🔍 Cerca ingrediente", placeholder="Inizia a scrivere...", key="wizard_ingredient_search")

    # Get compatible ingredients
    if search_term:
        matching_ingredients = search_ingredients(st.session_state.ingredients, search_term)[:10]

        if matching_ingredients:
            st.markdown("**Ingredienti trovati:**")

            cols = st.columns(2)
            for idx, ingredient in enumerate(matching_ingredients):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown("---")

                        # Ingredient info
                        tags = ingredient.get('tags', [])[:3]  # Show first 3 tags
                        st.markdown(f"**{ingredient['name']}**")
                        if tags:
                            st.markdown(f"🏷️ {', '.join(tags)}")

                        # Quality costs
                        costs = ingredient.get('quality_costs', {})
                        normal_cost = costs.get('NORMAL', {}).get('unit_cost', 0)
                        st.markdown(f"💰 Da €{normal_cost:.1f}")

                        # Check template compatibility
                        compatibility = check_template_compatibility(st.session_state.wizard_template, ingredient)
                        if compatibility['compatible']:
                            status_color = "🟢"
                            status_text = "Compatibile"
                        elif compatibility['warnings']:
                            status_color = "🟡"
                            status_text = "Con avvisi"
                        else:
                            status_color = "🔴"
                            status_text = "Incompatibile"

                        st.markdown(f"{status_color} {status_text}")

                        # Select button
                        if st.button(f"Scegli {ingredient['name']}", key=f"select_ingredient_{idx}"):
                            st.session_state.wizard_ingredient = ingredient['name']
                            # Auto-generate variants
                            generate_wizard_variants()
                            st.rerun()
        else:
            st.info("Nessun ingrediente trovato. Prova con un altro termine.")
    else:
        st.info("Inizia a digitare per cercare ingredienti...")

    # Show generated variants if available
    if hasattr(st.session_state, 'wizard_variants') and st.session_state.wizard_variants:
        st.markdown("---")
        st.subheader("🍽️ Le tue ricette generate!")

        for i, variant in enumerate(st.session_state.wizard_variants):
            with st.expander(f"{variant.style.title()} - ⭐{variant.stars:.1f} - €{variant.price:.2f}", expanded=i==0):

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Ingredienti:**")
                    for ingredient, role in variant.roles.items():
                        st.markdown(f"• {ingredient} _{format_role_display(role)}_")

                with col2:
                    st.markdown("**Dettagli:**")
                    st.markdown(f"⭐ Rating: {variant.stars:.1f}/5.0")
                    st.markdown(f"💰 Prezzo: €{variant.price:.2f}")
                    st.markdown(f"🎯 Segment Fit: {variant.segment_fit:.0f}%")
                    st.markdown(f"🧪 Ingredienti: {len(variant.ingredients)}")

                # Add to menu button
                if st.button(f"📋 Aggiungi al Menu", key=f"add_variant_{i}"):
                    # Convert variant to menu item format
                    menu_item = {
                        'template': st.session_state.wizard_template,
                        'section': st.session_state.wizard_section,
                        'customer': st.session_state.wizard_customer,
                        'anchor': st.session_state.wizard_ingredient,
                        'style': variant.style,
                        'ingredients': variant.ingredients,
                        'roles': variant.roles,
                        'tiers': variant.tiers,
                        'stars': variant.stars,
                        'price': variant.price,
                        'cost': variant.cost,
                        'segment_fit': variant.segment_fit,
                        'tag_set': variant.tag_set,
                        'notes': f"Generato dal Quick Start Wizard"
                    }
                    st.session_state.menu_items.append(menu_item)
                    st.success(f"✅ Ricetta {variant.style} aggiunta al menu!")

                    # Reset wizard and return to main view
                    st.session_state.show_wizard = False
                    st.session_state.wizard_step = 1
                    st.session_state.wizard_customer = None
                    st.session_state.wizard_section = None
                    st.session_state.wizard_template = None
                    st.session_state.wizard_ingredient = None
                    if hasattr(st.session_state, 'wizard_variants'):
                        del st.session_state.wizard_variants
                    st.rerun()

    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Torna al Step 3"):
            st.session_state.wizard_step = 3
            st.rerun()
    with col2:
        if st.button("❌ Esci dal Wizard"):
            st.session_state.show_wizard = False
            st.rerun()

def generate_wizard_variants():
    """Generate variants for the wizard"""
    if not all([st.session_state.wizard_customer, st.session_state.wizard_section,
                st.session_state.wizard_template, st.session_state.wizard_ingredient]):
        return

    # Find customer and ingredient objects
    customer = next((c for c in st.session_state.customers if c['name'] == st.session_state.wizard_customer), None)
    ingredient = find_ingredient_by_name(st.session_state.ingredients, st.session_state.wizard_ingredient)

    if customer and ingredient:
        try:
            variants = generate_variants(
                segment=st.session_state.wizard_customer,
                section=st.session_state.wizard_section,
                template=st.session_state.wizard_template,
                anchor_ingredient=ingredient,
                customers_data=st.session_state.customers,
                ingredients_data=st.session_state.ingredients,
                matches_lookup=st.session_state.matches_lookup
            )
            st.session_state.wizard_variants = variants
        except Exception as e:
            st.error(f"Errore nella generazione: {str(e)}")


# ====== NEW TAB FUNCTIONS (MVP 0.3.1) ======

def render_dashboard_tab():
    """Main dashboard with overview and quick actions"""
    st.header("🏠 Dashboard")

    # Quick stats
    n_items = len(st.session_state.menu_items)
    if n_items > 0:
        # Get current customer context
        current_customer = None
        if 'selected_customer' in st.session_state and st.session_state.customers:
            customer_name = st.session_state.selected_customer
            current_customer = next((c for c in st.session_state.customers if c['name'] == customer_name), None)

        # Calculate basic KPIs
        kpis = menu_kpis(st.session_state.menu_items, current_customer or {}, {})

        # Stats cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🍽️ Ricette", n_items)
        with col2:
            st.metric("⭐ Rating Medio", f"{kpis['avg_stars']:.1f}")
        with col3:
            st.metric("💰 Prezzo Medio", f"€{kpis['median_price']:.2f}")
        with col4:
            complexity = kpis['complexity_stats']['avg']
            st.metric("🔧 Complessità", f"{complexity:.1f} ing")

        # Quick actions
        st.subheader("⚡ Azioni Rapide")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 Nuova Ricetta", type="primary"):
                st.session_state.show_wizard = True
                st.rerun()

        with col2:
            if st.button("📊 Analisi Menu"):
                st.info("Vai al tab 'Menu Builder' per l'analisi completa")

        with col3:
            if st.button("📤 Esporta Menu"):
                if st.session_state.menu_items:
                    st.info("Vai al tab 'Menu Builder' per le opzioni di export")
                else:
                    st.warning("Menu vuoto - niente da esportare")

        # Recent recipes
        st.subheader("📋 Ricette Recenti")
        for i, item in enumerate(st.session_state.menu_items[-5:]):  # Show last 5
            with st.expander(f"{item.get('template', 'Unknown')} con {item.get('anchor', 'N/A')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Sezione**: {item.get('section', 'N/A')}")
                    st.markdown(f"**Cliente**: {item.get('customer', 'N/A')}")
                    st.markdown(f"**Stile**: {item.get('style', 'classico').title()}")
                with col2:
                    st.markdown(f"**Rating**: ⭐{item.get('stars', 0):.1f}")
                    st.markdown(f"**Prezzo**: €{item.get('price', 0):.2f}")
                    st.markdown(f"**Fit**: {item.get('segment_fit', 0):.0f}%")

    else:
        # Empty state
        st.info("👋 **Benvenuto in Chef Planner!**")
        st.markdown("""
        Il tuo menu è vuoto. Ecco cosa puoi fare:

        1. 🚀 **Quick Start**: Crea la tua prima ricetta in 4 step guidati
        2. 🧪 **Recipe Studio**: Crea ricette avanzate con controllo totale
        3. 👨‍💼 **Modalità Esperto**: Accedi a tutte le funzionalità avanzate
        """)

        if st.button("🎯 Inizia Quick Start", type="primary", help="Consigliato per nuovi utenti"):
            st.session_state.show_wizard = True
            st.rerun()

def render_recipe_studio_tab():
    """Recipe Studio for single recipe editing with 2-column layout"""
    st.header("🧪 Recipe Studio")
    st.markdown("*Crea e modifica ricette con controllo completo*")

    if not st.session_state.data_loaded:
        st.warning("⚠️ Carica prima i dati dal sidebar")
        return

    # 2-column layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("⚙️ Configurazione")

        # Customer selection
        customer_options = [c['name'] for c in st.session_state.customers]
        if customer_options:
            selected_customer = st.selectbox(
                "👥 Cliente Target",
                customer_options,
                key="studio_customer",
                help="Seleziona il segmento di clientela per questa ricetta"
            )

            # Section selection based on customer
            customer = next((c for c in st.session_state.customers if c['name'] == selected_customer), None)
            if customer:
                section_options = list(customer.get('sections', {}).keys())
                section_names = {
                    'Appetizer': '🥗 Antipasto',
                    'MainCourse': '🍖 Piatto Principale',
                    'Dessert': '🍰 Dessert',
                    'Burger': '🍔 Burger'
                }

                if section_options:
                    selected_section = st.selectbox(
                        "🍽️ Sezione Menu",
                        section_options,
                        format_func=lambda x: section_names.get(x, x),
                        key="studio_section"
                    )

                    # Show expected cost for this segment/section
                    section_info = customer['sections'].get(selected_section, {})
                    expected_cost = section_info.get('cost_expectation', 0)
                    st.info(f"💰 Budget atteso per {selected_customer}: €{expected_cost:.2f}")

                    # Template selection
                    all_templates = get_all_templates()
                    unlocked_templates = [t for t in all_templates if t.name in st.session_state.unlocked_templates]

                    if unlocked_templates:
                        template_names = [t.name for t in unlocked_templates]
                        selected_template = st.selectbox(
                            "📋 Template",
                            template_names,
                            key="studio_template",
                            help="Template di ricetta (solo quelli sbloccati)"
                        )

                        # Template description
                        st.markdown(f"*{get_template_description(selected_template)}*")

                        # Ingredient search
                        st.subheader("🥘 Ingrediente Principale")
                        ingredient_search = st.text_input(
                            "🔍 Cerca ingrediente",
                            placeholder="Inizia a scrivere...",
                            key="studio_ingredient_search"
                        )

                        selected_ingredient = None
                        if ingredient_search:
                            matching = search_ingredients(st.session_state.ingredients, ingredient_search)[:5]
                            if matching:
                                ingredient_names = [ing['name'] for ing in matching]
                                selected_ingredient_name = st.selectbox(
                                    "Scegli ingrediente",
                                    ingredient_names,
                                    key="studio_ingredient"
                                )
                                selected_ingredient = next((ing for ing in matching if ing['name'] == selected_ingredient_name), None)

                                # Show compatibility check
                                if selected_ingredient:
                                    compatibility = check_template_compatibility(selected_template, selected_ingredient)
                                    if compatibility['compatible']:
                                        st.success("✅ Combinazione compatibile")
                                    elif compatibility['warnings']:
                                        st.warning("⚠️ " + ", ".join(compatibility['warnings']))
                                    else:
                                        st.error("❌ Combinazione non compatibile")

                        # Generate button
                        if selected_ingredient:
                            if st.button("🎨 Genera Ricette", type="primary"):
                                try:
                                    variants = generate_variants(
                                        segment=selected_customer,
                                        section=selected_section,
                                        template=selected_template,
                                        anchor_ingredient=selected_ingredient,
                                        customers_data=st.session_state.customers,
                                        ingredients_data=st.session_state.ingredients,
                                        matches_lookup=st.session_state.matches_lookup
                                    )
                                    st.session_state.studio_variants = variants
                                    st.success(f"✅ Generate {len(variants)} varianti!")
                                except Exception as e:
                                    st.error(f"Errore: {str(e)}")

                    else:
                        st.warning("🔒 Nessun template sbloccato. Vai al tab 'Esperto' per sbloccare template.")

    with col2:
        st.subheader("🍽️ Anteprima Ricette")

        # Show generated variants
        if hasattr(st.session_state, 'studio_variants') and st.session_state.studio_variants:
            for i, variant in enumerate(st.session_state.studio_variants):
                with st.expander(f"✨ {variant.style.title()}", expanded=i==0):

                    # Variant stats
                    col2a, col2b = st.columns(2)
                    with col2a:
                        st.markdown(f"⭐ **Rating**: {variant.stars:.1f}/5.0")
                        st.markdown(f"💰 **Prezzo**: €{variant.price:.2f}")
                    with col2b:
                        st.markdown(f"🎯 **Segment Fit**: {variant.segment_fit:.0f}%")
                        st.markdown(f"🧪 **Ingredienti**: {len(variant.ingredients)}")

                    # Ingredient list with roles
                    st.markdown("**Ingredienti:**")
                    for ingredient, role in variant.roles.items():
                        role_display = format_role_display(role)
                        st.markdown(f"• **{ingredient}** _{role_display}_")

                    # Quality tiers
                    st.markdown("**Qualità Ingredienti:**")
                    tier_display = []
                    for ing, tier in variant.tiers.items():
                        tier_name = get_tier_display_name(tier)
                        tier_display.append(f"{ing}: {tier_name}")
                    st.markdown(", ".join(tier_display[:3]) + ("..." if len(tier_display) > 3 else ""))

                    # Add to menu
                    if st.button(f"📋 Aggiungi al Menu", key=f"studio_add_{i}"):
                        menu_item = {
                            'template': st.session_state.studio_template,
                            'section': st.session_state.studio_section,
                            'customer': st.session_state.studio_customer,
                            'anchor': st.session_state.studio_ingredient,
                            'style': variant.style,
                            'ingredients': variant.ingredients,
                            'roles': variant.roles,
                            'tiers': variant.tiers,
                            'stars': variant.stars,
                            'price': variant.price,
                            'cost': variant.cost,
                            'segment_fit': variant.segment_fit,
                            'tag_set': variant.tag_set,
                            'notes': f"Creato in Recipe Studio"
                        }
                        st.session_state.menu_items.append(menu_item)
                        st.success(f"✅ Ricetta {variant.style} aggiunta al menu!")

        else:
            st.info("👆 Configura i parametri a sinistra e genera le ricette per vederle qui")

        # Quick help
        with st.expander("💡 Come usare Recipe Studio"):
            st.markdown("""
            **Recipe Studio** ti dà controllo completo sulla creazione di ricette:

            1. **Scegli cliente**: Definisce gusti e budget
            2. **Seleziona sezione**: Determina il tipo di piatto
            3. **Scegli template**: La base della ricetta
            4. **Trova ingrediente**: L'elemento principale
            5. **Genera & Aggiungi**: Crea varianti e salvale nel menu

            💡 **Suggerimento**: Usa il Quick Start per ricette veloci, Recipe Studio per controllo avanzato!
            """)

def render_simplified_menu_builder_tab():
    """Simplified Menu Builder with essential KPIs and management"""
    st.header("🎯 Menu Builder")
    st.markdown("*Il tuo menu completo con analisi essenziali*")

    menu_items = st.session_state.menu_items
    if not menu_items:
        st.info("📋 **Il tuo menu è vuoto**")
        st.markdown("Crea la tua prima ricetta usando:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Quick Start", type="primary"):
                st.session_state.show_wizard = True
                st.rerun()
        with col2:
            if st.button("🧪 Recipe Studio"):
                st.info("Vai al tab 'Recipe Studio'")
        return

    # Get current customer context
    current_customer = None
    current_segment_name = "Generale"
    if 'selected_customer' in st.session_state and st.session_state.customers:
        customer_name = st.session_state.selected_customer
        current_customer = next((c for c in st.session_state.customers if c['name'] == customer_name), None)
        current_segment_name = customer_name

    # Calculate KPIs
    sections_meta = {}
    if current_customer:
        sections_meta = current_customer.get('sections', {})

    kpis = menu_kpis(menu_items, current_customer or {}, sections_meta)
    warnings = variety_warnings(menu_items, current_customer or {})
    health_score = menu_health_score(kpis, len(warnings))

    # Header with key stats
    col1, col2, col3 = st.columns(3)
    with col1:
        color = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
        st.metric("🏆 Menu Health", f"{color} {health_score}/100")
    with col2:
        st.metric("🍽️ Ricette", len(menu_items))
    with col3:
        st.metric("⭐ Rating Medio", f"{kpis['avg_stars']:.1f}/5.0")

    st.markdown("---")

    # Essential KPIs
    st.subheader("📊 KPIs Essenziali")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        fit_color = "🟢" if kpis['avg_fit_total'] >= 80 else "🟡" if kpis['avg_fit_total'] >= 60 else "🔴"
        st.metric("🎯 Segment Fit", f"{kpis['avg_fit_total']:.0f}%", help=f"{fit_color} Adattamento al segmento {current_segment_name}")

    with kpi_col2:
        st.metric("💰 Prezzo Mediano", f"€{kpis['median_price']:.2f}", help="Prezzo tipico nel menu")

    with kpi_col3:
        price_color = "🟢" if kpis['avg_price_deviation_pct'] <= 10 else "🟡" if kpis['avg_price_deviation_pct'] <= 20 else "🔴"
        st.metric("📊 Coerenza Prezzi", f"{kpis['avg_price_deviation_pct']:.0f}%", help=f"{price_color} Deviazione dai target")

    with kpi_col4:
        complexity = kpis['complexity_stats']['avg']
        st.metric("🔧 Complessità Media", f"{complexity:.1f} ing", help="Media ingredienti per ricetta")

    # Warnings (if any)
    if warnings:
        st.subheader("⚠️ Raccomandazioni")
        for warning in warnings[:3]:  # Show top 3 warnings
            st.warning(warning)

    # Quick menu management
    st.subheader("🛠️ Gestione Rapida")

    # Simple recipe list
    for i, item in enumerate(menu_items):
        with st.expander(f"{i+1}. {item.get('template', 'Unknown')} con {item.get('anchor', 'N/A')}", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**Sezione**: {item.get('section', 'N/A')}")
                st.markdown(f"**Cliente**: {item.get('customer', 'N/A')}")
                st.markdown(f"**Stile**: {item.get('style', 'classico').title()}")
                st.markdown(f"**Note**: {item.get('notes', 'Nessuna nota')}")

            with col2:
                st.markdown(f"⭐ {item.get('stars', 0):.1f}/5.0")
                st.markdown(f"💰 €{item.get('price', 0):.2f}")
                st.markdown(f"🎯 {item.get('segment_fit', 0):.0f}%")

            with col3:
                # Simple actions
                if st.button("🗑️", key=f"delete_simple_{i}", help="Elimina ricetta"):
                    st.session_state.menu_items.pop(i)
                    st.rerun()

    # Export section
    st.markdown("---")
    st.subheader("📤 Esporta Menu")

    if menu_items:
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = export_menu_csv(menu_items)
            filename_csv = get_export_filename('csv', current_segment_name)
            st.download_button(
                label="📊 CSV per Excel",
                data=csv_data,
                file_name=filename_csv,
                mime="text/csv"
            )

        with col2:
            json_data = export_menu_json(menu_items)
            filename_json = get_export_filename('json', current_segment_name)
            st.download_button(
                label="🔧 JSON Tecnico",
                data=json_data,
                file_name=filename_json,
                mime="application/json"
            )

        with col3:
            if current_customer:
                recommendations = unlock_recommendations(menu_items, current_customer, st.session_state.available_points, st.session_state.unlocked_templates)[:3]
            else:
                recommendations = []

            report_data = export_report_text(menu_items, kpis, warnings, recommendations, current_segment_name)
            filename_report = get_export_filename('report', current_segment_name)
            st.download_button(
                label="📋 Report Completo",
                data=report_data,
                file_name=filename_report,
                mime="text/plain"
            )
    else:
        st.warning("Menu vuoto - niente da esportare")

def render_expert_tab():
    """Expert tab with all advanced features moved from original interface"""
    st.header("👨‍💼 Modalità Esperto")
    st.markdown("*Tutte le funzionalità avanzate per utenti esperti*")

    if not st.session_state.data_loaded:
        st.warning("⚠️ Carica prima i dati dal sidebar")
        return

    # Sub-tabs for expert features
    expert_tab1, expert_tab2, expert_tab3 = st.tabs(["🔧 Configurazione Avanzata", "📊 Analytics Avanzate", "🥕 Database Ingredienti"])

    with expert_tab1:
        render_expert_configurator()

    with expert_tab2:
        render_expert_analytics()

    with expert_tab3:
        render_expert_ingredients()

def render_expert_configurator():
    """Advanced configurator (original Configurator tab functionality)"""
    st.subheader("🔧 Configurazione Avanzata")

    # This will contain the original render_configurator_tab() functionality
    # For now, call the original function
    render_configurator_tab()

def render_expert_analytics():
    """Advanced analytics (original Menu Preview advanced features)"""
    st.subheader("📊 Analytics Avanzate")

    # This will contain the original render_menu_preview_tab() functionality
    # For now, call the original function
    render_menu_preview_tab()

def render_expert_ingredients():
    """Ingredients database (original Ingredients tab)"""
    st.subheader("🥕 Database Ingredienti & Compatibilità")

    # This will contain the original render_ingredients_tab() functionality
    # For now, call the original function
    render_ingredients_tab()


def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()

    # App header
    st.title("👨‍🍳 Chef Planner MVP 0.3.1")
    st.markdown("*Menu builder rinnovato: più semplice, guidato e professionale*")

    # Render sidebar
    render_sidebar()

    # Show wizard if enabled
    if st.session_state.show_wizard:
        render_quick_start_wizard()
        return

    # Welcome section for new users
    if not st.session_state.data_loaded:
        st.info("👋 **Benvenuto in Chef Planner!** Carica i dati dal sidebar per iniziare.")
        return

    if len(st.session_state.menu_items) == 0:
        st.success("🚀 **Pronto per iniziare?** Clicca sul pulsante qui sotto per creare la tua prima ricetta!")
        if st.button("🎯 Inizia Quick Start", type="primary", help="Wizard guidato in 4 step"):
            st.session_state.show_wizard = True
            st.rerun()
        st.markdown("---")

    # Main content tabs - New structure
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🧪 Recipe Studio", "🎯 Menu Builder", "👨‍💼 Esperto"])

    with tab1:
        render_dashboard_tab()

    with tab2:
        render_recipe_studio_tab()

    with tab3:
        render_simplified_menu_builder_tab()

    with tab4:
        render_expert_tab()

    # Footer
    st.markdown("---")
    st.markdown("*Chef Planner MVP 0.3.1 - UI Refactor: semplice, guidato, professionale*")

if __name__ == "__main__":
    main()