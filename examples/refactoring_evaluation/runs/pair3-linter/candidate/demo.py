"""Built-in demo data and loading of complete reports."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from constants import ZERO
from input_data import load_customers, load_orders, load_products
from models import Customer, Order, OrderLine, Product, Report

from collation import build_report


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
