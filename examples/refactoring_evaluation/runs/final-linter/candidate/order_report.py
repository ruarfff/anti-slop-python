"""Public API and command-line entry point for order reports."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    from ._input import (
        group_order_lines,
        load_customers,
        load_orders,
        load_products,
        parse_customer,
        parse_decimal,
        parse_integer,
        parse_order,
        parse_order_line,
        parse_product,
        read_rows,
        required_text,
    )
    from ._models import (
        Customer,
        Invoice,
        Order,
        OrderLine,
        PricedLine,
        Product,
        Report,
        StockAlert,
    )
    from ._pricing import (
        CENT,
        EXPRESS_SHIPPING,
        FREE_SHIPPING_THRESHOLD,
        STANDARD_SHIPPING,
        TAX_RATE,
        ZERO,
        calculate_discount,
        calculate_shipping,
        calculate_subtotal,
        calculate_tax,
        create_invoice,
        money,
        price_line,
    )
except ImportError:
    from _input import (
        load_customers,
        load_orders,
        load_products,
    )
    from _models import (
        Customer,
        Invoice,
        Order,
        OrderLine,
        Product,
        Report,
        StockAlert,
    )
    from _pricing import (
        ZERO,
        create_invoice,
    )

__all__ = [
    "CENT",
    "EXPRESS_SHIPPING",
    "FREE_SHIPPING_THRESHOLD",
    "STANDARD_SHIPPING",
    "TAX_RATE",
    "ZERO",
    "Customer",
    "Invoice",
    "Order",
    "OrderLine",
    "PricedLine",
    "Product",
    "Report",
    "StockAlert",
    "build_report",
    "calculate_discount",
    "calculate_shipping",
    "calculate_subtotal",
    "calculate_tax",
    "create_invoice",
    "demo_report",
    "format_money",
    "gross_sales_by_category",
    "group_order_lines",
    "invoice_csv",
    "load_customers",
    "load_orders",
    "load_products",
    "load_report",
    "main",
    "money",
    "parse_customer",
    "parse_decimal",
    "parse_integer",
    "parse_order",
    "parse_order_line",
    "parse_product",
    "price_line",
    "read_rows",
    "render_invoice",
    "render_invoice_header",
    "render_invoice_lines",
    "render_invoice_totals",
    "render_report",
    "render_stock_alerts",
    "render_summary",
    "report_discounts",
    "report_tax",
    "report_total",
    "requested_stock",
    "required_text",
    "stock_alerts",
    "stock_csv",
    "summary_json",
    "totals_by_customer",
    "units_by_product",
    "write_exports",
]


def requested_stock(orders: Sequence[Order]) -> Counter[str]:
    result: Counter[str] = Counter()
    for order in orders:
        for line in order.lines:
            result[line.sku] += line.quantity
    return result


def stock_alerts(
    orders: Sequence[Order], products: dict[str, Product]
) -> tuple[StockAlert, ...]:
    return tuple(
        StockAlert(sku, products[sku].name, qty, products[sku].stock)
        for sku, qty in sorted(requested_stock(orders).items())
        if qty > products[sku].stock
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
    totals: dict[str, Decimal] = {}
    for invoice in report.invoices:
        totals[invoice.customer.identifier] = (
            totals.get(invoice.customer.identifier, ZERO) + invoice.total
        )
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
        f"  {x.quantity} x {x.name} [{x.sku}]: {format_money(x.total)}"
        for x in invoice.lines
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
    return (
        "\n\n".join(
            [
                *(render_invoice(i) for i in report.invoices),
                render_stock_alerts(report),
                render_summary(report),
            ]
        )
        + "\n"
    )


def _csv_report(report: Report, header: list[str], rows: list[list[object]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def invoice_csv(report: Report) -> str:
    return _csv_report(
        report,
        ["order_id", "customer_id", "date", "subtotal", "discount", "tax", "total"],
        [
            [
                i.order.identifier,
                i.customer.identifier,
                i.order.placed_on.isoformat(),
                str(i.subtotal),
                str(i.discount),
                str(i.tax),
                str(i.total),
            ]
            for i in report.invoices
        ],
    )


def stock_csv(report: Report) -> str:
    return _csv_report(
        report,
        ["sku", "name", "requested", "available", "shortage"],
        [
            [a.sku, a.name, a.requested, a.available, a.requested - a.available]
            for a in report.stock_alerts
        ],
    )


def summary_json(report: Report) -> str:
    payload = {
        "orders": len(report.invoices),
        "total": str(report_total(report)),
        "tax": str(report_tax(report)),
        "discounts": str(report_discounts(report)),
        "customer_totals": {k: str(v) for k, v in totals_by_customer(report).items()},
        "category_gross_sales": {
            k: str(v) for k, v in gross_sales_by_category(report).items()
        },
        "units_by_product": dict(sorted(units_by_product(report).items())),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_exports(report: Report, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in [
        ("report.txt", render_report(report)),
        ("invoices.csv", invoice_csv(report)),
        ("stock.csv", stock_csv(report)),
        ("summary.json", summary_json(report)),
    ]:
        (directory / name).write_text(
            content, encoding="utf-8", newline="" if name.endswith(".csv") else None
        )


def demo_report() -> Report:
    customers = {
        "C001": Customer(
            "C001", "Example Buyer", "buyer@example.invalid", "Austin", "US"
        )
    }
    products = {
        "PEN": Product("PEN", "Pen", "stationery", Decimal("2.50"), 10),
        "BOOK": Product("BOOK", "Notebook", "stationery", Decimal("12.00"), 3),
    }
    orders = [
        Order(
            "O001",
            "C001",
            date(2026, 1, 15),
            "standard",
            Decimal(10),
            (OrderLine("PEN", 4), OrderLine("BOOK", 2)),
        ),
        Order(
            "O002", "C001", date(2026, 1, 16), "pickup", ZERO, (OrderLine("BOOK", 2),)
        ),
    ]
    return build_report(orders, customers, products)


def load_report(directory: Path) -> Report:
    return build_report(
        load_orders(directory), load_customers(directory), load_products(directory)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an order report in USD.")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--demo", action="store_true", help="Use built-in sample orders"
    )
    inputs.add_argument(
        "--input", type=Path, help="Directory containing four input CSVs"
    )
    parser.add_argument("--output", type=Path, help="Write text, CSV, and JSON reports")
    arguments = parser.parse_args(argv)
    report = demo_report() if arguments.demo else load_report(arguments.input)
    if arguments.output is not None:
        write_exports(report, arguments.output)
    print(render_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
