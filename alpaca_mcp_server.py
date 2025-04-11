import os
import sys
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
try:
    mcp = FastMCP("alpaca-trading")
    logger.info("MCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {e}")
    sys.exit(1)

# Initialize Alpaca clients using environment variables
API_KEY = os.getenv("API_KEY_ID")
API_SECRET = os.getenv("API_SECRET_KEY")
PAPER = os.getenv("PAPER", "true").lower() == "true"

# Check if keys are available
if not API_KEY or not API_SECRET:
    logger.error("Alpaca API credentials not found in environment variables.")
    raise ValueError("Alpaca API credentials not found in environment variables.")

try:
    # Initialize trading and data clients
    trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
    stock_client = StockHistoricalDataClient(API_KEY, API_SECRET)
    logger.info("Alpaca clients initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Alpaca clients: {e}")
    sys.exit(1)

# Account information tools
@mcp.tool()
async def get_account_info(api_key: str, api_secret: str, paper: bool = True) -> str:
    """
    Get the current account information including balances and status.
    
    Args:
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        account = trading_client.get_account()
        
        info = f"""
Account Information:
-------------------
Account ID: {account.id}
Status: {account.status}
Currency: {account.currency}
Buying Power: ${float(account.buying_power):.2f}
Cash: ${float(account.cash):.2f}
Portfolio Value: ${float(account.portfolio_value):.2f}
Equity: ${float(account.equity):.2f}
Long Market Value: ${float(account.long_market_value):.2f}
Short Market Value: ${float(account.short_market_value):.2f}
Pattern Day Trader: {'Yes' if account.pattern_day_trader else 'No'}
Day Trades Remaining: {account.daytrade_count if hasattr(account, 'daytrade_count') else 'Unknown'}
"""
        return info
    except Exception as e:
        return f"Error getting account info: {str(e)}"

@mcp.tool()
async def get_positions(api_key: str, api_secret: str, paper: bool = True) -> str:
    """
    Get all current positions in the portfolio.
    
    Args:
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        positions = trading_client.get_all_positions()
        
        if not positions:
            return "No open positions found."
        
        result = "Current Positions:\n-------------------\n"
        for position in positions:
            result += f"""
Symbol: {position.symbol}
Quantity: {position.qty} shares
Market Value: ${float(position.market_value):.2f}
Average Entry Price: ${float(position.avg_entry_price):.2f}
Current Price: ${float(position.current_price):.2f}
Unrealized P/L: ${float(position.unrealized_pl):.2f} ({float(position.unrealized_plpc) * 100:.2f}%)
-------------------
"""
        return result
    except Exception as e:
        return f"Error getting positions: {str(e)}"

# Market data tools
@mcp.tool()
async def get_stock_quote(symbol: str, api_key: str, api_secret: str) -> str:
    """
    Get the latest quote for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
    """
    try:
        stock_client = StockHistoricalDataClient(api_key, api_secret)
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = stock_client.get_stock_latest_quote(request_params)
        
        if symbol in quotes:
            quote = quotes[symbol]
            return f"""
Latest Quote for {symbol}:
------------------------
Ask Price: ${quote.ask_price:.2f}
Bid Price: ${quote.bid_price:.2f}
Ask Size: {quote.ask_size}
Bid Size: {quote.bid_size}
Timestamp: {quote.timestamp}
"""
        else:
            return f"No quote data found for {symbol}."
    except Exception as e:
        return f"Error fetching quote for {symbol}: {str(e)}"

@mcp.tool()
async def get_stock_bars(symbol: str, api_key: str, api_secret: str, days: int = 5) -> str:
    """
    Get historical price bars for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        days: Number of trading days to look back (default: 5)
    """
    try:
        stock_client = StockHistoricalDataClient(api_key, api_secret)
        start_time = datetime.now() - timedelta(days=days)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_time
        )
        
        bars = stock_client.get_stock_bars(request_params)
        
        if symbol in bars and bars[symbol]:
            result = f"Historical Data for {symbol} (Last {days} trading days):\n"
            result += "---------------------------------------------------\n"
            
            for bar in bars[symbol]:
                result += f"Date: {bar.timestamp.date()}, Open: ${bar.open:.2f}, High: ${bar.high:.2f}, Low: ${bar.low:.2f}, Close: ${bar.close:.2f}, Volume: {bar.volume}\n"
            
            return result
        else:
            return f"No historical data found for {symbol} in the last {days} days."
    except Exception as e:
        return f"Error fetching historical data for {symbol}: {str(e)}"

