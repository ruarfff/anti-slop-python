"""Public order report API and command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from exports import *
from input_data import *
from models import *
from presentation import *
from pricing import *
from reporting import *

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
    customers = load_customers(directory)
    products = load_products(directory)
    orders = load_orders(directory)
    return build_report(orders, customers, products)


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
