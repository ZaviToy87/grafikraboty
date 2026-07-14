// Дополнительные утилиты для анализа продаж
window.SalesAnalyzer = {
  formatNumber(num) {
    return num.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  parseCurrency(str) {
    return parseFloat(str.replace(/[^\d.,-]/g, '').replace(',', '.'));
  }
};