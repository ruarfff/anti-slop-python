from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from .inventory import stock_alerts
from .models import Customer, Order, Product, Report
from .pricing import ZERO, create_invoice


def build_report(
    orders: Sequence[Order],
    customers: dict[str, Customer],
    products: dict[str, Product],
) -> Report:
    ordered = sorted(orders, key=lambda order: (order.placed_on, order.identifier))
    return Report(
        invoices=tuple(create_invoice(order, customers, products) for order in ordered),
        stock_alerts=stock_alerts(ordered, products),
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


def load_report(directory: Path) -> Report:
    from .parsing import load_customers, load_orders, load_products

    customers = load_customers(directory)
    products = load_products(directory)
    orders = load_orders(directory)
    return build_report(orders, customers, products)
