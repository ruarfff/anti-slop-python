from decimal import Decimal

from .models import Invoice, Report
from .reporting import report_discounts, report_tax, report_total, units_by_product


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
    return "\n".join(
        ["Stock shortages:"]
        + [
            f"  {a.sku}: requested {a.requested}, available {a.available}"
            for a in report.stock_alerts
        ]
    )


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
