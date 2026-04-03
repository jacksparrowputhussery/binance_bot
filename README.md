# Binance Futures Testnet Trading Bot

A Python CLI application for placing **MARKET**, **LIMIT**, and **STOP (Stop-Limit)** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M). Built with clean layered architecture, structured logging, and robust error handling.

---

## Features

- Place Market, Limit, and Stop-Limit orders on Binance Futures Testnet
- Supports both BUY and SELL sides
- Input validation with clear error messages before any API call
- Structured file logging — console stays clean
- API credentials loaded from a `.env` file
- Graceful error handling for API errors, network failures, and invalid input

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (argparse)
│   ├── client.py           # Binance API client wrapper
│   ├── orders.py           # Order placement logic
│   ├── validators.py       # Input validation
│   └── logging_config.py   # File-only logger
├── .env                    # Environment variables (not committed — add your API keys here)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet API Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register and log in
3. Go to **API Management** and generate your API key and secret

### 2. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd trading_bot
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add your credentials:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```


---

## Usage

```bash
python -m bot.cli --symbol SYMBOL --side BUY|SELL --order-type MARKET|LIMIT|STOP --quantity QTY [--price PRICE] [--stop-price STOP_PRICE]
```

### Arguments

| Argument         | Required          | Description                                              |
|------------------|-------------------|----------------------------------------------------------|
| `--symbol`       | Yes               | Trading pair, e.g. `BTCUSDT`                            |
| `--side`         | Yes               | `BUY` or `SELL`                                          |
| `--order-type`   | Yes               | `MARKET`, `LIMIT`, or `STOP`                             |
| `--quantity`     | Yes               | Quantity of base asset to trade                          |
| `--price`        | LIMIT / STOP only | Limit price for the order                                |
| `--stop-price`   | STOP only         | Trigger price — order activates when market reaches this |

---

## Examples

### Market Order

```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.001
```

```
==================================================
  ORDER REQUEST SUMMARY
==================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Order Type : MARKET
  Quantity   : 0.001
==================================================

  ORDER RESPONSE
==================================================
  Order ID     : 123456789
  Status       : FILLED
  Executed Qty : 0.001
  Avg Price    : 43250.50
==================================================
  Order placed successfully.
```

### Limit Order

```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.001 \
  --price 50000
```

```
==================================================
  ORDER REQUEST SUMMARY
==================================================
  Symbol     : BTCUSDT
  Side       : SELL
  Order Type : LIMIT
  Quantity   : 0.001
  Price      : 50000
==================================================

  ORDER RESPONSE
==================================================
  Order ID     : 987654321
  Status       : NEW
  Executed Qty : 0
  Avg Price    : 0
==================================================
  Order placed successfully.
```

> `Status: NEW` means the order is live on the order book, waiting for the market to reach your price.

### Stop-Limit Order

```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --order-type STOP \
  --quantity 0.004 \
  --stop-price 67000 \
  --price 67100
```

```
==================================================
  ORDER REQUEST SUMMARY
==================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Order Type : STOP
  Quantity   : 0.004
  Stop Price : 67000
  Price      : 67100
==================================================

  ORDER RESPONSE
==================================================
  Order ID     : 1000000041415779
  Status       : NEW
  Order Type   : STOP
  Trigger Price: 67000.00
  Limit Price  : 67100.00
  Quantity     : 0.0040
  Side         : BUY
==================================================
  Order placed successfully.
```

> When the market hits `--stop-price`, a limit order at `--price` is automatically placed.

---

## Logging

All API requests, responses, and errors are written to `trading_bot.log` in the project root. Nothing is written to the console from the logger — output stays clean.

**Log format:**
```
2024-01-15 10:30:00,123 | INFO | bot.orders | Placing order | symbol=BTCUSDT side=BUY type=MARKET quantity=0.001 price=None
2024-01-15 10:30:00,456 | INFO | bot.orders | Order response | {'orderId': 123, 'status': 'FILLED', ...}
```

---

## Error Handling

The bot handles all error conditions gracefully — no raw stack traces are ever printed to the console.

| Error Type        | Example                              | Output                              |
|-------------------|--------------------------------------|-------------------------------------|
| Validation error  | Invalid side, missing price          | `[Validation Error] field: message` |
| API error         | Invalid symbol, insufficient balance | `[API Error] Code -1121: ...`       |
| Network error     | No internet, timeout                 | `[Network Error] connection refused`|
| Config error      | Missing API keys in `.env`           | `[Configuration Error] ...`         |

---

## Assumptions

- Targets Binance Futures Testnet (USDT-M) only — not the live exchange
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled)
- STOP orders are submitted as conditional algo orders via the Binance Futures API
- For MARKET orders, the bot polls the order status once after 500ms to show the final `FILLED` status (testnet returns `NEW` immediately on creation)
- Minimum order quantities and price precision are enforced by the Binance API; any violations are surfaced as clear error messages
