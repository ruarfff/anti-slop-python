"""Inventory checks and report aggregation."""

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

try:
    from .order_models import ZERO, Customer, Order, Product, Report, StockAlert
    from .order_pricing import create_invoice
except ImportError:
    from order_models import ZERO, Customer, Order, Product, Report, StockAlert
    from order_pricing import create_invoice


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
    return sum((invoice.total for invoice in report.invoices), ZERO)


def report_tax(report: Report) -> Decimal:
    return sum((invoice.tax for invoice in report.invoices), ZERO)


def report_discounts(report: Report) -> Decimal:
    return sum((invoice.discount for invoice in report.invoices), ZERO)


def totals_by_customer(report: Report) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for invoice in report.invoices:
        identifier = invoice.customer.identifier
        totals[identifier] = totals.get(identifier, ZERO) + invoice.total
    return dict(sorted(totals.items()))


def gross_sales_by_category(report: Report) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for invoice in report.invoices:
        for line in invoice.lines:
            totals[line.category] = totals.get(line.category, ZERO) + line.total
    return dict(sorted(totals.items()))


def units_by_product(report: Report) -> Counter[str]:
    units: Counter[str] = Counter()
    for invoice in report.invoices:
        for line in invoice.lines:
            units[line.sku] += line.quantity
    return units
