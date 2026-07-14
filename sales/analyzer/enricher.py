from ..models.sale import Sale
from ..utils.nlp.category_classifier import CategoryClassifier
from typing import List

def enrich_sales_data(sales: List[Sale]) -> List[Sale]:
    """
    Обогащает список продаж:
      - категория (по названию)
      - бренд (по ключевым словам: AlphaPet, Royal Canin, etc.)
    """
    enriched = []
    for sale in sales:
        # Категория
        category = CategoryClassifier.classify(sale.product_name)
        
        # Бренд (простой поиск)
        brand = "Неизвестно"
        name_lower = sale.product_name.lower()
        if 'alphapet' in name_lower:
            brand = "AlphaPet"
        elif 'royal canin' in name_lower or 'royal канин' in name_lower:
            brand = "Royal Canin"
        elif 'wellement' in name_lower:
            brand = "Wellement"
        elif 'landor' in name_lower:
            brand = "Landor"
        elif 'best dinner' in name_lower:
            brand = "Best Dinner"
        elif 'lucky bits' in name_lower:
            brand = "Lucky Bits"
        elif 'triol' in name_lower:
            brand = "TRIOL"
        elif 'vetlunch' in name_lower:
            brand = "Vetlunch"
        elif 'сирис' in name_lower or 'сириус' in name_lower:
            brand = "Сириус"
        elif 'пробаланс' in name_lower:
            brand = "ПроБаланс"

        enriched.append(
            Sale(
                **sale.dict(exclude={'category', 'brand', 'is_new'}),
                category=category,
                brand=brand
            )
        )
    return enriched