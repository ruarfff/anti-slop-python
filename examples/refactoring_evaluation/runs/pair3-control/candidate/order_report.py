"""Public order report API and command-line entry point."""

from __future__ import annotations
import argparse, csv, io, json
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    from .models import *  # noqa: F403
    from .parsing import *  # noqa: F403
    from .pricing import *  # noqa: F403
    from .reporting import *  # noqa: F403
except ImportError:
    from models import *  # noqa: F403
    from parsing import *  # noqa: F403
    from pricing import *  # noqa: F403
    from reporting import *  # noqa: F403


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


def invoice_csv(report: Report) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(
        ["order_id", "customer_id", "date", "subtotal", "discount", "tax", "total"]
    )
    for invoice in report.invoices:
        writer.writerow(
            [
                invoice.order.identifier,
                invoice.customer.identifier,
                invoice.order.placed_on.isoformat(),
                str(invoice.subtotal),
                str(invoice.discount),
                str(invoice.tax),
                str(invoice.total),
            ]
        )
    return stream.getvalue()


def stock_csv(report: Report) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["sku", "name", "requested", "available", "shortage"])
    for alert in report.stock_alerts:
        writer.writerow(
            [
                alert.sku,
                alert.name,
                alert.requested,
                alert.available,
                alert.requested - alert.available,
            ]
        )
    return stream.getvalue()


def summary_json(report: Report) -> str:
    payload = {
        "orders": len(report.invoices),
        "total": str(report_total(report)),
        "tax": str(report_tax(report)),
        "discounts": str(report_discounts(report)),
        "customer_totals": {
            key: str(value) for key, value in totals_by_customer(report).items()
        },
        "category_gross_sales": {
            key: str(value) for key, value in gross_sales_by_category(report).items()
        },
        "units_by_product": dict(sorted(units_by_product(report).items())),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_exports(report: Report, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.txt").write_text(render_report(report), encoding="utf-8")
    (directory / "invoices.csv").write_text(
        invoice_csv(report), encoding="utf-8", newline=""
    )
    (directory / "stock.csv").write_text(
        stock_csv(report), encoding="utf-8", newline=""
    )
    (directory / "summary.json").write_text(summary_json(report), encoding="utf-8")


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
