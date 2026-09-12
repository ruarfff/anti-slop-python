from collections import Counter
from collections.abc import Sequence

from .models import Order, Product, StockAlert


def requested_stock(orders: Sequence[Order]) -> Counter[str]:
    requested: Counter[str] = Counter()
    for order in orders:
        for line in order.lines:
            requested[line.sku] += line.quantity
    return requested


def stock_alerts(
    orders: Sequence[Order], products: dict[str, Product]
) -> tuple[StockAlert, ...]:
    alerts = []
    for sku, quantity in sorted(requested_stock(orders).items()):
        product = products[sku]
        if quantity > product.stock:
            alerts.append(StockAlert(sku, product.name, quantity, product.stock))
    return tuple(alerts)
