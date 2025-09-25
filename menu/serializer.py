"""
Menu Export and Serialization for Chef Planner MVP 0.3
Export functionality for CSV, JSON, and readable text reports.
"""

import json
import csv
from typing import List, Dict, Any
from io import StringIO
from datetime import datetime


def export_menu_csv(menu_items: List[Dict[str, Any]]) -> str:
    """
    Export menu to CSV format
    Returns CSV as string
    """
    if not menu_items:
        return "No menu items to export"

    output = StringIO()
    writer = csv.writer(output)

    # CSV Headers
    headers = [
        'ID', 'Nome', 'Template', 'Sezione', 'Segmento Cliente', 'Ingrediente Principale',
        'Stile', 'Rating (stelle)', 'Prezzo (€)', 'Costo (€)', 'Segment Fit (%)',
        'Numero Ingredienti', 'Ingredienti', 'Qualità Ingredienti', 'Note'
    ]
    writer.writerow(headers)

    # Data rows
    for i, item in enumerate(menu_items, 1):
        # Format ingredients list
        ingredients_str = ', '.join(item.get('ingredients', []))

        # Format tiers
        tiers = item.get('tiers', {})
        tiers_str = ', '.join([f"{ing}:{tier}" for ing, tier in tiers.items()]) if tiers else ''

        row = [
            i,  # ID
            f"{item.get('template', 'Unknown')} con {item.get('anchor', 'N/A')}",  # Nome
            item.get('template', 'Unknown'),  # Template
            item.get('section', 'N/A'),  # Sezione
            item.get('customer', 'N/A'),  # Segmento Cliente
            item.get('anchor', 'N/A'),  # Ingrediente Principale
            item.get('style', 'classico').title(),  # Stile
            f"{item.get('stars', 0):.1f}",  # Rating
            f"{item.get('price', 0):.2f}",  # Prezzo
            f"{item.get('cost', 0):.2f}",  # Costo
            f"{item.get('segment_fit', 0):.0f}",  # Segment Fit
            len(item.get('ingredients', [])),  # Numero Ingredienti
            ingredients_str,  # Ingredienti
            tiers_str,  # Qualità Ingredienti
            item.get('notes', '')  # Note
        ]
        writer.writerow(row)

    return output.getvalue()


