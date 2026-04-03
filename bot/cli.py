"""CLI entry point for the Binance Futures trading bot.

Parses arguments, validates inputs, places orders, and prints results.
All exceptions are caught here; no stack traces reach the console.
"""
import argparse
import sys
from typing import Optional

from bot.client import APIError, BinanceFuturesClient, NetworkError
from bot.logging_config import get_logger
from bot.orders import OrderManager
from bot.validators import ValidationError, validate

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET or LIMIT futures orders on Binance Testnet (USDT-M)",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="Order side: BUY or SELL")
    parser.add_argument("--order-type", required=True, dest="order_type", help="Order type: MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Quantity of base asset to trade")
    parser.add_argument("--price", required=False, default=None, help="Limit price (required for LIMIT and STOP orders)")
    parser.add_argument("--stop-price", required=False, default=None, dest="stop_price", help="Trigger price (required for STOP orders)")
    return parser


def _print_summary(symbol: str, side: str, order_type: str, quantity: str, price: Optional[str], stop_price: Optional[str] = None) -> None:
    print("=" * 50)
    print("  ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Order Type : {order_type}")
    print(f"  Quantity   : {quantity}")
    if stop_price:
        print(f"  Stop Price : {stop_price}")
    if price:
        print(f"  Price      : {price}")
    print("=" * 50)


def _print_response(response: dict) -> None:
    print("\n  ORDER RESPONSE")
    print("=" * 50)

    # Standard order response fields
    if "orderId" in response:
        print(f"  Order ID     : {response['orderId']}")
        print(f"  Status       : {response.get('status', 'N/A')}")
        print(f"  Executed Qty : {response.get('executedQty', 'N/A')}")
        avg_price = response.get("avgPrice")
        if avg_price is not None:
            print(f"  Avg Price    : {avg_price}")
    # Algo/conditional order response (STOP orders on Futures testnet)
    elif "algoId" in response:
        print(f"  Order ID     : {response['algoId']}")
        print(f"  Status       : {response.get('algoStatus', 'N/A')}")
        print(f"  Order Type   : {response.get('orderType', 'N/A')}")
        print(f"  Trigger Price: {response.get('triggerPrice', 'N/A')}")
        print(f"  Limit Price  : {response.get('price', 'N/A')}")
        print(f"  Quantity     : {response.get('quantity', 'N/A')}")
        print(f"  Side         : {response.get('side', 'N/A')}")
    else:
        # Fallback: print all fields
        for key, value in response.items():
            if value is not None:
                print(f"  {key:<14}: {value}")

    print("=" * 50)
    print("  Order placed successfully.")


def main() -> None:
    """Main entry point: parse → validate → place order → print result."""
    parser = build_parser()
    args = parser.parse_args()

    # Validate inputs
    try:
        params = validate(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        print(f"[Validation Error] {exc.field}: {exc.message}")
        sys.exit(1)

    # Print request summary
    _print_summary(
        symbol=params.symbol,
        side=params.side,
        order_type=params.order_type,
        quantity=str(params.quantity),
        price=str(params.price) if params.price else None,
        stop_price=str(params.stop_price) if params.stop_price else None,
    )

    # Place order
    try:
        client = BinanceFuturesClient()
        manager = OrderManager(client)
        response = manager.place_order(params)
        _print_response(response)
    except ValidationError as exc:
        logger.error("Validation error: %s: %s", exc.field, exc.message)
        print(f"[Validation Error] {exc.field}: {exc.message}")
        sys.exit(1)
    except EnvironmentError as exc:
        logger.error("Environment error: %s", exc)
        print(f"[Configuration Error] {exc}")
        sys.exit(1)
    except APIError as exc:
        logger.error("API error %s: %s", exc.code, exc.message)
        print(f"[API Error] Code {exc.code}: {exc.message}")
        sys.exit(1)
    except NetworkError as exc:
        logger.error("Network error: %s", exc.detail)
        print(f"[Network Error] {exc.detail}")
        sys.exit(1)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        print(f"[Error] An unexpected error occurred: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
