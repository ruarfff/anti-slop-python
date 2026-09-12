from datetime import date
from decimal import Decimal

from .models import Customer, Order, OrderLine, Product, Report
from .pricing import ZERO
from .reporting import build_report


def demo_report() -> Report:
    customers = {
        "C001": Customer(
            identifier="C001",
            name="Example Buyer",
            email="buyer@example.invalid",
            city="Austin",
            country="US",
        )
    }
    products = {
        "PEN": Product(
            sku="PEN",
            name="Pen",
            category="stationery",
            unit_price=Decimal("2.50"),
            stock=10,
        ),
        "BOOK": Product(
            sku="BOOK",
            name="Notebook",
            category="stationery",
            unit_price=Decimal("12.00"),
            stock=3,
        ),
    }
    orders = [
        Order(
            identifier="O001",
            customer_id="C001",
            placed_on=date(2026, 1, 15),
            shipping="standard",
            discount_percent=Decimal(10),
            lines=(OrderLine(sku="PEN", quantity=4), OrderLine(sku="BOOK", quantity=2)),
        ),
        Order(
            identifier="O002",
            customer_id="C001",
            placed_on=date(2026, 1, 16),
            shipping="pickup",
            discount_percent=ZERO,
            lines=(OrderLine(sku="BOOK", quantity=2),),
        ),
    ]
    return build_report(orders, customers, products)
