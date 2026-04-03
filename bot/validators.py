"""Input validation for trading bot CLI parameters.

Pure functions with no I/O or side effects.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


class ValidationError(Exception):
    """Raised when a user-supplied parameter fails validation.

    Attributes:
        field: Name of the offending parameter.
        message: Human-readable description of the violation.
    """

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass
class OrderParams:
    """Validated and normalized order parameters."""

    symbol: str
    side: str           # normalized to uppercase: BUY or SELL
    order_type: str     # normalized to uppercase: MARKET, LIMIT, or STOP
    quantity: Decimal   # > 0
    price: Optional[Decimal]       # > 0 for LIMIT/STOP; None for MARKET
    stop_price: Optional[Decimal]  # > 0 for STOP; None otherwise


def validate(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
    stop_price: Optional[str] = None,
) -> OrderParams:
    """Validate and normalize order parameters.

    Rules applied in order:
    1. symbol — non-empty, alphanumeric
    2. side — BUY or SELL (case-insensitive)
    3. order_type — MARKET or LIMIT (case-insensitive)
    4. quantity — positive decimal > 0
    5. price — required and > 0 when order_type is LIMIT

    Args:
        symbol: Trading pair, e.g. BTCUSDT.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP.
        quantity: Amount of base asset as a string.
        price: Limit price as a string, or None for MARKET orders.
        stop_price: Trigger price for STOP orders.

    Returns:
        Normalized OrderParams dataclass.

    Raises:
        ValidationError: On the first violated rule.
    """
    # 1. symbol
    if not symbol or not symbol.isalnum():
        raise ValidationError("symbol", "must be a non-empty alphanumeric string (e.g. BTCUSDT)")

    # 2. side
    normalized_side = side.upper() if side else ""
    if normalized_side not in VALID_SIDES:
        raise ValidationError("side", f"must be one of {sorted(VALID_SIDES)}, got '{side}'")

    # 3. order_type
    normalized_order_type = order_type.upper() if order_type else ""
    if normalized_order_type not in VALID_ORDER_TYPES:
        raise ValidationError("order_type", f"must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'")

    # 4. quantity
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, TypeError):
        raise ValidationError("quantity", f"must be a valid decimal number, got '{quantity}'")
    if qty <= 0:
        raise ValidationError("quantity", f"must be greater than zero, got '{quantity}'")

    # 5. price (required for LIMIT and STOP, ignored for MARKET)
    parsed_price: Optional[Decimal] = None
    if normalized_order_type in ("LIMIT", "STOP"):
        if price is None or str(price).strip() == "":
            raise ValidationError("price", f"is required for {normalized_order_type} orders")
        try:
            parsed_price = Decimal(str(price))
        except (InvalidOperation, TypeError):
            raise ValidationError("price", f"must be a valid decimal number, got '{price}'")
        if parsed_price <= 0:
            raise ValidationError("price", f"must be greater than zero, got '{price}'")

    # 6. stop_price (required for STOP orders)
    parsed_stop_price: Optional[Decimal] = None
    if normalized_order_type == "STOP":
        if stop_price is None or str(stop_price).strip() == "":
            raise ValidationError("stop_price", "is required for STOP orders")
        try:
            parsed_stop_price = Decimal(str(stop_price))
        except (InvalidOperation, TypeError):
            raise ValidationError("stop_price", f"must be a valid decimal number, got '{stop_price}'")
        if parsed_stop_price <= 0:
            raise ValidationError("stop_price", f"must be greater than zero, got '{stop_price}'")

    return OrderParams(
        symbol=symbol.upper(),
        side=normalized_side,
        order_type=normalized_order_type,
        quantity=qty,
        price=parsed_price,
        stop_price=parsed_stop_price,
    )
