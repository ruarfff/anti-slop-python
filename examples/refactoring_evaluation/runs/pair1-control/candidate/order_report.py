"""Public order report API and command-line entry point."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "candidate"

from .exports import invoice_csv, stock_csv, summary_json, write_exports
from .input_data import (
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
from .model import (
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
    Report,
    StockAlert,
)
from .presentation import (
    format_money,
    render_invoice,
    render_invoice_header,
    render_invoice_lines,
    render_invoice_totals,
    render_report,
    render_stock_alerts,
    render_summary,
)
from .pricing import (
    calculate_discount,
    calculate_shipping,
    calculate_subtotal,
    calculate_tax,
    create_invoice,
    money,
    price_line,
)
from .reporting import (
    build_report,
    gross_sales_by_category,
    report_discounts,
    report_tax,
    report_total,
    requested_stock,
    stock_alerts,
    totals_by_customer,
    units_by_product,
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
            identifier="O001",
            customer_id="C001",
            placed_on=date(2026, 1, 15),
            shipping="standard",
            discount_percent=Decimal(10),
            lines=(OrderLine("PEN", 4), OrderLine("BOOK", 2)),
        ),
        Order(
            identifier="O002",
            customer_id="C001",
            placed_on=date(2026, 1, 16),
            shipping="pickup",
            discount_percent=ZERO,
            lines=(OrderLine("BOOK", 2),),
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
