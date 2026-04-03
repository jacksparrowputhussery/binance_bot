"""Binance Futures Testnet API client wrapper.

Wraps python-binance, isolating all HTTP communication and
translating third-party exceptions into domain-specific types.
"""
import os
from decimal import Decimal
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout

from bot.logging_config import get_logger

load_dotenv()  # load .env file if present

TESTNET_BASE_URL = "https://testnet.binancefuture.com"

logger = get_logger(__name__)


class APIError(Exception):
    """Raised when the Binance API returns an error response.

    Attributes:
        code: Binance API error code.
        message: Binance API error message.
    """

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class NetworkError(Exception):
    """Raised when a network-level failure occurs.

    Attributes:
        detail: Original exception string.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Network error: {detail}")


class BinanceFuturesClient:
    """Thin wrapper around python-binance Client for Futures Testnet."""

    def __init__(self) -> None:
        """Initialize the client using environment variables.

        Raises:
            EnvironmentError: If BINANCE_API_KEY or BINANCE_API_SECRET are not set.
        """
        api_key = os.environ.get("BINANCE_API_KEY")
        api_secret = os.environ.get("BINANCE_API_SECRET")

        if not api_key:
            raise EnvironmentError("BINANCE_API_KEY environment variable is not set")
        if not api_secret:
            raise EnvironmentError("BINANCE_API_SECRET environment variable is not set")

        self._client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,
        )
        # Override futures base URL to point at the testnet
        self._client.FUTURES_URL = TESTNET_BASE_URL + "/fapi"

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: Optional[str] = None,
        stop_price: Optional[Decimal] = None,
    ) -> dict:
        """Place a futures order on the Binance Testnet.

        Args:
            symbol: Trading pair, e.g. BTCUSDT.
            side: BUY or SELL.
            order_type: MARKET, LIMIT, or STOP.
            quantity: Amount of base asset.
            price: Limit price (required for LIMIT/STOP orders).
            time_in_force: Time-in-force value, e.g. GTC.
            stop_price: Trigger price for STOP orders.

        Returns:
            Raw Order_Response dict from the Binance API.

        Raises:
            APIError: If the Binance API returns an error response.
            NetworkError: If a network-level failure occurs.
        """
        kwargs: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        if price is not None:
            kwargs["price"] = str(price)
        if time_in_force is not None:
            kwargs["timeInForce"] = time_in_force
        if stop_price is not None:
            kwargs["stopPrice"] = str(stop_price)

        try:
            response = self._client.futures_create_order(**kwargs)
            return response
        except BinanceAPIException as exc:
            raise APIError(code=exc.code, message=exc.message) from exc
        except (RequestsConnectionError, Timeout, OSError) as exc:
            raise NetworkError(detail=str(exc)) from exc

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """Fetch the current status of an order by ID.

        Args:
            symbol: Trading pair, e.g. BTCUSDT.
            order_id: The order ID returned by place_order.

        Returns:
            Order status dict from the Binance API.

        Raises:
            APIError: If the Binance API returns an error response.
            NetworkError: If a network-level failure occurs.
        """
        try:
            return self._client.futures_get_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as exc:
            raise APIError(code=exc.code, message=exc.message) from exc
        except (RequestsConnectionError, Timeout, OSError) as exc:
            raise NetworkError(detail=str(exc)) from exc
