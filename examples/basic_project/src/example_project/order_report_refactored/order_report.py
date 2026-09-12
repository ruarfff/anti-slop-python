"""Public API and command-line entry point for the order report example."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "order_report_refactored"

from .demo import demo_report
from .exports import invoice_csv, stock_csv, summary_json, write_exports
from .inventory import requested_stock, stock_alerts
from .models import (
    Customer,
    Invoice,
    Order,
    OrderLine,
    PricedLine,
    Product,
    Report,
    StockAlert,
)
from .parsing import (
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
from .reporting import (
    build_report,
    gross_sales_by_category,
    load_report,
    report_discounts,
    report_tax,
    report_total,
    totals_by_customer,
    units_by_product,
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