def export_menu_json(menu_items: List[Dict[str, Any]]) -> str:
    """
    Export menu to JSON format
    Returns formatted JSON string
    """
    if not menu_items:
        return json.dumps({"menu_items": [], "exported_at": datetime.now().isoformat()}, indent=2)

    # Create export structure
    export_data = {
        "menu_info": {
            "total_items": len(menu_items),
            "exported_at": datetime.now().isoformat(),
            "format_version": "1.0"
        },
        "menu_items": []
    }

    for i, item in enumerate(menu_items):
        # Clean and structure each item
        export_item = {
            "id": i + 1,
            "name": f"{item.get('template', 'Unknown')} con {item.get('anchor', 'N/A')}",
            "template": item.get('template', 'Unknown'),
            "section": item.get('section', 'N/A'),
            "customer_segment": item.get('customer', 'N/A'),
            "anchor_ingredient": item.get('anchor', 'N/A'),
            "style": item.get('style', 'classico'),
            "rating": {
                "stars": round(item.get('stars', 0), 2),
                "segment_fit_pct": round(item.get('segment_fit', 0), 1)
            },
            "pricing": {
                "suggested_price": round(item.get('price', 0), 2),
                "total_cost": round(item.get('cost', 0), 2)
            },
            "ingredients": {
                "list": item.get('ingredients', []),
                "count": len(item.get('ingredients', [])),
                "roles": item.get('roles', {}),
                "tiers": item.get('tiers', {})
            },
            "notes": item.get('notes', ''),
            "tags": list(item.get('tag_set', set())) if isinstance(item.get('tag_set'), set) else item.get('tag_set', [])
        }

        # Add fit breakdown if available
        if item.get('fit_breakdown'):
            export_item["rating"]["fit_breakdown"] = item['fit_breakdown']

        export_data["menu_items"].append(export_item)

    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_report_text(menu_items: List[Dict[str, Any]], kpis: Dict[str, Any],
                      warnings: List[str], suggestions: List[Dict[str, Any]],
                      segment_name: str = "Sconosciuto") -> str:
    """
    Export comprehensive readable text report
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("🍽️  CHEF PLANNER - REPORT MENU COMPLETO")
    lines.append("=" * 70)
    lines.append(f"📅 Data export: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(f"👥 Segmento cliente: {segment_name}")
    lines.append(f"🍽️ Ricette nel menu: {kpis.get('n_items', 0)}")
    lines.append("")

    # Executive Summary
    lines.append("📊 RIEPILOGO ESECUTIVO")
    lines.append("-" * 30)
    health_score = menu_health_score(kpis, len(warnings))
    lines.append(f"🏆 Salute Menu: {health_score}/100")

    if health_score >= 80:
        lines.append("✅ Menu eccellente - pronto per il servizio!")
    elif health_score >= 60:
        lines.append("⚠️ Menu buono - piccoli miglioramenti raccomandati")
    else:
        lines.append("❌ Menu necessita miglioramenti significativi")

    lines.append("")

    # KPI Section
    lines.append("📈 INDICATORI CHIAVE DI PERFORMANCE")
    lines.append("-" * 40)
    lines.append(f"⭐ Rating medio: {kpis.get('avg_stars', 0):.1f}/5.0 stelle")
    lines.append(f"🎯 Segment Fit medio: {kpis.get('avg_fit_total', 0):.1f}%")
    lines.append(f"💰 Prezzo mediano: €{kpis.get('median_price', 0):.2f}")
    lines.append(f"📊 Deviazione prezzi: {kpis.get('avg_price_deviation_pct', 0):.1f}%")
    lines.append("")

    # Breakdown dettagliato
    lines.append("   Breakdown Fit per Categoria:")
    lines.append(f"   💶 Price Fit: {kpis.get('avg_fit_price', 0):.1f}%")
    lines.append(f"   🏷️ Tag Fit: {kpis.get('avg_fit_tags', 0):.1f}%")
    lines.append(f"   ⭐ Evaluation Fit: {kpis.get('avg_fit_eval', 0):.1f}%")
    lines.append("")

    # Section Coverage
    lines.append("🍽️ COPERTURA SEZIONI")
    lines.append("-" * 25)
    section_coverage = kpis.get('section_coverage', {})
    for section, info in section_coverage.items():
        count = info['count']
        actual_ratio = info['actual_ratio']
        expected_ratio = info['expected_ratio']
        status = "✅" if abs(actual_ratio - expected_ratio) <= 0.2 else "⚠️"
        lines.append(f"{status} {section}: {count} ricette ({actual_ratio:.1%}, atteso {expected_ratio:.1%})")

    lines.append("")

    # Tag Coverage
    lines.append("🏷️ COPERTURA TAG PREFERITI")
    lines.append("-" * 30)
    tag_coverage = kpis.get('tag_coverage', {})
    fav_coverage_pct = tag_coverage.get('favourite_coverage_pct', 0)
    lines.append(f"📋 Copertura tag preferiti: {fav_coverage_pct:.0f}%")

    missing_favourites = tag_coverage.get('missing_favourites', [])
    if missing_favourites:
        lines.append(f"❌ Tag preferiti mancanti: {', '.join(missing_favourites[:5])}")
    else:
        lines.append("✅ Tutti i tag preferiti sono coperti")

    lines.append("")

    # Complexity Analysis
    lines.append("🔧 ANALISI COMPLESSITÀ")
    lines.append("-" * 25)
    complexity = kpis.get('complexity_stats', {})
    lines.append(f"📊 Ingredienti per ricetta - Min: {complexity.get('min', 0)}, Media: {complexity.get('avg', 0):.1f}, Max: {complexity.get('max', 0)}")

    variety_desc = "equilibrata"
    avg_complexity = complexity.get('avg', 0)
    if avg_complexity < 4:
        variety_desc = "semplice"
    elif avg_complexity > 8:
        variety_desc = "complessa"

    lines.append(f"🎯 Complessità menu: {variety_desc}")
    lines.append("")

    # Menu Items Detail
    if menu_items:
        lines.append("🍽️ DETTAGLIO RICETTE")
        lines.append("-" * 25)

        for i, item in enumerate(menu_items, 1):
            name = f"{item.get('template', 'Unknown')} con {item.get('anchor', 'N/A')}"
            section = item.get('section', 'N/A')
            stars = item.get('stars', 0)
            price = item.get('price', 0)
            fit = item.get('segment_fit', 0)
            style = item.get('style', 'classico').title()

            lines.append(f"{i:2d}. {name}")
            lines.append(f"    📍 {section} | {style} | ⭐{stars:.1f} | €{price:.2f} | 🎯{fit:.0f}%")

            # Show ingredients with roles
            ingredients = item.get('ingredients', [])
            if len(ingredients) <= 6:
                lines.append(f"    🥘 {', '.join(ingredients)}")
            else:
                lines.append(f"    🥘 {', '.join(ingredients[:4])}... (+{len(ingredients)-4} altri)")

            lines.append("")

    # Warnings Section
    if warnings:
        lines.append("⚠️ AVVISI E RACCOMANDAZIONI")
        lines.append("-" * 35)
        for i, warning in enumerate(warnings, 1):
            lines.append(f"{i:2d}. {warning}")
        lines.append("")

    # Suggestions Section
    if suggestions:
        lines.append("💡 SUGGERIMENTI PER MIGLIORARE IL MENU")
        lines.append("-" * 45)
        lines.append("Template consigliati da sbloccare:")
        for i, suggestion in enumerate(suggestions, 1):
            template = suggestion['template']
            points = suggestion['points']
            reason = suggestion['reason']
            lines.append(f"{i:2d}. {template} ({points} punti) - {reason}")
        lines.append("")

    # Cost Analysis
    cost_vs_target = kpis.get('cost_vs_target', {})
    if cost_vs_target:
        lines.append("💰 ANALISI COSTI VS TARGET")
        lines.append("-" * 30)
        distribution = cost_vs_target.get('distribution', {})
        total_items = sum(distribution.values())

        if total_items > 0:
            under = distribution.get('under_target', 0)
            on = distribution.get('on_target', 0)
            over = distribution.get('over_target', 0)

            lines.append(f"🔻 Sotto target: {under} ricette ({under/total_items:.1%})")
            lines.append(f"🎯 Sul target: {on} ricette ({on/total_items:.1%})")
            lines.append(f"🔺 Sopra target: {over} ricette ({over/total_items:.1%})")

        lines.append("")

    # Footer
    lines.append("=" * 70)
    lines.append("📝 Report generato da Chef Planner MVP 0.3")
    lines.append("🎮 Built for Chef: A Restaurant Tycoon Game")
    lines.append("=" * 70)

    return "\n".join(lines)


def menu_health_score(kpis: Dict[str, Any], warnings_count: int) -> int:
    """
    Calculate overall menu health score (0-100)
    Helper function for report generation
    """
    if kpis.get('n_items', 0) == 0:
        return 0

    # Base score components
    stars_score = (kpis.get('avg_stars', 0) / 5.0) * 30  # Max 30 points
    fit_score = (kpis.get('avg_fit_total', 0) / 100.0) * 25  # Max 25 points

    # Price coherence score (inverted deviation)
    price_coherence = max(0, 20 - kpis.get('avg_price_deviation_pct', 0) * 0.5)  # Max 20 points
    price_coherence = min(20, price_coherence)

    # Section balance score
    section_balance = 15  # Start with max
    section_coverage = kpis.get('section_coverage', {})
    for section_info in section_coverage.values():
        deviation = section_info.get('deviation', 0)
        if deviation > 0.3:  # 30% deviation penalty
            section_balance -= 5
    section_balance = max(0, section_balance)

    # Tag coverage score
    tag_coverage_pct = kpis.get('tag_coverage', {}).get('favourite_coverage_pct', 0)
    tag_score = (tag_coverage_pct / 100.0) * 10  # Max 10 points

    # Warning penalty
    warning_penalty = min(warnings_count * 3, 20)  # Max 20 point penalty

    # Calculate final score
    total_score = stars_score + fit_score + price_coherence + section_balance + tag_score - warning_penalty

    return max(0, min(100, int(total_score)))


def get_export_filename(export_type: str, segment_name: str = "menu") -> str:
    """
    Generate appropriate filename for exports
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    clean_segment = segment_name.lower().replace(" ", "_")

    extensions = {
        'csv': 'csv',
        'json': 'json',
        'report': 'txt'
    }

    ext = extensions.get(export_type, 'txt')
    return f"chef_planner_{clean_segment}_{timestamp}.{ext}"