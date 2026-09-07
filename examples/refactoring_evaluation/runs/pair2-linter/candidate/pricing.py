"""Invoice pricing and inventory checks."""

from collections import Counter
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from models import (
    CENT,
    EXPRESS_SHIPPING,
    FREE_SHIPPING_THRESHOLD,
    STANDARD_SHIPPING,
    TAX_RATE,
    ZERO,
    Customer,
    Invoice,
    Order,
    OrderLine,
    PricedLine,
    Product,
    StockAlert,
)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def price_line(line: OrderLine, products: dict[str, Product]) -> PricedLine:
    product = products[line.sku]
    unit_price = money(product.unit_price)
    return PricedLine(
        sku=product.sku,
        name=product.name,
        category=product.category,
        quantity=line.quantity,
        unit_price=unit_price,
        total=money(unit_price * line.quantity),
    )


def calculate_subtotal(lines: Sequence[PricedLine]) -> Decimal:
    return sum((line.total for line in lines), ZERO)


def calculate_discount(subtotal: Decimal, percent: Decimal) -> Decimal:
    return money(subtotal * percent / 100)


def calculate_tax(subtotal: Decimal, discount: Decimal) -> Decimal:
    return money((subtotal - discount) * TAX_RATE)


def calculate_shipping(method: str, discounted_subtotal: Decimal) -> Decimal:
    if method == "pickup":
        return ZERO
    if method == "express":
        return EXPRESS_SHIPPING
    if discounted_subtotal >= FREE_SHIPPING_THRESHOLD:
        return ZERO
    return STANDARD_SHIPPING


def create_invoice(
    order: Order,
    customers: dict[str, Customer],
    products: dict[str, Product],
) -> Invoice:
    lines = tuple(price_line(line, products) for line in order.lines)
    subtotal = calculate_subtotal(lines)
    discount = calculate_discount(subtotal, order.discount_percent)
    tax = calculate_tax(subtotal, discount)
    shipping = calculate_shipping(order.shipping, subtotal - discount)
    return Invoice(
        order=order,
        customer=customers[order.customer_id],
        lines=lines,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        shipping=shipping,
        total=subtotal - discount + tax + shipping,
    )


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
