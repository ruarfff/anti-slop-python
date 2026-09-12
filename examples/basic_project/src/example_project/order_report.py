"""Before refactoring: an order report workflow accumulated in one module.

This module intentionally violates SPY003. It combines input parsing, validation,
pricing, inventory checks, reporting, serialization, and command-line handling.
Run it with --demo for a working example that needs no external services.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
TAX_RATE = Decimal("0.08")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
STANDARD_SHIPPING = Decimal("5.00")
EXPRESS_SHIPPING = Decimal("15.00")


@dataclass(frozen=True)
class Customer:
    identifier: str
    name: str
    email: str
    city: str
    country: str


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    category: str
    unit_price: Decimal
    stock: int


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int


@dataclass(frozen=True)
class Order:
    identifier: str
    customer_id: str
    placed_on: date
    shipping: str
    discount_percent: Decimal
    lines: tuple[OrderLine, ...]


@dataclass(frozen=True)
class PricedLine:
    sku: str
    name: str
    category: str
    quantity: int
    unit_price: Decimal
    total: Decimal


@dataclass(frozen=True)
class Invoice:
    order: Order
    customer: Customer
    lines: tuple[PricedLine, ...]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal


@dataclass(frozen=True)
class StockAlert:
    sku: str
    name: str
    requested: int
    available: int


@dataclass(frozen=True)
class Report:
    invoices: tuple[Invoice, ...]
    stock_alerts: tuple[StockAlert, ...]


# Input parsing


def required_text(row: dict[str, str], key: str) -> str:
    value = row[key].strip()
    if not value:
        raise ValueError(f"{key} must not be empty")
    return value


def parse_integer(row: dict[str, str], key: str) -> int:
    value = int(required_text(row, key))
    if value < 0:
        raise ValueError(f"{key} must not be negative")
    return value


def parse_decimal(row: dict[str, str], key: str) -> Decimal:
    value = Decimal(required_text(row, key))
    if not value.is_finite() or value < 0:
        raise ValueError(f"{key} must be a finite non-negative number")
    return value


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = []
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"Malformed CSV row in {path}")
            rows.append(row)
        return rows


def parse_customer(row: dict[str, str]) -> Customer:
    return Customer(
        identifier=required_text(row, "customer_id"),
        name=required_text(row, "name"),
        email=required_text(row, "email"),
        city=required_text(row, "city"),
        country=required_text(row, "country"),
    )


def parse_product(row: dict[str, str]) -> Product:
    return Product(
        sku=required_text(row, "sku"),
        name=required_text(row, "name"),
        category=required_text(row, "category"),
        unit_price=parse_decimal(row, "unit_price"),
        stock=parse_integer(row, "stock"),
    )


def parse_order_line(row: dict[str, str]) -> OrderLine:
    quantity = parse_integer(row, "quantity")
    if quantity == 0:
        raise ValueError("quantity must be greater than zero")
    return OrderLine(sku=required_text(row, "sku"), quantity=quantity)


def group_order_lines(rows: list[dict[str, str]]) -> dict[str, list[OrderLine]]:
    groups: dict[str, list[OrderLine]] = {}
    for row in rows:
        order_id = required_text(row, "order_id")
        groups.setdefault(order_id, []).append(parse_order_line(row))
    return groups


def parse_order(row: dict[str, str], lines: Sequence[OrderLine]) -> Order:
    discount = parse_decimal(row, "discount_percent")
    if discount > 100:
        raise ValueError("discount_percent must not exceed 100")
    shipping = required_text(row, "shipping")
    if shipping not in {"standard", "express", "pickup"}:
        raise ValueError(f"Unknown shipping method: {shipping}")
    if not lines:
        raise ValueError("An order must have at least one line")
    return Order(
        identifier=required_text(row, "order_id"),
        customer_id=required_text(row, "customer_id"),
        placed_on=date.fromisoformat(required_text(row, "placed_on")),
        shipping=shipping,
        discount_percent=discount,
        lines=tuple(lines),
    )


def load_customers(directory: Path) -> dict[str, Customer]:
    customers: dict[str, Customer] = {}
    for row in read_rows(directory / "customers.csv"):
        customer = parse_customer(row)
        if customer.identifier in customers:
            raise ValueError(f"Duplicate customer: {customer.identifier}")
        customers[customer.identifier] = customer
    return customers


def load_products(directory: Path) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for row in read_rows(directory / "products.csv"):
        product = parse_product(row)
        if product.sku in products:
            raise ValueError(f"Duplicate product: {product.sku}")
        products[product.sku] = product
    return products


def load_orders(directory: Path) -> list[Order]:
    groups = group_order_lines(read_rows(directory / "order_lines.csv"))
    orders: list[Order] = []
    identifiers: set[str] = set()
    for row in read_rows(directory / "orders.csv"):
        order_id = required_text(row, "order_id")
        if order_id in identifiers:
            raise ValueError(f"Duplicate order: {order_id}")
        orders.append(parse_order(row, groups.pop(order_id, [])))
        identifiers.add(order_id)
    if groups:
        raise ValueError(f"Lines refer to unknown orders: {sorted(groups)}")
    return orders


# Pricing


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def price_line(line: OrderLine, products: dict[str, Product]) -> PricedLine:
    product = products[line.sku]
    unit_price = money(product.unit_price)
    return PricedLine(
        sku=product.sku,
        name=product.name,
        category=product.category,
        quantity=line.quantity,
        unit_price=unit_price,
        total=money(unit_price * line.quantity),
    )


def calculate_subtotal(lines: Sequence[PricedLine]) -> Decimal:
    return sum((line.total for line in lines), ZERO)


def calculate_discount(subtotal: Decimal, percent: Decimal) -> Decimal:
    return money(subtotal * percent / 100)


def calculate_tax(subtotal: Decimal, discount: Decimal) -> Decimal:
    return money((subtotal - discount) * TAX_RATE)


def calculate_shipping(method: str, discounted_subtotal: Decimal) -> Decimal:
    if method == "pickup":
        return ZERO
    if method == "express":
        return EXPRESS_SHIPPING
    if discounted_subtotal >= FREE_SHIPPING_THRESHOLD:
        return ZERO
    return STANDARD_SHIPPING


def create_invoice(
    order: Order,
    customers: dict[str, Customer],
    products: dict[str, Product],
) -> Invoice:
    lines = tuple(price_line(line, products) for line in order.lines)
    subtotal = calculate_subtotal(lines)
    discount = calculate_discount(subtotal, order.discount_percent)
    tax = calculate_tax(subtotal, discount)
    shipping = calculate_shipping(order.shipping, subtotal - discount)
    return Invoice(
        order=order,
        customer=customers[order.customer_id],
        lines=lines,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        shipping=shipping,
        total=subtotal - discount + tax + shipping,
    )


# Inventory and report aggregation


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


# Text presentation


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


# Export formats


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


# Demo data and command-line entry point


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
