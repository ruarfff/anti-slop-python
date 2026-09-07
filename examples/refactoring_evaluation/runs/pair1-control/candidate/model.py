"""Domain records and money constants used by order reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

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
