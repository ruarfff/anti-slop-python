from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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
