"""Inventory and report aggregation."""

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from models import *
from pricing import create_invoice


def requested_stock(orders: Sequence[Order]) -> Counter[str]:
    result = Counter()
    for order in orders:
        for line in order.lines:
            result[line.sku] += line.quantity
    return result


def stock_alerts(
    orders: Sequence[Order], products: dict[str, Product]
) -> tuple[StockAlert, ...]:
    return tuple(
        StockAlert(sku, products[sku].name, quantity, products[sku].stock)
        for sku, quantity in sorted(requested_stock(orders).items())
        if quantity > products[sku].stock
    )


def build_report(
    orders: Sequence[Order],
    customers: dict[str, Customer],
    products: dict[str, Product],
) -> Report:
    ordered = sorted(orders, key=lambda order: (order.placed_on, order.identifier))
    return Report(
        tuple(create_invoice(order, customers, products) for order in ordered),
        stock_alerts(ordered, products),
    )


def report_total(report: Report) -> Decimal:
    return sum((i.total for i in report.invoices), ZERO)


def report_tax(report: Report) -> Decimal:
    return sum((i.tax for i in report.invoices), ZERO)


def report_discounts(report: Report) -> Decimal:
    return sum((i.discount for i in report.invoices), ZERO)


def totals_by_customer(report: Report) -> dict[str, Decimal]:
    result = {}
    for invoice in report.invoices:
        result[invoice.customer.identifier] = (
            result.get(invoice.customer.identifier, ZERO) + invoice.total
        )
    return dict(sorted(result.items()))


def gross_sales_by_category(report: Report) -> dict[str, Decimal]:
    result = {}
    for invoice in report.invoices:
        for line in invoice.lines:
            result[line.category] = result.get(line.category, ZERO) + line.total
    return dict(sorted(result.items()))


def units_by_product(report: Report) -> Counter[str]:
    result = Counter()
    for invoice in report.invoices:
        for line in invoice.lines:
            result[line.sku] += line.quantity
    return result
