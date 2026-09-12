import csv
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Customer, Order, OrderLine, Product


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
    return OrderLine(required_text(row, "sku"), quantity)


def group_order_lines(rows: list[dict[str, str]]) -> dict[str, list[OrderLine]]:
    groups: dict[str, list[OrderLine]] = {}
    for row in rows:
        groups.setdefault(required_text(row, "order_id"), []).append(
            parse_order_line(row)
        )
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
