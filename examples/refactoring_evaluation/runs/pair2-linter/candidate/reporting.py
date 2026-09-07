"""Report assembly, aggregate values, and text presentation."""

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from models import ZERO, Customer, Invoice, Order, Product, Report
from pricing import create_invoice, stock_alerts


def build_report(
    orders: Sequence[Order],
    customers: dict[str, Customer],
    products: dict[str, Product],
) -> Report:
    ordered = sorted(orders, key=lambda order: (order.placed_on, order.identifier))
    invoices = tuple(create_invoice(order, customers, products) for order in ordered)
    return Report(invoices=invoices, stock_alerts=stock_alerts(ordered, products))


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


def format_money(value: Decimal) -> str:
    return f"USD {value:,.2f}"


def render_invoice_header(invoice: Invoice) -> list[str]:
    return [
        f"Order {invoice.order.identifier} | {invoice.order.placed_on.isoformat()}",
        f"Customer: {invoice.customer.name} ({invoice.customer.identifier})",
        f"Destination: {invoice.customer.city}, {invoice.customer.country}",
        f"Shipping: {invoice.order.shipping}",
    ]


def render_invoice_lines(invoice: Invoice) -> list[str]:
    return [
        f"  {line.quantity} x {line.name} [{line.sku}]: {format_money(line.total)}"
        for line in invoice.lines
    ]


def render_invoice_totals(invoice: Invoice) -> list[str]:
    return [
        f"Subtotal: {format_money(invoice.subtotal)}",
        f"Discount: {format_money(invoice.discount)}",
        f"Tax: {format_money(invoice.tax)}",
        f"Shipping charge: {format_money(invoice.shipping)}",
        f"Total: {format_money(invoice.total)}",
    ]


def render_invoice(invoice: Invoice) -> str:
    lines = render_invoice_header(invoice)
    lines.extend(render_invoice_lines(invoice))
    lines.extend(render_invoice_totals(invoice))
    return "\n".join(lines)


def render_stock_alerts(report: Report) -> str:
    if not report.stock_alerts:
        return "Stock: all requested items available"
    lines = ["Stock shortages:"]
    for alert in report.stock_alerts:
        lines.append(
            f"  {alert.sku}: requested {alert.requested}, available {alert.available}"
        )
    return "\n".join(lines)


def render_summary(report: Report) -> str:
    return "\n".join(
        [
            f"Orders: {len(report.invoices)}",
            f"Units: {sum(units_by_product(report).values())}",
            f"Discounts: {format_money(report_discounts(report))}",
            f"Tax collected: {format_money(report_tax(report))}",
            f"Grand total: {format_money(report_total(report))}",
        ]
    )


def render_report(report: Report) -> str:
    sections = [render_invoice(invoice) for invoice in report.invoices]
    sections.extend([render_stock_alerts(report), render_summary(report)])
    return "\n\n".join(sections) + "\n"
