"""Money and shipping constants used by order calculations."""

from decimal import Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
TAX_RATE = Decimal("0.08")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
STANDARD_SHIPPING = Decimal("5.00")
EXPRESS_SHIPPING = Decimal("15.00")
