# Alpaca MCP Server

This is a Model Context Protocol (MCP) server for Alpaca, allowing LLMs like Claude to interact with the Alpaca trading API. It enables trading stocks, checking positions, fetching market data, and managing your account - all through natural language.

## Features

- 📊 **Market Data** - Get real-time stock quotes and historical price data
- 💵 **Account Information** - Check your balances, buying power, and status
- 📈 **Position Management** - View current positions and their performance
- 🛒 **Order Placement** - Place market and limit orders through natural language
- 📋 **Order Management** - List, track, and cancel orders

## Prerequisites

- Python 3.10+
- Alpaca API keys (from https://app.alpaca.markets/paper/dashboard/overview)
- Node.js and npm (for running the MCP inspector)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/alpaca-mcp.git
   cd alpaca-mcp
   ```

2. Install the required packages:
   ```bash
   pip install mcp alpaca-py python-dotenv
   ```

## Usage

### Running the server

Start the server using the MCP inspector:

```bash
npx @modelcontextprotocol/inspector python alpaca_mcp_server.py
```

The inspector will start a web interface at http://127.0.0.1:6274 where you can interact with the server.

### Available Tools

The server exposes the following tools, each requiring your Alpaca API credentials as parameters:

- `get_account_info(api_key, api_secret, paper)` - Get account balances and status
- `get_positions(api_key, api_secret, paper)` - List all current positions in the portfolio
- `get_stock_quote(symbol, api_key, api_secret)` - Get the latest quote for a stock
- `get_stock_bars(symbol, api_key, api_secret, days)` - Get historical price bars for a stock
- `get_orders(api_key, api_secret, paper, status, limit)` - List orders with specified status
- `place_market_order(symbol, side, quantity, api_key, api_secret, paper)` - Place a market order
- `place_limit_order(symbol, side, quantity, limit_price, api_key, api_secret, paper)` - Place a limit order
- `cancel_all_orders(api_key, api_secret, paper)` - Cancel all open orders
- `close_all_positions(api_key, api_secret, paper, cancel_orders)` - Close all open positions

Each tool requires:
- `api_key`: Your Alpaca API key ID
- `api_secret`: Your Alpaca API secret key
- `paper`: Boolean indicating whether to use paper trading (defaults to True)

## Example Queries

When using the MCP inspector, you can ask questions like:

- "What's my current account balance and buying power?"
- "Show me my current positions"
- "Get the latest quote for AAPL"
- "Show me the price history for TSLA over the last 10 days"
- "Buy 5 shares of MSFT at market price"
- "Sell 10 shares of AMZN with a limit price of $130"
- "Cancel all my open orders"

The LLM will automatically include your API credentials when making the calls.

## Security Notice

This MCP server will have access to your Alpaca account and can place real trades. Always:
1. Keep your API credentials secure
2. Review what the LLM is suggesting before approving any trades
3. Use paper trading (paper=True) while testing
4. Never share your API credentials in public repositories or discussions

## License

MIT