import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import numpy as np
from collections import defaultdict, Counter

# Configurazione pagina
st.set_page_config(
    page_title="Chef Game - Generatore Menu Intelligente",
    page_icon="🍽️",
    layout="wide"
)

@st.cache_data
def load_data():
    """Carica tutti i dati JSON"""
    with open('customer_types.json', 'r', encoding='utf-8') as f:
        customers = json.load(f)

    with open('recipes_database.json', 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    with open('ingredients_data.json', 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    with open('matches_data.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)

    return customers, recipes, ingredients, matches

def calculate_recipe_appeal(recipe, customer_type, customer_data):
    """Calcola l'appeal di una ricetta per un tipo di cliente"""
    score = 0

    # Score base dalla valutazione
    base_score = recipe.get('evaluation_base', 50) / 100
    score += base_score * customer_data.get('evaluation_score_weight', 0.5)

    # Score prezzo (inverso per i cheapskate)
    price_score = 1 - (recipe.get('estimated_cost', 5) / 20)  # Normalizza a max 20€
    if customer_type == 'Cheapskate':
        price_score = 1 - price_score  # Inverti per cheapskate
    score += price_score * customer_data.get('price_score_weight', 0.5)

    # Score tag preferiti
    recipe_tags = set()
    for ingredient in recipe.get('ingredients', []):
        ingredient_name = ingredient['name'].replace('Tier1', '').replace('Tier2', '').replace('Tier3', '')
        # Trova i tag dell'ingrediente
        for ing_data in ingredients:
            if ingredient_name in ing_data['name']:
                recipe_tags.update(ing_data.get('tags', []))
                break

    tag_score = 0
    favorite_tags = customer_data.get('favourite_tags', [])
    secondary_tags = customer_data.get('secondary_favourite_tags', [])

    for tag in favorite_tags:
        if tag in recipe_tags:
            tag_score += 1

    for tag in secondary_tags:
        if tag in recipe_tags:
            tag_score += 0.5

    if favorite_tags or secondary_tags:
        tag_score = tag_score / (len(favorite_tags) + len(secondary_tags) * 0.5)

    score += tag_score * customer_data.get('tag_score_weight', 0.3)

    # Compatibilità ingredienti
    compatibility_score = recipe.get('compatibility_score', 2.5) / 5
    score += compatibility_score * 0.2

    return min(score, 1.0)  # Cap a 1.0

def generate_menu_for_customer(customer_type, recipes_by_section, customer_data):
    """Genera un menù ottimizzato per un tipo di cliente"""
    menu = {}
    total_cost = 0

    # Sezioni del menù in ordine di priorità
    sections = ['Appetizer', 'Salad', 'Soup', 'MainCourse', 'SideDish', 'Dessert']

    for section in sections:
        if section not in recipes_by_section or not recipes_by_section[section]:
            continue

        # Calcola appeal per tutte le ricette della sezione
        recipe_appeals = []
        for recipe in recipes_by_section[section]:
            appeal = calculate_recipe_appeal(recipe, customer_type, customer_data)
            recipe_appeals.append((recipe, appeal))

        # Ordina per appeal e prendi le migliori
        recipe_appeals.sort(key=lambda x: x[1], reverse=True)

        # Seleziona 2-4 ricette per sezione
        num_recipes = min(random.randint(2, 4), len(recipe_appeals))
        selected_recipes = [recipe for recipe, _ in recipe_appeals[:num_recipes]]

        menu[section] = selected_recipes
        total_cost += sum(recipe.get('estimated_cost', 0) for recipe in selected_recipes)

    return menu, total_cost

def display_recipe_card(recipe):
    """Mostra una carta ricetta con dettagli"""
    with st.container():
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"🍽️ {recipe.get('descriptive_name', recipe['name'])}")
            st.write(f"**Categoria:** {recipe.get('menu_section', 'N/A')}")
            st.write(f"**Tier:** {recipe.get('tier', 1)}")

            # Ingredienti
            if 'ingredients' in recipe and recipe['ingredients']:
                st.write("**Ingredienti:**")
                for ingredient in recipe['ingredients']:
                    category_icon = "⭐" if ingredient.get('category') == 'IMPORTANT' else "•"
                    st.write(f"{category_icon} {ingredient['name']} ({ingredient['quantity']})")

        with col2:
            # Metriche
            col2a, col2b = st.columns(2)
            with col2a:
                st.metric("Costo", f"€{recipe.get('estimated_cost', 0):.2f}")
                st.metric("Valutazione", f"{recipe.get('evaluation_base', 50)}/100")
            with col2b:
                st.metric("Compatibilità", f"{recipe.get('compatibility_score', 2.5):.1f}/5")
                st.metric("Tempo", f"{recipe.get('eating_time', 300)/60:.0f} min")

def main():
    st.title("🍽️ Chef Game - Generatore Menu Intelligente")
    st.markdown("### Crea menù personalizzati in base alla clientela del tuo ristorante")

    # Carica dati
    try:
        customers, recipes, ingredients, matches = load_data()
    except FileNotFoundError as e:
        st.error(f"❌ Errore nel caricamento dei file: {e}")
        st.info("Assicurati che tutti i file JSON siano nella stessa directory dell'app.")
        return

    # Ricette già organizzate per sezione
    recipes_by_section = recipes.get('recipes_by_section', {})

    # Sidebar per controlli
    st.sidebar.header("🎛️ Configurazione Menu")

    # Selezione tipo cliente
    customer_names = [customer['name'] for customer in customers['customer_types']]
    selected_customer = st.sidebar.selectbox(
        "Tipo di Clientela",
        customer_names,
        help="Seleziona il tipo di clientela predominante del tuo ristorante"
    )

    # Trova dati cliente selezionato
    customer_data = None
    for customer in customers['customer_types']:
        if customer['name'] == selected_customer:
            customer_data = customer
            break

    # Opzioni aggiuntive
    st.sidebar.subheader("⚙️ Opzioni Avanzate")
    max_cost = st.sidebar.slider("Budget Massimo per Ricetta (€)", 1.0, 20.0, 10.0, 0.5)
    min_quality = st.sidebar.selectbox("Qualità Minima", ["NORMAL", "FIRST_CHOICE", "GOURMET"])
    show_stats = st.sidebar.checkbox("Mostra Statistiche Avanzate", value=True)

    # Bottone genera menù
    if st.sidebar.button("🎲 Genera Menu Personalizzato", type="primary"):
        st.session_state.generate_menu = True

    # Layout principale
    if hasattr(st.session_state, 'generate_menu') and st.session_state.generate_menu:

        # Genera menù
        menu, total_cost = generate_menu_for_customer(
            selected_customer,
            recipes_by_section,
            customer_data
        )

        # Header risultati
        st.header(f"📋 Menu Personalizzato per: {selected_customer}")

        # Metriche generali
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Costo Totale Menu", f"€{total_cost:.2f}")
        with col2:
            total_recipes = sum(len(recipes) for recipes in menu.values())
            st.metric("Ricette Totali", total_recipes)
        with col3:
            avg_cost = total_cost / total_recipes if total_recipes > 0 else 0
            st.metric("Costo Medio Ricetta", f"€{avg_cost:.2f}")
        with col4:
            sections_count = len([s for s in menu.values() if s])
            st.metric("Sezioni Menu", sections_count)

        # Mostra profilo cliente
        if show_stats:
            with st.expander(f"📊 Profilo Cliente: {selected_customer}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Tag Preferiti:**")
                    for tag in customer_data.get('favourite_tags', []):
                        st.write(f"💚 {tag}")

                    st.write("**Tag Secondari:**")
                    for tag in customer_data.get('secondary_favourite_tags', []):
                        st.write(f"💛 {tag}")

                with col2:
                    st.write("**Pesi di Valutazione:**")
                    st.write(f"Prezzo: {customer_data.get('price_score_weight', 0):.1f}")
                    st.write(f"Qualità: {customer_data.get('evaluation_score_weight', 0):.1f}")
                    st.write(f"Tag: {customer_data.get('tag_score_weight', 0):.1f}")

                    # Grafico radar delle preferenze
                    categories = ['Prezzo', 'Qualità', 'Tag']
                    values = [
                        customer_data.get('price_score_weight', 0),
                        customer_data.get('evaluation_score_weight', 0),
                        customer_data.get('tag_score_weight', 0)
                    ]

                    fig = go.Figure(data=go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=selected_customer
                    ))

                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )),
                        showlegend=False,
                        title="Priorità Cliente",
                        height=300
                    )

                    st.plotly_chart(fig, use_container_width=True)

        # Mostra menu per sezioni
        sections_display = {
            'Appetizer': '🥗 Antipasti',
            'Salad': '🥬 Insalate',
            'Soup': '🍲 Zuppe',
            'MainCourse': '🍖 Portate Principali',
            'SideDish': '🥔 Contorni',
            'Dessert': '🍰 Dessert'
        }

        for section, display_name in sections_display.items():
            if section in menu and menu[section]:
                st.subheader(display_name)

                # Crea tabs per ogni ricetta della sezione
                recipe_names = [recipe.get('descriptive_name', recipe['name'])[:30] for recipe in menu[section]]
                tabs = st.tabs(recipe_names)

                for i, (tab, recipe) in enumerate(zip(tabs, menu[section])):
                    with tab:
                        display_recipe_card(recipe)

                        # Bottone per dettagli ingredienti
                        if st.button(f"📝 Dettagli Ingredienti", key=f"details_{section}_{i}"):
                            st.write("**Analisi Ingredienti:**")

                            ingredient_costs = []
                            for ingredient in recipe.get('ingredients', []):
                                # Trova costo ingrediente
                                ingredient_name = ingredient['name'].replace('Tier1', '').replace('Tier2', '').replace('Tier3', '')
                                cost = 0

                                for ing_data in ingredients:
                                    if ingredient_name in ing_data['name']:
                                        quality_costs = ing_data.get('quality_costs', {})
                                        if 'NORMAL' in quality_costs:
                                            unit_cost = quality_costs['NORMAL'].get('unit_cost', 0)
                                            cost = unit_cost * ingredient['quantity']
                                        break

                                ingredient_costs.append({
                                    'Ingrediente': ingredient['name'],
                                    'Quantità': ingredient['quantity'],
                                    'Costo': cost,
                                    'Categoria': ingredient.get('category', 'NORMAL')
                                })

                            df_ingredients = pd.DataFrame(ingredient_costs)
                            st.dataframe(df_ingredients, use_container_width=True)

    else:
        # Pagina iniziale
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://via.placeholder.com/400x200/667eea/ffffff?text=Chef+Menu+Generator",
                    caption="Seleziona un tipo di clientela e genera il menu perfetto!")

        # Statistiche generali
        st.subheader("📈 Statistiche Database")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tipi di Clientela", len(customer_names))
        with col2:
            # Conta tutte le ricette in tutte le sezioni
            total_recipes = sum(len(section_recipes) for section_recipes in recipes_by_section.values())
            st.metric("Ricette Totali", total_recipes)
        with col3:
            st.metric("Ingredienti", len(ingredients))
        with col4:
            st.metric("Compatibilità", len(matches))

        # Grafico distribuzione ricette per categoria
        section_counts = {section: len(recipes_list) for section, recipes_list in recipes_by_section.items()}

        fig = px.pie(
            values=list(section_counts.values()),
            names=list(section_counts.keys()),
            title="Distribuzione Ricette per Categoria"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabella tipi di clientela
        st.subheader("👥 Tipi di Clientela Disponibili")

        customer_summary = []
        for customer in customers['customer_types']:
            customer_summary.append({
                'Tipo': customer['name'],
                'Tag Preferiti': ', '.join(customer.get('favourite_tags', [])[:3]),
                'Focus Prezzo': f"{customer.get('price_score_weight', 0):.1f}",
                'Focus Qualità': f"{customer.get('evaluation_score_weight', 0):.1f}"
            })

        df_customers = pd.DataFrame(customer_summary)
        st.dataframe(df_customers, use_container_width=True)

if __name__ == "__main__":
    main()