from typing import Dict, List, Tuple
from ..models.sale import Sale
from ..utils.formatting import format_currency, format_number

def calculate_metrics(sales: List[Sale]) -> dict:
    """
    Рассчитывает основные метрики продаж.
    """
    total_revenue = sum(s.revenue for s in sales)
    total_quantity = sum(s.quantity for s in sales)
    total_products = len(sales)

    # Средний чек (выручка / количество позиций)
    avg_check = total_revenue / total_products if total_products > 0 else 0

    # Топ-10 по выручке
    top_by_revenue = sorted(sales, key=lambda s: s.revenue, reverse=True)[:10]
    top_revenue_items = [
        {
            "product": s.product_name,
            "quantity": s.quantity,
            "revenue": s.revenue,
            "revenue_fmt": format_currency(s.revenue),
            "share": f"{(s.revenue / total_revenue * 100):.1f}%" if total_revenue > 0 else "0%"
        }
        for s in top_by_revenue
    ]

    # Топ-10 по количеству
    top_by_quantity = sorted(sales, key=lambda s: s.quantity, reverse=True)[:10]
    top_quantity_items = [
        {
            "product": s.product_name,
            "quantity": s.quantity,
            "revenue": s.revenue,
            "revenue_fmt": format_currency(s.revenue),
            "share": f"{(s.quantity / total_quantity * 100):.1f}%" if total_quantity > 0 else "0%"
        }
        for s in top_by_quantity
    ]

    # Распределение по категориям
    category_stats: Dict[str, dict] = {}
    for s in sales:
        cat = s.category or "Прочее"
        if cat not in category_stats:
            category_stats[cat] = {"revenue": 0, "quantity": 0, "count": 0}
        category_stats[cat]["revenue"] += s.revenue
        category_stats[cat]["quantity"] += s.quantity
        category_stats[cat]["count"] += 1

    category_breakdown = []
    for cat, stats in category_stats.items():
        share_rev = (stats["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        share_qty = (stats["quantity"] / total_quantity * 100) if total_quantity > 0 else 0
        category_breakdown.append({
            "category": cat,
            "revenue": stats["revenue"],
            "revenue_fmt": format_currency(stats["revenue"]),
            "share_revenue": f"{share_rev:.1f}%",
            "quantity": stats["quantity"],
            "share_quantity": f"{share_qty:.1f}%",
            "count": stats["count"]
        })

    # Сортируем по выручке
    category_breakdown.sort(key=lambda x: x["revenue"], reverse=True)

    return {
        "total_revenue": total_revenue,
        "total_revenue_fmt": format_currency(total_revenue),
        "total_quantity": total_quantity,
        "total_products": total_products,
        "avg_check": avg_check,
        "avg_check_fmt": format_currency(avg_check),
        "top_by_revenue": top_revenue_items,
        "top_by_quantity": top_quantity_items,
        "category_breakdown": category_breakdown,
        "period_summary": f"{total_products} позиций, {format_currency(total_revenue)} выручки"
    }