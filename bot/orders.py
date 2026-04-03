"""Order placement logic for the trading bot.

Owns the business rules for constructing order payloads
and delegates HTTP communication to BinanceFuturesClient.
"""
import time

from bot.client import BinanceFuturesClient
from bot.logging_config import get_logger
from bot.validators import OrderParams

logger = get_logger(__name__)


class OrderManager:
    """Orchestrates order placement via the Binance Futures client."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_order(self, params: OrderParams) -> dict:
        """Place a futures order based on validated OrderParams.

        MARKET orders are submitted without a price.
        LIMIT orders are submitted with the given price and timeInForce=GTC.

        Args:
            params: Validated and normalized order parameters.

        Returns:
            Raw Order_Response dict from the Binance API.

        Raises:
            APIError: Propagated from client on API errors.
            NetworkError: Propagated from client on network failures.
        """
        logger.info(
            "Placing order | symbol=%s side=%s type=%s quantity=%s price=%s",
            params.symbol,
            params.side,
            params.order_type,
            params.quantity,
            params.price,
        )

        if params.order_type == "MARKET":
            response = self._client.place_order(
                symbol=params.symbol,
                side=params.side,
                order_type="MARKET",
                quantity=params.quantity,
            )
            # Testnet returns status=NEW immediately; poll once to get the filled status
            time.sleep(0.5)
            response = self._client.get_order_status(params.symbol, response["orderId"])
        elif params.order_type == "LIMIT":
            response = self._client.place_order(
                symbol=params.symbol,
                side=params.side,
                order_type="LIMIT",
                quantity=params.quantity,
                price=params.price,
                time_in_force="GTC",
            )
        else:  # STOP (Stop-Limit)
            response = self._client.place_order(
                symbol=params.symbol,
                side=params.side,
                order_type="STOP",
                quantity=params.quantity,
                price=params.price,
                stop_price=params.stop_price,
                time_in_force="GTC",
            )

        logger.info("Order response | %s", response)
        return response
