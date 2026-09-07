"""Money calculations and invoice construction."""

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
)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def price_line(line: OrderLine, products: dict[str, Product]) -> PricedLine:
    product = products[line.sku]
    unit_price = money(product.unit_price)
    return PricedLine(
        product.sku,
        product.name,
        product.category,
        line.quantity,
        unit_price,
        money(unit_price * line.quantity),
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
    order: Order, customers: dict[str, Customer], products: dict[str, Product]
) -> Invoice:
    lines = tuple(price_line(line, products) for line in order.lines)
    subtotal = calculate_subtotal(lines)
    discount = calculate_discount(subtotal, order.discount_percent)
    tax = calculate_tax(subtotal, discount)
    shipping = calculate_shipping(order.shipping, subtotal - discount)
    return Invoice(
        order,
        customers[order.customer_id],
        lines,
        subtotal,
        discount,
        tax,
        shipping,
        subtotal - discount + tax + shipping,
    )