# Order management tools
@mcp.tool()
async def get_orders(api_key: str, api_secret: str, paper: bool = True, status: str = "all", limit: int = 10) -> str:
    """
    Get orders with the specified status.
    
    Args:
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
        status: Order status to filter by (open, closed, all)
        limit: Maximum number of orders to return (default: 10)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        
        if status.lower() == "open":
            query_status = QueryOrderStatus.OPEN
        elif status.lower() == "closed":
            query_status = QueryOrderStatus.CLOSED
        else:
            query_status = QueryOrderStatus.ALL
            
        request_params = GetOrdersRequest(
            status=query_status,
            limit=limit
        )
        
        orders = trading_client.get_orders(request_params)
        
        if not orders:
            return f"No {status} orders found."
        
        result = f"{status.capitalize()} Orders (Last {len(orders)}):\n"
        result += "-----------------------------------\n"
        
        for order in orders:
            result += f"""
Symbol: {order.symbol}
ID: {order.id}
Type: {order.type}
Side: {order.side}
Quantity: {order.qty}
Status: {order.status}
Submitted At: {order.submitted_at}
"""
            if hasattr(order, 'filled_at') and order.filled_at:
                result += f"Filled At: {order.filled_at}\n"
                
            if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
                result += f"Filled Price: ${float(order.filled_avg_price):.2f}\n"
                
            result += "-----------------------------------\n"
            
        return result
    except Exception as e:
        return f"Error fetching orders: {str(e)}"

@mcp.tool()
async def place_market_order(symbol: str, side: str, quantity: float, api_key: str, api_secret: str, paper: bool = True) -> str:
    """
    Place a market order.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        side: Order side (buy or sell)
        quantity: Number of shares to buy or sell
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        
        if side.lower() == "buy":
            order_side = OrderSide.BUY
        elif side.lower() == "sell":
            order_side = OrderSide.SELL
        else:
            return f"Invalid order side: {side}. Must be 'buy' or 'sell'."
        
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        
        order = trading_client.submit_order(order_data)
        
        return f"""
Market Order Placed Successfully:
--------------------------------
Order ID: {order.id}
Symbol: {order.symbol}
Side: {order.side}
Quantity: {order.qty}
Type: {order.type}
Time In Force: {order.time_in_force}
Status: {order.status}
"""
    except Exception as e:
        return f"Error placing market order: {str(e)}"

@mcp.tool()
async def place_limit_order(symbol: str, side: str, quantity: float, limit_price: float, api_key: str, api_secret: str, paper: bool = True) -> str:
    """
    Place a limit order.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        side: Order side (buy or sell)
        quantity: Number of shares to buy or sell
        limit_price: Limit price for the order
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        
        if side.lower() == "buy":
            order_side = OrderSide.BUY
        elif side.lower() == "sell":
            order_side = OrderSide.SELL
        else:
            return f"Invalid order side: {side}. Must be 'buy' or 'sell'."
        
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
        
        order = trading_client.submit_order(order_data)
        
        return f"""
Limit Order Placed Successfully:
-------------------------------
Order ID: {order.id}
Symbol: {order.symbol}
Side: {order.side}
Quantity: {order.qty}
Type: {order.type}
Limit Price: ${float(order.limit_price):.2f}
Time In Force: {order.time_in_force}
Status: {order.status}
"""
    except Exception as e:
        return f"Error placing limit order: {str(e)}"

@mcp.tool()
async def cancel_all_orders(api_key: str, api_secret: str, paper: bool = True) -> str:
    """
    Cancel all open orders.
    
    Args:
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        cancel_statuses = trading_client.cancel_orders()
        return f"Successfully canceled all open orders. Status: {cancel_statuses}"
    except Exception as e:
        return f"Error canceling orders: {str(e)}"

# Account management tools
@mcp.tool()
async def close_all_positions(api_key: str, api_secret: str, paper: bool = True, cancel_orders: bool = True) -> str:
    """
    Close all open positions.
    
    Args:
        api_key: Alpaca API key ID
        api_secret: Alpaca API secret key
        paper: Whether to use paper trading (default: True)
        cancel_orders: Whether to cancel all open orders before closing positions (default: True)
    """
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        trading_client.close_all_positions(cancel_orders=cancel_orders)
        return "Successfully closed all positions."
    except Exception as e:
        return f"Error closing positions: {str(e)}"

# Run the server
if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        # Let the inspector handle the transport
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)