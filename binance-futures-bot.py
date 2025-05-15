import time
import json
import logging
import threading
import random
import requests
import hmac
import hashlib
import urllib.parse
import queue
import asyncio
import numpy as np
import pandas as pd
# Import pandas_ta instead of talib
import pandas_ta as ta
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup,  constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======== BOT CONFIGURATION ========
# Replace these values with your own
TELEGRAM_BOT_TOKEN = "BOT_TOKEN"  # Replace with your bot token
ADMIN_USER_IDS = [1272488609]    # Replace with your Telegram user ID(s)
# ==================================

# Binance API configuration
BINANCE_API_KEY = "API"  # Your Binance API key
BINANCE_API_SECRET = "API" 
BINANCE_API_URL = "https://fapi.binance.com"  # Futures API URL
BINANCE_TEST_API_URL = "https://testnet.binancefuture.com"  # Testnet URL for testing

# Trading modes
TRADING_MODES = {
    "safe": {
        "leverage": 5,
        "take_profit": 0.6,  # 0.6% take profit
        "stop_loss": 0.3,    # 0.3% stop loss
        "position_size_percent": 10,  # 10% of available balance
        "max_daily_trades": 10,
        "description": "Safe mode with lower risk and conservative profit targets"
    },
    "standard": {
        "leverage": 10,
        "take_profit": 1.0,  # 1.0% take profit
        "stop_loss": 0.5,    # 0.5% stop loss
        "position_size_percent": 15,  # 15% of available balance
        "max_daily_trades": 15,
        "description": "Standard mode with balanced risk and profit targets"
    },
    "aggressive": {
        "leverage": 20,
        "take_profit": 1.5,  # 1.5% take profit
        "stop_loss": 0.7,    # 0.7% stop loss
        "position_size_percent": 20,  # 20% of available balance
        "max_daily_trades": 20,
        "description": "Aggressive mode with higher risk and profit targets"
    }
}

# Technical indicator settings
INDICATOR_SETTINGS = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ema_short": 20,
    "ema_long": 50,
    "bb_period": 20,
    "bb_std": 2.0,
    "signal_check_interval": 30,  # Check for signals every 30 seconds
    "candle_timeframe": "5m"  # 5-minute candles
}

# Bot configuration
CONFIG = {
    "api_key": BINANCE_API_KEY,
    "api_secret": BINANCE_API_SECRET,
    "trading_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"],  # Default trading pairs
    "position_size_usdt": 100,  # Default position size in USDT
    "use_percentage": True,  # Whether to use percentage of balance
    "position_size_percentage": 10.0,  # Percentage of balance to use (10%)
    "take_profit": 0.6,       # percentage
    "stop_loss": 0.3,         # percentage
    "trading_enabled": True,
    "trading_mode": "safe",     # Current trading mode
    "max_daily_trades": 10,    # Maximum number of trades per day
    "signal_check_interval": 30,  # Check for signals every 30 seconds
    "use_testnet": False,        # Use Binance testnet for testing
    "use_real_trading": True,  # Set to True to enable real trading with Binance API
    "daily_profit_target": 5.0,    # Daily profit target in percentage
    "daily_loss_limit": 3.0,       # Daily loss limit in percentage
    "hedge_mode": True,            # Use hedge mode (separate long and short positions)
    "leverage": 5                  # Default leverage
}

# Active trades and daily statistics
ACTIVE_TRADES = []
COMPLETED_TRADES = []
DAILY_STATS = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "total_trades": 0,
    "winning_trades": 0,
    "losing_trades": 0,
    "total_profit_pct": 0.0,
    "total_profit_usdt": 0.0,
    "starting_balance": 0.0,
    "current_balance": 0.0,
    "roi": 0.0
}

# Symbol information cache
SYMBOL_INFO = {}

class BinanceFuturesAPI:
    def __init__(self, config):
        self.config = config
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.base_url = BINANCE_TEST_API_URL if config["use_testnet"] else BINANCE_API_URL

    def _generate_signature(self, data):
        """Generate HMAC SHA256 signature for Binance API"""
        query_string = urllib.parse.urlencode(data)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self):
        """Get headers for Binance API requests"""
        return {
            'X-MBX-APIKEY': self.api_key
        }

    def get_exchange_info(self):
        """Get exchange information"""
        try:
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get exchange info: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            return None

    def get_account_info(self):
        """Get account information"""
        try:
            url = f"{self.base_url}/fapi/v2/account"
            timestamp = int(time.time() * 1000)
            params = {
                'timestamp': timestamp
            }
            params['signature'] = self._generate_signature(params)

            headers = self._get_headers()

            response = requests.get(url, params=params, headers=headers)

            if response.status_code != 200:
                logger.error(f"API error response: {response.text}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("Authentication failed: Invalid API key or secret")
                return None
            elif response.status_code == 403:
                logger.error("Forbidden: This API key doesn't have permission to access this resource")
                return None
            else:
                logger.error(f"Failed to get account info: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_ticker_price(self, symbol):
        """Get current price for a symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/ticker/price"
            params = {'symbol': symbol}

            response = requests.get(url, params=params)
            if response.status_code == 200:
                return float(response.json()['price'])
            else:
                logger.error(f"Failed to get ticker price: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting ticker price: {e}")
            return None

    def get_klines(self, symbol, interval, limit=100):
        """Get klines/candlestick data"""
        try:
            url = f"{self.base_url}/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                # Convert to pandas DataFrame for easier manipulation
                data = response.json()
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                                'close_time', 'quote_asset_volume', 'number_of_trades', 
                                                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
                
                # Convert string values to float for calculations
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                return df
            else:
                logger.error(f"Failed to get klines: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting klines: {e}")
            return None

    def change_leverage(self, symbol, leverage):
        """Change leverage for a symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/leverage"
            timestamp = int(time.time() * 1000)
            params = {
                'symbol': symbol,
                'leverage': leverage,
                'timestamp': timestamp
            }
            params['signature'] = self._generate_signature(params)

            response = requests.post(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                logger.info(f"Changed leverage for {symbol} to {leverage}x")
                return response.json()
            else:
                logger.error(f"Failed to change leverage: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error changing leverage: {e}")
            return None

    def change_margin_type(self, symbol, margin_type):
        """Change margin type for a symbol (ISOLATED or CROSSED)"""
        try:
            url = f"{self.base_url}/fapi/v1/marginType"
            timestamp = int(time.time() * 1000)
            params = {
                'symbol': symbol,
                'marginType': margin_type,  # ISOLATED or CROSSED
                'timestamp': timestamp
            }
            params['signature'] = self._generate_signature(params)

            response = requests.post(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                logger.info(f"Changed margin type for {symbol} to {margin_type}")
                return response.json()
            elif "already" in response.text:
                # Already in this margin type, not an error
                return {"msg": f"Margin type already set to {margin_type}"}
            else:
                logger.error(f"Failed to change margin type: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error changing margin type: {e}")
            return None

    def get_position_mode(self):
        """Get position mode (Hedge Mode or One-way Mode)"""
        try:
            url = f"{self.base_url}/fapi/v1/positionSide/dual"
            timestamp = int(time.time() * 1000)
            params = {
                'timestamp': timestamp
            }
            params['signature'] = self._generate_signature(params)

            response = requests.get(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get position mode: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting position mode: {e}")
            return None

    def change_position_mode(self, dual_side_position):
        """Change position mode (Hedge Mode or One-way Mode)"""
        try:
            url = f"{self.base_url}/fapi/v1/positionSide/dual"
            timestamp = int(time.time() * 1000)
            params = {
                'dualSidePosition': 'true' if dual_side_position else 'false',
                'timestamp': timestamp
            }
            params['signature'] = self._generate_signature(params)

            response = requests.post(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                mode = "Hedge Mode" if dual_side_position else "One-way Mode"
                logger.info(f"Changed position mode to {mode}")
                return response.json()
            elif "already" in response.text:
                # Already in this mode, not an error
                return {"msg": "Position mode already set"}
            else:
                logger.error(f"Failed to change position mode: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error changing position mode: {e}")
            return None

    def create_order(self, symbol, side, order_type, quantity=None, price=None, 
                    stop_price=None, position_side=None, reduce_only=False, 
                    time_in_force="GTC", close_position=False):
        """Create a new order"""
        try:
            url = f"{self.base_url}/fapi/v1/order"
            timestamp = int(time.time() * 1000)

            params = {
                'symbol': symbol,
                'side': side,  # BUY or SELL
                'type': order_type,  # LIMIT, MARKET, STOP, TAKE_PROFIT, etc.
                'timestamp': timestamp,
                'timeInForce': time_in_force  # GTC, IOC, FOK
            }

            if quantity:
                params['quantity'] = quantity

            if price and order_type not in ['MARKET', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                params['price'] = price

            if stop_price and order_type in ['STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']:
                params['stopPrice'] = stop_price

            if position_side:
                params['positionSide'] = position_side  # LONG or SHORT

            if reduce_only:
                params['reduceOnly'] = 'true'

            if close_position:
                params['closePosition'] = 'true'

            params['signature'] = self._generate_signature(params)

            response = requests.post(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                logger.info(f"Created order: {symbol} {side} {order_type} {quantity}")
                return response.json()
            else:
                logger.error(f"Failed to create order: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None

    def get_open_positions(self):
        """Get all open positions"""
        try:
            account_info = self.get_account_info()
            if account_info and 'positions' in account_info:
                # Filter positions with non-zero amount
                open_positions = [p for p in account_info['positions'] if float(p['positionAmt']) != 0]
                return open_positions
            return []
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

    def get_open_orders(self, symbol=None):
        """Get all open orders for a symbol or all symbols"""
        try:
            url = f"{self.base_url}/fapi/v1/openOrders"
            timestamp = int(time.time() * 1000)

            params = {
                'timestamp': timestamp
            }

            if symbol:
                params['symbol'] = symbol

            params['signature'] = self._generate_signature(params)

            response = requests.get(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get open orders: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return None

    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        """Cancel an order"""
        try:
            url = f"{self.base_url}/fapi/v1/order"
            timestamp = int(time.time() * 1000)

            params = {
                'symbol': symbol,
                'timestamp': timestamp
            }

            if order_id:
                params['orderId'] = order_id
            elif orig_client_order_id:
                params['origClientOrderId'] = orig_client_order_id
            else:
                logger.error("Either orderId or origClientOrderId must be provided")
                return None

            params['signature'] = self._generate_signature(params)

            response = requests.delete(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to cancel order: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return None

    def cancel_all_orders(self, symbol):
        """Cancel all orders for a symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/allOpenOrders"
            timestamp = int(time.time() * 1000)

            params = {
                'symbol': symbol,
                'timestamp': timestamp
            }

            params['signature'] = self._generate_signature(params)

            response = requests.delete(url, params=params, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to cancel all orders: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error canceling all orders: {e}")
            return None

    def get_symbol_info(self, symbol):
        """Get symbol information including precision"""
        global SYMBOL_INFO
        
        # Return from cache if available
        if symbol in SYMBOL_INFO:
            return SYMBOL_INFO[symbol]
            
        try:
            exchange_info = self.get_exchange_info()
            if not exchange_info:
                return None
                
            for sym_info in exchange_info['symbols']:
                if sym_info['symbol'] == symbol:
                    # Cache the result
                    SYMBOL_INFO[symbol] = {
                        'pricePrecision': sym_info['pricePrecision'],
                        'quantityPrecision': sym_info['quantityPrecision'],
                        'minQty': next((f['minQty'] for f in sym_info['filters'] if f['filterType'] == 'LOT_SIZE'), '0.001'),
                        'tickSize': next((f['tickSize'] for f in sym_info['filters'] if f['filterType'] == 'PRICE_FILTER'), '0.01'),
                        'minNotional': next((f['notional'] for f in sym_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), '10')
                    }
                    return SYMBOL_INFO[symbol]
            
            logger.error(f"Symbol {symbol} not found in exchange info")
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def round_step_size(self, quantity, step_size):
        """Round quantity to step size"""
        step_size_decimal = self.get_decimal_places(step_size)
        return round(quantity - (quantity % float(step_size)), step_size_decimal)

    def get_decimal_places(self, value):
        """Get decimal places in a number"""
        value_str = str(value)
        if '.' in value_str:
            return len(value_str.split('.')[1])
        return 0

    def round_price(self, symbol, price):
        """Round price according to symbol's price precision"""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            # Default to 2 decimal places if we can't get the info
            return round(price, 2)
        
        price_precision = symbol_info['pricePrecision']
        return round(price, price_precision)

    def round_quantity(self, symbol, quantity):
        """Round quantity according to symbol's quantity precision"""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            # Default to 3 decimal places if we can't get the info
            return round(quantity, 3)
        
        quantity_precision = symbol_info['quantityPrecision']
        return round(quantity, quantity_precision)

    def get_balance(self):
        """Get USDT balance"""
        try:
            account_info = self.get_account_info()
            if account_info and 'assets' in account_info:
                for asset in account_info['assets']:
                    if asset['asset'] == 'USDT':
                        return {
                            'total': float(asset['walletBalance']),
                            'available': float(asset['availableBalance']),
                            'unrealized_pnl': float(asset['unrealizedProfit'])
                        }
            return None
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None

class TechnicalAnalysis:
    def __init__(self, binance_api):
        self.binance_api = binance_api
        self.settings = INDICATOR_SETTINGS

    def calculate_indicators(self, symbol, timeframe=None):
        """Calculate technical indicators for a symbol using pandas_ta instead of talib"""
        if not timeframe:
            timeframe = self.settings['candle_timeframe']
            
        # Get klines data
        df = self.binance_api.get_klines(symbol, timeframe, limit=100)
        if df is None or len(df) < 50:  # Need enough data for indicators
            logger.error(f"Not enough data for {symbol} to calculate indicators")
            return None
            
        # Calculate RSI using pandas_ta
        df['rsi'] = ta.rsi(df['close'], length=self.settings['rsi_period'])
        
        # Calculate EMAs using pandas_ta
        df['ema_short'] = ta.ema(df['close'], length=self.settings['ema_short'])
        df['ema_long'] = ta.ema(df['close'], length=self.settings['ema_long'])
        
        # Calculate Bollinger Bands using pandas_ta
        bb = ta.bbands(df['close'], length=self.settings['bb_period'], std=self.settings['bb_std'])
        df['bb_upper'] = bb['BBU_' + str(self.settings['bb_period']) + '_' + str(self.settings['bb_std'])]
        df['bb_middle'] = bb['BBM_' + str(self.settings['bb_period']) + '_' + str(self.settings['bb_std'])]
        df['bb_lower'] = bb['BBL_' + str(self.settings['bb_period']) + '_' + str(self.settings['bb_std'])]
        
        # Determine candle color (green/red)
        df['candle_color'] = np.where(df['close'] >= df['open'], 'green', 'red')
        
        # Calculate candle size
        df['candle_size'] = abs(df['close'] - df['open'])
        df['candle_size_pct'] = df['candle_size'] / df['open'] * 100
        
        # Get the latest data
        latest = df.iloc[-1].copy()
        previous = df.iloc[-2].copy() if len(df) > 1 else None
        
        return {
            'symbol': symbol,
            'timestamp': latest['timestamp'],
            'close': latest['close'],
            'rsi': latest['rsi'],
            'ema_short': latest['ema_short'],
            'ema_long': latest['ema_long'],
            'bb_upper': latest['bb_upper'],
            'bb_middle': latest['bb_middle'],
            'bb_lower': latest['bb_lower'],
            'candle_color': latest['candle_color'],
            'candle_size_pct': latest['candle_size_pct'],
            'previous': previous,
            'df': df  # Include full dataframe for additional analysis if needed
        }

    def get_signal(self, symbol, timeframe=None):
        """Get trading signal based on technical indicators"""
        indicators = self.calculate_indicators(symbol, timeframe)
        if not indicators:
            return None
            
        signal = {
            'symbol': symbol,
            'timestamp': indicators['timestamp'],
            'price': indicators['close'],
            'action': 'WAIT',  # Default action
            'strength': 0,     # Signal strength (0-100)
            'reasons': []      # Reasons for the signal
        }
        
        # RSI + Candle Color Strategy
        if indicators['rsi'] < self.settings['rsi_oversold'] and indicators['candle_color'] == 'green':
            signal['action'] = 'LONG'
            signal['strength'] += 30
            signal['reasons'].append(f"RSI oversold ({indicators['rsi']:.2f}) with green candle")
            
        elif indicators['rsi'] > self.settings['rsi_overbought'] and indicators['candle_color'] == 'red':
            signal['action'] = 'SHORT'
            signal['strength'] += 30
            signal['reasons'].append(f"RSI overbought ({indicators['rsi']:.2f}) with red candle")
            
        # EMA Strategy
        if indicators['close'] > indicators['ema_short'] > indicators['ema_long']:
            # Price above short EMA, short EMA above long EMA = bullish
            if signal['action'] == 'LONG':
                signal['strength'] += 20
                signal['reasons'].append("EMA alignment confirms bullish trend")
            elif signal['action'] == 'WAIT':
                signal['action'] = 'LONG'
                signal['strength'] += 20
                signal['reasons'].append("EMA alignment suggests bullish trend")
                
        elif indicators['close'] < indicators['ema_short'] < indicators['ema_long']:
            # Price below short EMA, short EMA below long EMA = bearish
            if signal['action'] == 'SHORT':
                signal['strength'] += 20
                signal['reasons'].append("EMA alignment confirms bearish trend")
            elif signal['action'] == 'WAIT':
                signal['action'] = 'SHORT'
                signal['strength'] += 20
                signal['reasons'].append("EMA alignment suggests bearish trend")
                
        # Bollinger Band Breakout Strategy
        if indicators['close'] > indicators['bb_upper']:
            # Price above upper band = potential short (overbought)
            if signal['action'] == 'SHORT':
                signal['strength'] += 20
                signal['reasons'].append("Price above upper Bollinger Band")
            elif signal['action'] == 'WAIT':
                signal['action'] = 'SHORT'
                signal['strength'] += 15
                signal['reasons'].append("Price above upper Bollinger Band")
                
        elif indicators['close'] < indicators['bb_lower']:
            # Price below lower band = potential long (oversold)
            if signal['action'] == 'LONG':
                signal['strength'] += 20
                signal['reasons'].append("Price below lower Bollinger Band")
            elif signal['action'] == 'WAIT':
                signal['action'] = 'LONG'
                signal['strength'] += 15
                signal['reasons'].append("Price below lower Bollinger Band")
                
        # If signal strength is too low, revert to WAIT
        if signal['strength'] < 30:
            signal['action'] = 'WAIT'
            signal['reasons'] = ["Signal strength too low"]
            
        return signal

class TradingBot:
    def __init__(self, config, telegram_bot=None):
        self.config = config
        self.telegram_bot = telegram_bot
        self.running = False
        self.trading_thread = None
        self.signal_check_thread = None
        self.notification_queue = queue.Queue()
        self.notification_thread = None
        self.binance_api = BinanceFuturesAPI(config) if config["api_key"] and config["api_secret"] else None
        self.technical_analysis = TechnicalAnalysis(self.binance_api) if self.binance_api else None
        
        # Initialize daily stats
        self.reset_daily_stats()

    def reset_daily_stats(self):
        """Reset daily statistics"""
        DAILY_STATS["date"] = datetime.now().strftime("%Y-%m-%d")
        DAILY_STATS["total_trades"] = 0
        DAILY_STATS["winning_trades"] = 0
        DAILY_STATS["losing_trades"] = 0
        DAILY_STATS["total_profit_pct"] = 0.0
        DAILY_STATS["total_profit_usdt"] = 0.0
        
        # Get current balance if available
        if self.binance_api and self.config["use_real_trading"]:
            try:
                balance = self.binance_api.get_balance()
                if balance:
                    DAILY_STATS["starting_balance"] = balance['total']
                    DAILY_STATS["current_balance"] = balance['total']
            except Exception as e:
                logger.error(f"Error getting balance for daily stats: {e}")
                DAILY_STATS["starting_balance"] = 0.0
                DAILY_STATS["current_balance"] = 0.0
        else:
            DAILY_STATS["starting_balance"] = 0.0
            DAILY_STATS["current_balance"] = 0.0

    def send_notification(self, message, keyboard=None):
        """Send notification to all admin chat IDs"""
        if not self.telegram_bot:
            logger.warning("Cannot send notification: Telegram bot not initialized")
            return
        
        if not hasattr(self.telegram_bot, 'admin_chat_ids') or not self.telegram_bot.admin_chat_ids:
            logger.warning("Cannot send notification: No admin chat IDs available")
            return
        
        # Add to queue for processing by notification thread
        try:
            self.notification_queue.put((message, keyboard))
            logger.info(f"Added notification to queue: {message[:30]}...")
        except Exception as e:
            logger.error(f"Error queueing notification: {e}")

    def process_notification_queue(self):
        """Process the notification queue in a separate thread"""
        logger.info("Starting notification queue processor thread")

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.running: # Check self.running to allow graceful shutdown
            try:
                # Get the next notification from the queue (blocking with timeout)
                message, keyboard = self.notification_queue.get(block=True, timeout=1.0)

                if message is None and keyboard is None: # Sentinel for stopping
                    logger.info("Notification processor received stop signal.")
                    break

                # Log that we're processing a notification
                # logger.info(f"Processing notification: {message[:30]}...") # Optional

                if not self.telegram_bot or not hasattr(self.telegram_bot, 'admin_chat_ids') or not self.telegram_bot.admin_chat_ids:
                    logger.error("Cannot send notification: Telegram bot not initialized or no admin chat IDs")
                    self.notification_queue.task_done()
                    time.sleep(1) # Brief pause if misconfigured
                    continue

                for chat_id in self.telegram_bot.admin_chat_ids:
                    try:
                        # First try with asyncio.run_coroutine_threadsafe
                        coro_payload = {
                            'chat_id': chat_id,
                            'text': message,
                            'parse_mode': constants.ParseMode.HTML # Good practice
                        }
                        if keyboard:
                            coro_payload['reply_markup'] = InlineKeyboardMarkup(keyboard)
                        
                        future = asyncio.run_coroutine_threadsafe(
                            self.telegram_bot.application.bot.send_message(**coro_payload),
                            loop
                        )
                        future.result(timeout=10) # Wait for the result (with timeout)
                        # logger.info(f"Sent notification to {chat_id} via asyncio") # Optional
                    
                    except Exception as e1:
                        logger.error(f"Failed to send notification using asyncio to {chat_id}: {e1}. Trying fallback.")

                        # Fallback: Try using requests directly
                        try:
                            token = None
                            if hasattr(self.telegram_bot, 'token'):
                                token = self.telegram_bot.token
                            elif hasattr(self.telegram_bot.application, 'bot') and hasattr(self.telegram_bot.application.bot, '_token'): # PTB v20+
                                token = self.telegram_bot.application.bot._token
                            elif hasattr(self.telegram_bot.application, 'token'): # Older PTB
                                token = self.telegram_bot.application.token


                            if not token:
                                logger.error("Could not find Telegram token for fallback.")
                                raise Exception("Telegram token not found")

                            url = f"https://api.telegram.org/bot{token}/sendMessage"
                            payload = {
                                'chat_id': chat_id,
                                'text': message,
                                'parse_mode': 'HTML'
                            }

                            if keyboard:
                                keyboard_json = []
                                for row in keyboard:
                                    keyboard_row = []
                                    for button in row:
                                        keyboard_row.append({
                                            'text': button.text,
                                            'callback_data': button.callback_data
                                        })
                                    keyboard_json.append(keyboard_row)
                                payload['reply_markup'] = json.dumps({'inline_keyboard': keyboard_json})

                            response = requests.post(url, json=payload, timeout=10)
                            if response.status_code == 200:
                                logger.info(f"Sent notification to {chat_id} using fallback requests.")
                            else:
                                logger.error(f"Fallback requests failed for {chat_id} with status {response.status_code}: {response.text}")
                                # raise Exception(f"HTTP error: {response.status_code}") # Don't re-raise, just log
                        except Exception as e2:
                            logger.error(f"Fallback requests method also failed for {chat_id}: {e2}")
                
                self.notification_queue.task_done()
                # time.sleep(0.1) # Small optional delay

            except queue.Empty:
                if not self.running and self.notification_queue.empty(): # Check if bot is stopped and queue is empty
                    break
                continue # Loop again if queue is empty but bot is running
            except Exception as e:
                logger.error(f"Error processing notification queue: {e}", exc_info=True)
                if not self.running: # If critical error and bot should stop
                    break
                time.sleep(5)
        
        loop.close()
        logger.info("Notification queue processor thread stopped.")
    def start_trading(self):
        """Start the trading bot"""
        if not self.running:
            self.running = True

            # Apply trading mode settings
            self.apply_trading_mode_settings()

            # Set up hedge mode if enabled
            if self.config["hedge_mode"] and self.binance_api:
                self.binance_api.change_position_mode(True)

            # Start the signal check thread
            self.signal_check_thread = threading.Thread(target=self.signal_check_loop)
            self.signal_check_thread.daemon = True
            self.signal_check_thread.start()
            
            # Start the notification processor thread
            self.notification_thread = threading.Thread(target=self.process_notification_queue)
            self.notification_thread.daemon = True
            self.notification_thread.start()

            # Reset daily stats when starting trading
            self.reset_daily_stats()
            
            # Send notification that bot has started
            self.send_notification(
                f"🚀 Trading Bot Started\n\n"
                f"Mode: {self.config['trading_mode'].capitalize()}\n"
                f"Leverage: {self.config['leverage']}x\n"
                f"Take Profit: {self.config['take_profit']}%\n"
                f"Stop Loss: {self.config['stop_loss']}%\n"
                f"Position Size: {self.config['position_size_percentage']}% of balance\n"
                f"Daily Profit Target: {self.config['daily_profit_target']}%\n"
                f"Daily Loss Limit: {self.config['daily_loss_limit']}%\n"
                f"Trading Pairs: {', '.join(self.config['trading_pairs'])}\n"
                f"Real Trading: {'Enabled' if self.config['use_real_trading'] else 'Disabled (Simulation)'}"
            )

            return True
        return False

    def stop_trading(self):
        if not self.running:
            logger.info("Trading bot is not running.")
            return False # Not running
            
        logger.info("Stopping trading bot...")
        self.running = False # Signal threads to stop

        if self.signal_check_thread and self.signal_check_thread.is_alive():
            try:
                # No specific signal needed for signal_check_thread if it checks self.running
                self.signal_check_thread.join(timeout=self.config["signal_check_interval"] + 2.0) # Wait for it to finish current iteration + buffer
                if self.signal_check_thread.is_alive():
                    logger.warning("Signal check thread did not terminate in time.")
                else:
                    logger.info("Signal check thread joined.")
            except Exception as e:
                logger.error(f"Error joining signal_check_thread: {e}")
        
        if self.notification_thread and self.notification_thread.is_alive():
            try:
                self.notification_queue.put((None, None)) # Send sentinel to notification queue
                self.notification_thread.join(timeout=7.0) # Give a bit more time for final msgs + sentinel
                if self.notification_thread.is_alive():
                    logger.warning("Notification thread did not terminate in time.")
                else:
                    logger.info("Notification thread joined.")
            except Exception as e:
                logger.error(f"Error joining notification_thread: {e}")
        
        stop_message = "⏹️ <b>Trading Bot Stopped</b> ⏹️"
        # We try to send a final notification. Since the notification thread might be stopped,
        # this might not go through the queue as intended, but it's a best effort.
        # A more robust way for this final message would be to send it synchronously
        # before fully stopping the notification thread, or have the notification thread
        # send it upon receiving the sentinel. For now, this is a simple attempt.
        if self.telegram_bot and hasattr(self.telegram_bot, 'admin_chat_ids') and self.telegram_bot.admin_chat_ids:
             # Directly try to send without queueing if thread is likely down
            try:
                loop = asyncio.get_event_loop() # Try to get existing loop or new one
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                for chat_id in self.telegram_bot.admin_chat_ids:
                    coro = self.telegram_bot.application.bot.send_message(chat_id=chat_id, text=stop_message, parse_mode=constants.ParseMode.HTML)
                    if loop.is_running():
                         asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=5)
                    else:
                         loop.run_until_complete(coro) # If loop isn't running, run it for this
            except Exception as e:
                logger.error(f"Could not send final stop notification: {e}")


        logger.info("Trading bot stopped.")
        return True

    def apply_trading_mode_settings(self):
        """Apply settings from the selected trading mode"""
        mode = self.config["trading_mode"]
        if mode in TRADING_MODES:
            mode_settings = TRADING_MODES[mode]

            # Apply settings from the mode
            self.config["leverage"] = mode_settings["leverage"]
            self.config["take_profit"] = mode_settings["take_profit"]
            self.config["stop_loss"] = mode_settings["stop_loss"]
            self.config["position_size_percentage"] = mode_settings["position_size_percent"]
            self.config["max_daily_trades"] = mode_settings["max_daily_trades"]

            logger.info(f"Applied {mode} trading mode settings")

    def check_daily_limits(self):
        """Check if daily profit target or loss limit has been reached"""
        # If we have real trading enabled and have starting balance
        if DAILY_STATS["starting_balance"] > 0:
            current_profit_pct = (DAILY_STATS["current_balance"] - DAILY_STATS["starting_balance"]) / DAILY_STATS["starting_balance"] * 100
            
            # Check if we've hit the daily profit target
            if current_profit_pct >= self.config["daily_profit_target"]:
                logger.info(f"Daily profit target reached: {current_profit_pct:.2f}% >= {self.config['daily_profit_target']}%")
                self.send_notification(
                    f"🎯 DAILY PROFIT TARGET REACHED!\n\n"
                    f"Current profit: {current_profit_pct:.2f}%\n"
                    f"Target: {self.config['daily_profit_target']}%\n\n"
                    f"Trading will be paused for today. Use /starttrade to resume."
                )
                return False
            
            # Check if we've hit the daily loss limit
            if current_profit_pct <= -self.config["daily_loss_limit"]:
                logger.info(f"Daily loss limit reached: {current_profit_pct:.2f}% <= -{self.config['daily_loss_limit']}%")
                self.send_notification(
                    f"⚠️ DAILY LOSS LIMIT REACHED!\n\n"
                    f"Current loss: {current_profit_pct:.2f}%\n"
                    f"Limit: -{self.config['daily_loss_limit']}%\n\n"
                    f"Trading will be paused for today. Use /starttrade to resume."
                )
                return False
        
        return True

    def signal_check_loop(self):
        """Main loop to check for trading signals"""
        logger.info("Starting signal check loop")
        
        while self.running:
            try:
                # Check daily limits
                if not self.check_daily_limits():
                    self.stop_trading()
                    break
                    
                # Check if we've reached max daily trades
                if DAILY_STATS["total_trades"] >= self.config["max_daily_trades"]:
                    logger.info(f"Max daily trades reached: {DAILY_STATS['total_trades']} >= {self.config['max_daily_trades']}")
                    self.send_notification(
                        f"📊 MAX DAILY TRADES REACHED\n\n"
                        f"Trades today: {DAILY_STATS['total_trades']}\n"
                        f"Max allowed: {self.config['max_daily_trades']}\n\n"
                        f"Trading will be paused for today. Use /starttrade to resume."
                    )
                    self.stop_trading()
                    break
                
                # Check for signals on each trading pair
                for symbol in self.config["trading_pairs"]:
                    # Skip if we already have an active trade for this symbol
                    if any(t['symbol'] == symbol and not t.get('completed', False) for t in ACTIVE_TRADES):
                        continue
                        
                    # Get trading signal
                    signal = self.technical_analysis.get_signal(symbol)
                    if not signal or signal['action'] == 'WAIT':
                        continue
                        
                    # Process the signal
                    self.process_signal(signal)
                    
                # Sleep for the configured interval
                time.sleep(self.config["signal_check_interval"])
                
            except Exception as e:
                logger.error(f"Error in signal check loop: {e}")
                time.sleep(10)  # Sleep longer on error

    def process_signal(self, signal):
        """Process a trading signal"""
        symbol = signal['symbol']
        action = signal['action']
        price = signal['price']
        
        logger.info(f"Processing signal: {symbol} {action} at {price}")
        
        # Determine position side based on action
        position_side = "LONG" if action == "LONG" else "SHORT"
        
        # Determine order side based on action
        order_side = "BUY" if action == "LONG" else "SELL"
        
        # Calculate position size
        position_size = self.calculate_position_size(symbol, price)
        if not position_size:
            logger.error(f"Failed to calculate position size for {symbol}")
            return
            
        # Set leverage for the symbol
        if self.binance_api:
            self.binance_api.change_leverage(symbol, self.config["leverage"])
            
        # Create the trade
        trade = self.create_trade(symbol, action, position_side, order_side, price, position_size)
        if not trade:
            logger.error(f"Failed to create trade for {symbol}")
            return
            
        # Send notification about the new trade
        self.send_trade_notification(trade, signal['reasons'])

    def calculate_position_size(self, symbol, price):
        """Calculate position size based on balance and risk settings"""
        try:
            if not self.binance_api:
                # Default to config value if no API
                return self.config["position_size_usdt"] / price
                
            # Get current balance
            balance = self.binance_api.get_balance()
            if not balance:
                logger.error("Failed to get balance")
                return None
                
            # Calculate position size based on percentage of balance
            if self.config["use_percentage"]:
                position_size_usdt = balance['available'] * (self.config["position_size_percentage"] / 100)
            else:
                position_size_usdt = self.config["position_size_usdt"]
                
            # Calculate quantity based on price and leverage
            quantity = (position_size_usdt * self.config["leverage"]) / price
            
            # Round quantity according to symbol's precision
            quantity = self.binance_api.round_quantity(symbol, quantity)
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None

    def create_trade(self, symbol, action, position_side, order_side, price, quantity):
        """Create a new trade"""
        try:
            # Calculate take profit and stop loss prices
            take_profit_pct = self.config["take_profit"]
            stop_loss_pct = self.config["stop_loss"]
            
            if action == "LONG":
                take_profit_price = price * (1 + take_profit_pct / 100)
                stop_loss_price = price * (1 - stop_loss_pct / 100)
            else:  # SHORT
                take_profit_price = price * (1 - take_profit_pct / 100)
                stop_loss_price = price * (1 + stop_loss_pct / 100)
                
            # Round prices according to symbol's precision
            take_profit_price = self.binance_api.round_price(symbol, take_profit_price)
            stop_loss_price = self.binance_api.round_price(symbol, stop_loss_price)
            
            # Create the trade object
            trade = {
                'id': int(time.time()),
                'timestamp': time.time(),
                'symbol': symbol,
                'action': action,
                'position_side': position_side,
                'order_side': order_side,
                'entry_price': price,
                'quantity': quantity,
                'take_profit': take_profit_price,
                'stop_loss': stop_loss_price,
                'leverage': self.config["leverage"],
                'entry_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed': False,
                'mode': self.config['trading_mode'],
                'entry_order_id': None,
                'tp_order_id': None,
                'sl_order_id': None,
                'real_trade': self.config['use_real_trading']
            }
            
            # If using real trading with Binance API, create the actual orders
            if self.binance_api and self.config["use_real_trading"]:
                # Place entry order (MARKET)
                entry_order = self.binance_api.create_order(
                    symbol=symbol,
                    side=order_side,
                    order_type="MARKET",
                    quantity=quantity,
                    position_side=position_side
                )
                
                if not entry_order:
                    logger.error(f"Failed to create entry order for {symbol}")
                    return None
                    
                trade['entry_order_id'] = entry_order['orderId']
                
                # Wait a moment for the order to be executed
                time.sleep(1)
                
                # Place take profit order
                tp_order = self.binance_api.create_order(
                    symbol=symbol,
                    side="SELL" if order_side == "BUY" else "BUY",
                    order_type="TAKE_PROFIT_MARKET",
                    quantity=quantity,
                    stop_price=take_profit_price,
                    position_side=position_side,
                    reduce_only=True
                )
                
                if tp_order:
                    trade['tp_order_id'] = tp_order['orderId']
                
                # Place stop loss order
                sl_order = self.binance_api.create_order(
                    symbol=symbol,
                    side="SELL" if order_side == "BUY" else "BUY",
                    order_type="STOP_MARKET",
                    quantity=quantity,
                    stop_price=stop_loss_price,
                    position_side=position_side,
                    reduce_only=True
                )
                
                if sl_order:
                    trade['sl_order_id'] = sl_order['orderId']
            
            # Add the trade to the active trades list
            ACTIVE_TRADES.append(trade)
            
            # Update daily stats
            DAILY_STATS["total_trades"] += 1
            
            return trade
            
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            return None

    def send_trade_notification(self, trade, reasons):
        """Send notification about a new trade"""
        action_emoji = "🟢" if trade['action'] == "LONG" else "🔴"
        
        message = (
            f"{action_emoji} NEW {trade['action']} POSITION\n\n"
            f"Symbol: {trade['symbol']}\n"
            f"Entry Price: ${trade['entry_price']:.4f}\n"
            f"Quantity: {trade['quantity']}\n"
            f"Leverage: {trade['leverage']}x\n"
            f"Take Profit: ${trade['take_profit']:.4f} (+{self.config['take_profit']}%)\n"
            f"Stop Loss: ${trade['stop_loss']:.4f} (-{self.config['stop_loss']}%)\n"
            f"Time: {trade['entry_time']}\n"
            f"Mode: {self.config['trading_mode'].capitalize()}\n\n"
            f"Signal Reasons:\n"
        )
        
        for reason in reasons:
            message += f"• {reason}\n"
            
        message += f"\nReal Trade: {'Yes' if trade['real_trade'] else 'No (Simulation)'}"
        
        self.send_notification(message)

    def complete_trade(self, trade, exit_price, exit_reason):
        """Complete a trade with a result"""
        try:
            # Calculate profit/loss
            if trade['action'] == "LONG":
                profit_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
            else:  # SHORT
                profit_pct = ((trade['entry_price'] - exit_price) / trade['entry_price']) * 100
                
            # Apply leverage to profit percentage
            leveraged_profit_pct = profit_pct * trade['leverage']
            
            # Calculate profit in USDT
            position_value = trade['entry_price'] * trade['quantity']
            profit_usdt = position_value * (profit_pct / 100)
            
            # Update trade with completion details
            trade['completed'] = True
            trade['exit_price'] = exit_price
            trade['exit_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trade['profit_pct'] = profit_pct
            trade['leveraged_profit_pct'] = leveraged_profit_pct
            trade['profit_usdt'] = profit_usdt
            trade['exit_reason'] = exit_reason
            
            # Update daily stats
            DAILY_STATS["total_profit_pct"] += leveraged_profit_pct
            DAILY_STATS["total_profit_usdt"] += profit_usdt
            
            if profit_pct > 0:
                DAILY_STATS["winning_trades"] += 1
            else:
                DAILY_STATS["losing_trades"] += 1
                
            # Update current balance if we're using real trading
            if self.config["use_real_trading"] and DAILY_STATS["current_balance"] > 0:
                DAILY_STATS["current_balance"] += profit_usdt
                
            # Calculate ROI
            if DAILY_STATS["starting_balance"] > 0:
                DAILY_STATS["roi"] = (DAILY_STATS["current_balance"] - DAILY_STATS["starting_balance"]) / DAILY_STATS["starting_balance"] * 100
            
            # If this was a real trade, cancel any remaining orders
            if trade['real_trade'] and self.binance_api:
                if trade.get('tp_order_id'):
                    self.binance_api.cancel_order(trade['symbol'], order_id=trade['tp_order_id'])
                    
                if trade.get('sl_order_id'):
                    self.binance_api.cancel_order(trade['symbol'], order_id=trade['sl_order_id'])
            
            # Determine if win or loss
            is_win = profit_pct > 0
            result = "WIN" if is_win else "LOSS"
            emoji = "✅" if is_win else "❌"
            
            # Get reason text
            if exit_reason == "take_profit":
                reason_text = "Take Profit Hit"
            elif exit_reason == "stop_loss":
                reason_text = "Stop Loss Hit"
            elif exit_reason == "manual":
                reason_text = "Manual Close"
            else:
                reason_text = exit_reason
                
            # Send completion notification
            complete_message = (
                f"{emoji} TRADE COMPLETED - {result}\n\n"
                f"Symbol: {trade['symbol']}\n"
                f"Action: {trade['action']}\n"
                f"Entry Price: ${trade['entry_price']:.4f}\n"
                f"Exit Price: ${exit_price:.4f}\n"
                f"Profit/Loss: {profit_pct:.2f}% (Raw) / {leveraged_profit_pct:.2f}% (Leveraged)\n"
                f"Profit USDT: ${profit_usdt:.2f}\n"
                f"Quantity: {trade['quantity']}\n"
                f"Leverage: {trade['leverage']}x\n"
                f"Close Reason: {reason_text}\n"
                f"Entry Time: {trade['entry_time']}\n"
                f"Exit Time: {trade['exit_time']}\n"
                f"Duration: {int(time.time() - trade['timestamp'])} seconds\n"
                f"Mode: {trade.get('mode', 'Standard').capitalize()}\n"
                f"Real Trade: {'Yes' if trade.get('real_trade', False) else 'No (Simulation)'}"
            )
            
            self.send_notification(complete_message)
            
            # Move the trade from active to completed
            if trade in ACTIVE_TRADES:
                ACTIVE_TRADES.remove(trade)
                COMPLETED_TRADES.append(trade)
                
            return True
            
        except Exception as e:
            logger.error(f"Error completing trade: {e}")
            return False

    def get_daily_stats_message(self):
        """Get a formatted message with daily trading statistics"""
        win_rate = 0
        if DAILY_STATS["total_trades"] > 0:
            win_rate = (DAILY_STATS["winning_trades"] / DAILY_STATS["total_trades"]) * 100
            
        balance_change = 0
        if DAILY_STATS["starting_balance"] > 0:
            balance_change = ((DAILY_STATS["current_balance"] - DAILY_STATS["starting_balance"]) / DAILY_STATS["starting_balance"]) * 100
            
        stats_message = (
            f"📊 DAILY TRADING STATS - {DAILY_STATS['date']}\n\n"
            f"Total Trades: {DAILY_STATS['total_trades']}\n"
            f"Winning Trades: {DAILY_STATS['winning_trades']}\n"
            f"Losing Trades: {DAILY_STATS['losing_trades']}\n"
            f"Win Rate: {win_rate:.1f}%\n\n"
            f"Total Profit/Loss: {DAILY_STATS['total_profit_pct']:.2f}%\n"
            f"Total Profit USDT: ${DAILY_STATS['total_profit_usdt']:.2f}\n\n"
            f"Starting Balance: ${DAILY_STATS['starting_balance']:.2f}\n"
            f"Current Balance: ${DAILY_STATS['current_balance']:.2f}\n"
            f"Balance Change: {balance_change:.2f}%\n\n"
            f"Trading Mode: {self.config['trading_mode'].capitalize()}\n"
            f"Real Trading: {'Enabled' if self.config['use_real_trading'] else 'Disabled (Simulation)'}"
        )
        
        return stats_message

class TelegramBotHandler:
    def __init__(self, token, admin_ids):
        self.token = token
        self.admin_user_ids = admin_ids
        # Initialize admin_chat_ids with admin_user_ids to enable immediate notifications
        self.admin_chat_ids = admin_ids.copy()  # Use a copy of admin_user_ids
        self.trading_bot = None
        self.bot = None
        self.application = Application.builder().token(token).build()

        # Register handlers
        self.register_handlers()
        
        # Log the initialization
        logger.info(f"TelegramBotHandler initialized with admin chat IDs: {self.admin_chat_ids}")

    def register_handlers(self):
        """Register all command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("config", self.config_command))
        self.application.add_handler(CommandHandler("set", self.set_config_command))
        self.application.add_handler(CommandHandler("trades", self.trades_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("positions", self.positions_command))
        self.application.add_handler(CommandHandler("indicators", self.indicators_command))

        # Trading commands
        self.application.add_handler(CommandHandler("starttrade", self.start_trading_command))
        self.application.add_handler(CommandHandler("stoptrade", self.stop_trading_command))
        self.application.add_handler(CommandHandler("closeall", self.close_all_positions_command))

        # Settings commands
        self.application.add_handler(CommandHandler("setleverage", self.set_leverage_command))
        self.application.add_handler(CommandHandler("setmode", self.set_mode_command))
        self.application.add_handler(CommandHandler("addpair", self.add_pair_command))
        self.application.add_handler(CommandHandler("removepair", self.remove_pair_command))
        self.application.add_handler(CommandHandler("setprofit", self.set_profit_command))

        # Real trading commands
        self.application.add_handler(CommandHandler("enablereal", self.enable_real_trading_command))
        self.application.add_handler(CommandHandler("disablereal", self.disable_real_trading_command))
        self.application.add_handler(CommandHandler("toggletestnet", self.toggle_testnet_command))
        self.application.add_handler(CommandHandler("testapi", self.test_api_command))

        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Message handler for text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    def set_trading_bot(self, trading_bot):
        """Set the trading bot instance"""
        self.trading_bot = trading_bot
        self.bot = self.application.bot

    async def is_authorized(self, update: Update) -> bool:
        """Check if the user is authorized to use the bot"""
        user_id = update.effective_user.id
        if user_id not in self.admin_user_ids:
            await update.effective_chat.send_message(
                "⛔ You are not authorized to use this bot."
            )
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return False
        return True

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        if not await self.is_authorized(update):
            return

        chat_id = update.effective_chat.id
        if chat_id not in self.admin_chat_ids:
            self.admin_chat_ids.append(chat_id)
            logger.info(f"Added chat ID {chat_id} to admin chats. Current admin chats: {self.admin_chat_ids}")
        else:
            logger.info(f"Chat ID {chat_id} already in admin chats: {self.admin_chat_ids}")

        keyboard = [
            [InlineKeyboardButton("🔄 Start Trading", callback_data="select_trading_mode")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats"),
             InlineKeyboardButton("📈 Positions", callback_data="positions")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="config"),
             InlineKeyboardButton("📋 Status", callback_data="status")]
        ]

        await update.message.reply_text(
            "Welcome to the Binance Futures Trading Bot!\n\n"
            "This bot specializes in trading with:\n"
            "• Technical indicators (RSI, EMA, Bollinger Bands)\n"
            "• Automatic position sizing\n"
            "• Take profit and stop loss management\n"
            "• Daily profit/loss tracking\n\n"
            "Use /help to see available commands.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        if not await self.is_authorized(update):
            return

        help_text = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Show current bot status\n"
            "/config - Show current configuration\n"
            "/set [param] [value] - Set configuration parameter\n"
            "/trades - Show recent trades\n"
            "/stats - Show daily trading statistics\n"
            "/balance - Show your Binance account balance\n"
            "/positions - Show open positions\n"
            "/indicators [symbol] - Show technical indicators for a symbol\n\n"
            "Trading Commands:\n"
            "/starttrade - Start trading\n"
            "/stoptrade - Stop trading\n"
            "/closeall - Close all open positions\n\n"
            "Settings Commands:\n"
            "/setleverage [value] - Set leverage (e.g., /setleverage 10)\n"
            "/setmode [mode] - Set trading mode (safe, standard, aggressive)\n"
            "/addpair [symbol] - Add trading pair (e.g., /addpair BTCUSDT)\n"
            "/removepair [symbol] - Remove trading pair\n"
            "/setprofit [target] [limit] - Set daily profit target and loss limit\n\n"
            "Real Trading Commands:\n"
            "/enablereal - Enable real trading with Binance API\n"
            "/disablereal - Disable real trading (simulation only)\n"
            "/toggletestnet - Switch between Binance Testnet and Production\n"
            "/testapi - Test your Binance API connection\n"
        )
        await update.message.reply_text(help_text)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return

        message_object_to_interact_with = update.callback_query.message if update.callback_query else update.message
        
        if not message_object_to_interact_with:
            logger.error("status_command: Could not determine message object from update.")
            if update.effective_chat:
                await update.effective_chat.send_text("Error: Could not process status request.")
            return

        if not self.trading_bot:
            await message_object_to_interact_with.reply_text("Trading bot not initialized.")
            return

        active_trades = [t for t in ACTIVE_TRADES if not t.get('completed', False)]
        completed_trades = COMPLETED_TRADES

        total_profit_pct = 0
        win_count = 0
        loss_count = 0
        total_profit_usdt = 0.0

        for trade in completed_trades:
            result = trade.get('leveraged_profit_pct', 0)
            total_profit_pct += result
            if result > 0:
                win_count += 1
            else:
                loss_count += 1
            total_profit_usdt += trade.get('profit_usdt', 0.0)

        win_rate = (win_count / len(completed_trades) * 100) if completed_trades else 0
        real_trading_status = "✅ Enabled" if self.trading_bot.config["use_real_trading"] else "❌ Disabled (Simulation)"

        status_text = (
            f"📊 <b>BOT STATUS</b> 📊\n\n"
            f"<b>Trading:</b> {'✅ Running' if self.trading_bot.running else '❌ Stopped'}\n"
            f"<b>Mode:</b> {self.trading_bot.config['trading_mode'].capitalize()}\n"
            f"<b>Leverage:</b> {self.trading_bot.config['leverage']}x\n"
            f"<b>Take Profit:</b> {self.trading_bot.config['take_profit']}%\n"
            f"<b>Stop Loss:</b> {self.trading_bot.config['stop_loss']}%\n\n"
            f"<b>Real Trading:</b> {real_trading_status}\n"
            f"<b>Active Trades:</b> {len(active_trades)}\n"
            f"<b>Completed Trades:</b> {len(completed_trades)}\n"
            f"<b>Total Profit %:</b> {total_profit_pct:.2f}%\n"
            f"<b>Total Profit USDT:</b> ${total_profit_usdt:.2f}\n"
            f"<b>Win Rate:</b> {win_rate:.1f}% ({win_count}/{len(completed_trades)})\n\n"
            f"<b>Trading Pairs:</b> {', '.join(self.trading_bot.config['trading_pairs'])}\n"
            f"<b>Daily Profit Target:</b> {self.trading_bot.config['daily_profit_target']}%\n"
            f"<b>Daily Loss Limit:</b> {self.trading_bot.config['daily_loss_limit']}%"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Start Trading", callback_data="select_trading_mode"),
             InlineKeyboardButton("⏹️ Stop Trading", callback_data="stop_trading")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats"),
             InlineKeyboardButton("📈 Positions", callback_data="positions")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="config"),
             InlineKeyboardButton(f"{'🔴 Disable' if self.trading_bot.config['use_real_trading'] else '🟢 Enable'} Real Trading",
                                 callback_data="toggle_real_trading")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    status_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
            except Exception as e:
                logger.warning(f"Failed to edit message in status_command (callback): {e}. Sending new message.")
                await message_object_to_interact_with.reply_text(
                    status_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
        else:
            await message_object_to_interact_with.reply_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode=constants.ParseMode.HTML
            )

    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return

        message_object_to_interact_with = update.callback_query.message if update.callback_query else update.message

        if not message_object_to_interact_with:
            logger.error("config_command: Could not determine message object from update.")
            if update.effective_chat:
                await update.effective_chat.send_text("Error: Could not process config request.")
            return

        if not self.trading_bot:
            await message_object_to_interact_with.reply_text("Trading bot not initialized.")
            return

        config_display = self.trading_bot.config.copy()
        if 'api_key' in config_display:
            config_display['api_key'] = '****' if config_display['api_key'] else 'Not set'
        if 'api_secret' in config_display:
            config_display['api_secret'] = '****' if config_display['api_secret'] else 'Not set'

        config_text = (
            f"⚙️ <b>BOT CONFIGURATION</b> ⚙️\n\n"
            f"<b>Trading Settings:</b>\n"
            f"• Mode: {config_display['trading_mode'].capitalize()}\n"
            f"• Leverage: {config_display['leverage']}x\n"
            f"• Take Profit: {config_display['take_profit']}%\n"
            f"• Stop Loss: {config_display['stop_loss']}%\n"
            f"• Position Size: {config_display['position_size_percentage']}% of balance\n"
            f"• Max Daily Trades: {config_display['max_daily_trades']}\n\n"
            f"<b>Trading Pairs:</b>\n"
            f"• {', '.join(config_display['trading_pairs'])}\n\n"
            f"<b>Profit/Loss Settings:</b>\n"
            f"• Daily Profit Target: {config_display['daily_profit_target']}%\n"
            f"• Daily Loss Limit: {config_display['daily_loss_limit']}%\n\n"
            f"<b>API Settings:</b>\n"
            f"• API Key: {config_display['api_key']}\n"
            f"• API Secret: {config_display['api_secret']}\n"
            f"• Use Testnet: {'Yes' if config_display['use_testnet'] else 'No'}\n"
            f"• Real Trading: {'Enabled' if config_display['use_real_trading'] else 'Disabled (Simulation)'}"
        )
        
        keyboard = [
            [InlineKeyboardButton("Change Mode", callback_data="select_trading_mode")],
            [InlineKeyboardButton("Set Leverage", callback_data="set_leverage"),
             InlineKeyboardButton("Set Profit/Loss", callback_data="set_profit_loss")],
            [InlineKeyboardButton("Manage Pairs", callback_data="manage_pairs"),
             InlineKeyboardButton(f"{'Disable' if self.trading_bot.config['use_real_trading'] else 'Enable'} Real Trading",
                                 callback_data="toggle_real_trading")],
            [InlineKeyboardButton("Back to Status", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    config_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
            except Exception as e:
                logger.warning(f"Failed to edit message in config_command (callback): {e}. Sending new message.")
                await message_object_to_interact_with.reply_text(
                    config_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
        else:
            await message_object_to_interact_with.reply_text(
                config_text,
                reply_markup=reply_markup,
                parse_mode=constants.ParseMode.HTML
            )

    async def set_config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /set command to update configuration"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /set [parameter] [value]\n\n"
                "Common parameters:\n"
                "• leverage (e.g., 10)\n"
                "• trading_mode (safe, standard, aggressive)\n"
                "• take_profit (percentage)\n"
                "• stop_loss (percentage)\n"
                "• position_size_percentage (percentage of balance)\n"
                "• daily_profit_target (percentage)\n"
                "• daily_loss_limit (percentage)\n"
                "• api_key (your Binance API key)\n"
                "• api_secret (your Binance API secret)\n"
                "• use_testnet (true/false)\n"
                "• use_real_trading (true/false)"
            )
            return

        param = args[0].lower()
        value_str = args[1]

        if param not in self.trading_bot.config:
            await update.message.reply_text(f"Unknown parameter: {param}. Use /config to see available parameters.")
            return

        original_value = self.trading_bot.config[param]
        new_value = None

        try:
            if isinstance(original_value, bool):
                new_value = value_str.lower() in ['true', 'yes', '1', 'on']
            elif isinstance(original_value, int):
                new_value = int(value_str)
            elif isinstance(original_value, float):
                new_value = float(value_str)
            elif isinstance(original_value, str):
                if param == 'trading_mode' and value_str not in TRADING_MODES:
                    await update.message.reply_text(
                        f"Invalid trading mode: {value_str}\n"
                        f"Available modes: {', '.join(TRADING_MODES.keys())}"
                    )
                    return
                new_value = value_str
            elif isinstance(original_value, list):
                # Handle list parameters like trading_pairs
                new_value = value_str.split(',')
            else:
                new_value = value_str
        except ValueError:
            await update.message.reply_text(f"Invalid value format for {param}: {value_str}. Expected type: {type(original_value).__name__}")
            return

        self.trading_bot.config[param] = new_value

        if param == 'trading_mode':
            self.trading_bot.apply_trading_mode_settings()
            await update.message.reply_text(
                f"Trading mode changed to {new_value}. Applied new settings:\n"
                f"• Leverage: {self.trading_bot.config['leverage']}x\n"
                f"• Take Profit: {self.trading_bot.config['take_profit']}%\n"
                f"• Stop Loss: {self.trading_bot.config['stop_loss']}%\n"
                f"• Position Size: {self.trading_bot.config['position_size_percentage']}% of balance\n"
                f"• Max Daily Trades: {self.trading_bot.config['max_daily_trades']}"
            )
        else:
            await update.message.reply_text(f"Configuration updated: {param} = {new_value}")

    async def trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /trades command to show recent trades"""
        if not await self.is_authorized(update):
            return

        all_trades = ACTIVE_TRADES + COMPLETED_TRADES

        if not all_trades:
            await update.message.reply_text("No trades recorded yet")
            return

        recent_trades = sorted(all_trades, key=lambda x: x['timestamp'], reverse=True)[:5]

        trades_text = "📊 RECENT TRADES\n\n"
        for trade in recent_trades:
            status = "Active" if not trade.get('completed', False) else "Completed"
            result_pct_str = f"{trade.get('leveraged_profit_pct', 0):.2f}%" if trade.get('completed', False) else "N/A"
            profit_usdt_str = f"${trade.get('profit_usdt', 0.0):.2f}" if trade.get('completed', False) else "N/A"

            if not trade.get('completed', False):
                elapsed = int(time.time() - trade['timestamp'])
                time_info = f"Elapsed: {elapsed}s"
            else:
                try:
                    entry_dt = datetime.strptime(trade['entry_time'], "%Y-%m-%d %H:%M:%S")
                    exit_dt = datetime.strptime(trade['exit_time'], "%Y-%m-%d %H:%M:%S")
                    duration_seconds = int((exit_dt - entry_dt).total_seconds())
                    time_info = f"Duration: {duration_seconds}s"
                except (KeyError, ValueError):
                    duration_seconds = int(trade.get('exit_timestamp', time.time()) - trade['timestamp'])
                    time_info = f"Duration: {duration_seconds}s (approx)"

            trades_text += (
                f"Symbol: {trade['symbol']}\n"
                f"Action: {trade['action']}\n"
                f"Status: {status}\n"
                f"Entry: ${trade['entry_price']:.4f}\n"
                f"Leverage: {trade['leverage']}x\n"
                f"Result: {result_pct_str}\n"
                f"Profit: {profit_usdt_str}\n"
                f"{time_info}\n"
                f"Mode: {trade.get('mode', 'Standard').capitalize()}\n"
                f"Real Trade: {'Yes' if trade.get('real_trade', False) else 'No (Simulation)'}\n\n"
            )

        await update.message.reply_text(trades_text)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return

        is_callback = bool(update.callback_query)
        message_object_to_interact_with = update.callback_query.message if is_callback else update.message
        
        if not message_object_to_interact_with:
            logger.error("stats_command: Could not determine message object from update.")
            if update.effective_chat:
                await update.effective_chat.send_text("Error: Could not process stats request.")
            return

        if not self.trading_bot:
            await message_object_to_interact_with.reply_text("Trading bot not initialized.")
            return

        stats_message_text = self.trading_bot.get_daily_stats_message()
        
        keyboard_nav = [
            [InlineKeyboardButton("🔙 Back to Status", callback_data="status")],
            [InlineKeyboardButton("⚙️ Config", callback_data="config")]
        ]
        reply_markup_nav = InlineKeyboardMarkup(keyboard_nav)

        if is_callback:
            try:
                await update.callback_query.edit_message_text(
                    stats_message_text, 
                    parse_mode=constants.ParseMode.HTML,
                    reply_markup=reply_markup_nav
                )
            except Exception as e:
                logger.warning(f"Failed to edit message in stats_command (callback): {e}. Sending new message.")
                await message_object_to_interact_with.reply_text(
                    stats_message_text, 
                    parse_mode=constants.ParseMode.HTML,
                    reply_markup=reply_markup_nav
                )
        else:
            await message_object_to_interact_with.reply_text(
                stats_message_text, 
                parse_mode=constants.ParseMode.HTML,
                reply_markup=reply_markup_nav 
            )

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /balance command to show Binance account balance"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot or not self.trading_bot.binance_api:
            await update.message.reply_text("Trading bot or Binance API not initialized")
            return

        status_msg = await update.message.reply_text("🔄 Fetching account balance... Please wait.")

        try:
            balance = self.trading_bot.binance_api.get_balance()
            if balance:
                balance_text = (
                    f"💰 ACCOUNT BALANCE\n\n"
                    f"Total Balance: ${balance['total']:.2f} USDT\n"
                    f"Available Balance: ${balance['available']:.2f} USDT\n"
                    f"Unrealized PnL: ${balance['unrealized_pnl']:.2f} USDT\n\n"
                    f"Mode: {'Testnet' if self.trading_bot.config['use_testnet'] else 'Production'}"
                )
                await status_msg.edit_text(balance_text)
            else:
                await status_msg.edit_text("❌ Failed to get account balance. Please check your API credentials.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error getting account balance: {str(e)}")

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return

        initial_reply_source_message = update.callback_query.message if update.callback_query else update.message
        
        if not initial_reply_source_message:
            logger.error("positions_command: Could not determine initial reply source.")
            if update.effective_chat:
                 await update.effective_chat.send_text("Error: Could not process positions request.")
            return

        if not self.trading_bot or not self.trading_bot.binance_api:
            await initial_reply_source_message.reply_text("Trading bot or Binance API not initialized.")
            return

        status_msg_being_edited = await initial_reply_source_message.reply_text(
            "🔄 Fetching open positions... Please wait.",
            parse_mode=constants.ParseMode.HTML
        )

        try:
            positions = self.trading_bot.binance_api.get_open_positions()
            positions_text = "📈 <b>OPEN POSITIONS</b> 📈\n\n"
            found_positions = False

            if positions:
                for position in positions:
                    if float(position['positionAmt']) == 0:
                        continue
                    found_positions = True
                    symbol = position['symbol']
                    amount = float(position['positionAmt'])
                    entry_price = float(position['entryPrice'])
                    mark_price = float(position['markPrice'])
                    unrealized_pnl = float(position['unrealizedProfit'])
                    leverage = float(position['leverage'])
                    position_side_api = position.get('positionSide', 'BOTH') 

                    actual_side_display = "LONG" if amount > 0 else "SHORT"
                    
                    roi_leveraged = 0.0
                    if entry_price != 0 and leverage != 0:
                        initial_margin = (abs(amount) * entry_price) / leverage
                        if initial_margin != 0:
                            roi_leveraged = (unrealized_pnl / initial_margin) * 100
                    
                    positions_text += (
                        f"<b>Symbol:</b> {symbol}\n"
                        f"<b>Side:</b> {actual_side_display} (API Side: {position_side_api})\n"
                        f"<b>Size:</b> {abs(amount)}\n"
                        f"<b>Entry Price:</b> ${entry_price:.4f}\n"
                        f"<b>Mark Price:</b> ${mark_price:.4f}\n"
                        f"<b>Unrealized PnL:</b> ${unrealized_pnl:.2f} (Leveraged)\n"
                        f"<b>ROI:</b> {roi_leveraged:.2f}%\n"
                        f"<b>Leverage:</b> {int(leverage)}x\n\n"
                    )
            
            keyboard_nav = [[InlineKeyboardButton("🔙 Back to Status", callback_data="status")]]
            reply_markup_nav = InlineKeyboardMarkup(keyboard_nav)

            if found_positions:
                await status_msg_being_edited.edit_text(
                    positions_text, 
                    parse_mode=constants.ParseMode.HTML,
                    reply_markup=reply_markup_nav
                )
            else:
                await status_msg_being_edited.edit_text(
                    "No open positions found.",
                    reply_markup=reply_markup_nav
                )
        except Exception as e:
            logger.error(f"Error processing positions data: {e}", exc_info=True)
            if status_msg_being_edited:
                await status_msg_being_edited.edit_text(
                    f"❌ Error getting open positions: {str(e)}",
                    parse_mode=constants.ParseMode.HTML 
                )
            else:
                 await initial_reply_source_message.reply_text(f"❌ Error getting open positions: {str(e)}")

    async def indicators_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /indicators command to show technical indicators for a symbol"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot or not self.trading_bot.technical_analysis:
            await update.message.reply_text("Trading bot or Technical Analysis not initialized")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                "Please specify a symbol. Example: /indicators BTCUSDT\n\n"
                f"Available pairs: {', '.join(self.trading_bot.config['trading_pairs'])}"
            )
            return

        symbol = args[0].upper()
        status_msg = await update.message.reply_text(f"🔄 Calculating indicators for {symbol}... Please wait.")

        try:
            indicators = self.trading_bot.technical_analysis.calculate_indicators(symbol)
            if indicators:
                indicators_text = (
                    f"📊 TECHNICAL INDICATORS - {symbol}\n\n"
                    f"Price: ${indicators['close']:.4f}\n\n"
                    f"RSI (14): {indicators['rsi']:.2f}\n"
                    f"EMA (20): {indicators['ema_short']:.4f}\n"
                    f"EMA (50): {indicators['ema_long']:.4f}\n\n"
                    f"Bollinger Bands:\n"
                    f"• Upper: ${indicators['bb_upper']:.4f}\n"
                    f"• Middle: ${indicators['bb_middle']:.4f}\n"
                    f"• Lower: ${indicators['bb_lower']:.4f}\n\n"
                    f"Candle: {indicators['candle_color'].capitalize()}\n"
                    f"Candle Size: {indicators['candle_size_pct']:.2f}%\n\n"
                    f"Time: {indicators['timestamp']}"
                )
                
                # Get signal
                signal = self.trading_bot.technical_analysis.get_signal(symbol)
                if signal:
                    indicators_text += f"\n\nSignal: {signal['action']}\n"
                    indicators_text += f"Strength: {signal['strength']}/100\n\n"
                    indicators_text += "Reasons:\n"
                    for reason in signal['reasons']:
                        indicators_text += f"• {reason}\n"
                
                await status_msg.edit_text(indicators_text)
            else:
                await status_msg.edit_text(f"❌ Failed to calculate indicators for {symbol}")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error calculating indicators: {str(e)}")

    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /starttrade command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        await self.show_trading_mode_selection(update, context)

    async def show_trading_mode_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trading mode selection menu"""
        modes_text = "🔄 SELECT TRADING MODE\n\n"
        for mode_name, mode_settings in TRADING_MODES.items():
            modes_text += f"📌 {mode_name.capitalize()}\n"
            modes_text += f"• {mode_settings['description']}\n"
            modes_text += f"• Leverage: {mode_settings['leverage']}x\n"
            modes_text += f"• Take Profit: {mode_settings['take_profit']}%\n"
            modes_text += f"• Stop Loss: {mode_settings['stop_loss']}%\n"
            modes_text += f"• Position Size: {mode_settings['position_size_percent']}% of balance\n\n"
        keyboard = []
        for mode_name in TRADING_MODES.keys():
            keyboard.append([InlineKeyboardButton(
                f"Start with {mode_name.capitalize()}",
                callback_data=f"start_mode_{mode_name}"
            )])
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="status")])

        if update.callback_query:
            await update.callback_query.edit_message_text(
                modes_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                modes_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stoptrade command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        if self.trading_bot.stop_trading():
            await update.message.reply_text("Trading stopped. No new trades will be opened.")
        else:
            await update.message.reply_text("Trading is already stopped")

    async def close_all_positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /closeall command to close all open positions"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot or not self.trading_bot.binance_api:
            await update.message.reply_text("Trading bot or Binance API not initialized")
            return

        status_msg = await update.message.reply_text("🔄 Closing all open positions... Please wait.")

        try:
            positions = self.trading_bot.binance_api.get_open_positions()
            if not positions:
                await status_msg.edit_text("No open positions to close.")
                return

            closed_count = 0
            for position in positions:
                symbol = position['symbol']
                amount = float(position['positionAmt'])
                
                if amount == 0:
                    continue
                
                # Determine order side (opposite of position side)
                order_side = "SELL" if amount > 0 else "BUY"
                position_side = "LONG" if amount > 0 else "SHORT"
                
                # Create market order to close position
                close_order = self.trading_bot.binance_api.create_order(
                    symbol=symbol,
                    side=order_side,
                    order_type="MARKET",
                    quantity=abs(amount),
                    position_side=position_side,
                    reduce_only=True
                )
                
                if close_order:
                    closed_count += 1
            
            if closed_count > 0:
                await status_msg.edit_text(f"✅ Successfully closed {closed_count} positions.")
            else:
                await status_msg.edit_text("No positions were closed. There might be an issue with the API.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error closing positions: {str(e)}")

    async def set_leverage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /setleverage command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                f"Current leverage: {self.trading_bot.config['leverage']}x\n\n"
                "Usage: /setleverage [value]\n"
                "Example: /setleverage 10"
            )
            return

        try:
            leverage = int(args[0])
            if leverage < 1 or leverage > 125:
                await update.message.reply_text("Leverage must be between 1 and 125")
                return

            self.trading_bot.config['leverage'] = leverage
            await update.message.reply_text(f"Leverage set to {leverage}x")
        except ValueError:
            await update.message.reply_text("Invalid leverage value. Please provide a number.")

    async def set_mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /setmode command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                f"Current mode: {self.trading_bot.config['trading_mode']}\n\n"
                "Usage: /setmode [mode]\n"
                f"Available modes: {', '.join(TRADING_MODES.keys())}\n"
                "Example: /setmode aggressive"
            )
            return

        mode = args[0].lower()
        if mode not in TRADING_MODES:
            await update.message.reply_text(
                f"Invalid mode: {mode}\n"
                f"Available modes: {', '.join(TRADING_MODES.keys())}"
            )
            return

        self.trading_bot.config['trading_mode'] = mode
        self.trading_bot.apply_trading_mode_settings()
        
        await update.message.reply_text(
            f"Trading mode set to {mode}. Applied new settings:\n"
            f"• Leverage: {self.trading_bot.config['leverage']}x\n"
            f"• Take Profit: {self.trading_bot.config['take_profit']}%\n"
            f"• Stop Loss: {self.trading_bot.config['stop_loss']}%\n"
            f"• Position Size: {self.trading_bot.config['position_size_percentage']}% of balance\n"
            f"• Max Daily Trades: {self.trading_bot.config['max_daily_trades']}"
        )

    async def add_pair_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /addpair command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                f"Current pairs: {', '.join(self.trading_bot.config['trading_pairs'])}\n\n"
                "Usage: /addpair [symbol]\n"
                "Example: /addpair BTCUSDT"
            )
            return

        symbol = args[0].upper()
        
        # Check if pair already exists
        if symbol in self.trading_bot.config['trading_pairs']:
            await update.message.reply_text(f"Pair {symbol} is already in the trading list")
            return
            
        # Verify the pair exists on Binance
        if self.trading_bot.binance_api:
            price = self.trading_bot.binance_api.get_ticker_price(symbol)
            if not price:
                await update.message.reply_text(f"Could not find pair {symbol} on Binance. Please check the symbol.")
                return
        
        # Add the pair
        self.trading_bot.config['trading_pairs'].append(symbol)
        await update.message.reply_text(
            f"Added {symbol} to trading pairs\n\n"
            f"Current pairs: {', '.join(self.trading_bot.config['trading_pairs'])}"
        )

    async def remove_pair_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /removepair command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                f"Current pairs: {', '.join(self.trading_bot.config['trading_pairs'])}\n\n"
                "Usage: /removepair [symbol]\n"
                "Example: /removepair BTCUSDT"
            )
            return

        symbol = args[0].upper()
        
        # Check if pair exists
        if symbol not in self.trading_bot.config['trading_pairs']:
            await update.message.reply_text(f"Pair {symbol} is not in the trading list")
            return
            
        # Remove the pair
        self.trading_bot.config['trading_pairs'].remove(symbol)
        await update.message.reply_text(
            f"Removed {symbol} from trading pairs\n\n"
            f"Current pairs: {', '.join(self.trading_bot.config['trading_pairs'])}"
        )

    async def set_profit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /setprofit command"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                f"Current profit target: {self.trading_bot.config['daily_profit_target']}%\n"
                f"Current loss limit: {self.trading_bot.config['daily_loss_limit']}%\n\n"
                "Usage: /setprofit [target] [limit]\n"
                "Example: /setprofit 5 3"
            )
            return

        try:
            profit_target = float(args[0])
            loss_limit = float(args[1])
            
            if profit_target <= 0:
                await update.message.reply_text("Profit target must be greater than 0")
                return
                
            if loss_limit <= 0:
                await update.message.reply_text("Loss limit must be greater than 0")
                return
            
            self.trading_bot.config['daily_profit_target'] = profit_target
            self.trading_bot.config['daily_loss_limit'] = loss_limit
            
            await update.message.reply_text(
                f"Daily profit/loss settings updated:\n"
                f"• Profit Target: {profit_target}%\n"
                f"• Loss Limit: {loss_limit}%\n\n"
                f"The bot will stop trading when either limit is reached."
            )
        except ValueError:
            await update.message.reply_text("Invalid values. Please provide numbers for target and limit.")

    async def enable_real_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /enablereal command to enable real trading"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        if not self.trading_bot.config["api_key"] or not self.trading_bot.config["api_secret"]:
            await update.message.reply_text(
                "⚠️ API credentials not set.\n\n"
                "Please set your Binance API credentials first:\n"
                "/set api_key YOUR_API_KEY\n"
                "/set api_secret YOUR_API_SECRET"
            )
            return

        status_msg = await update.message.reply_text("🔄 Testing Binance API connection before enabling real trading...")

        if self.trading_bot.binance_api:
            try:
                account_info = self.trading_bot.binance_api.get_account_info()
                if account_info:
                    self.trading_bot.config["use_real_trading"] = True
                    balance = self.trading_bot.binance_api.get_balance()
                    await status_msg.edit_text(
                        f"✅ Real trading has been ENABLED!\n\n"
                        f"Mode: {'Testnet' if self.trading_bot.config['use_testnet'] else 'Production'}\n"
                        f"Account Status: {account_info.get('status', 'Unknown')}\n"
                        f"Balance: ${balance['total'] if balance else 'Unknown'} USDT\n\n"
                        f"⚠️ WARNING: The bot will now execute REAL trades on Binance using your account.\n"
                        f"Please monitor your trades carefully."
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ Failed to connect to Binance API. Please check your API credentials.\n\n"
                        f"Real trading has NOT been enabled."
                    )
            except Exception as e:
                await status_msg.edit_text(
                    f"❌ Error testing API connection: {str(e)}\n\n"
                    f"Real trading has NOT been enabled."
                )
        else:
            await status_msg.edit_text(
                "❌ Binance API not initialized. Please check your API credentials.\n\n"
                "Real trading has NOT been enabled."
            )

    async def disable_real_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /disablereal command to disable real trading"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        self.trading_bot.config["use_real_trading"] = False
        await update.message.reply_text(
            "✅ Real trading has been DISABLED.\n\n"
            "The bot will now operate in simulation mode only."
        )

    async def toggle_testnet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /toggletestnet command to switch between testnet and production"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        self.trading_bot.config["use_testnet"] = not self.trading_bot.config["use_testnet"]

        # Reinitialize the Binance API with the new setting
        self.trading_bot.binance_api = BinanceFuturesAPI(self.trading_bot.config)
        self.trading_bot.technical_analysis = TechnicalAnalysis(self.trading_bot.binance_api)

        mode = "Testnet" if self.trading_bot.config["use_testnet"] else "Production"
        await update.message.reply_text(
            f"✅ Switched to {mode} mode.\n\n"
            f"{'⚠️ You are now using the Binance Testnet. API keys for the main Binance site will not work.' if self.trading_bot.config['use_testnet'] else '⚠️ You are now using the Binance Production API. Testnet API keys will not work.'}\n\n"
            f"Please make sure your API keys are for {mode}."
        )

    async def test_api_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /testapi command to test the Binance API connection"""
        if not await self.is_authorized(update):
            return

        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized")
            return

        # Check if API credentials are set
        if not self.trading_bot.config["api_key"] or not self.trading_bot.config["api_secret"]:
            await update.message.reply_text(
                "⚠️ API credentials not set.\n\n"
                "Please set your Binance API credentials first:\n"
                "/set api_key YOUR_API_KEY\n"
                "/set api_secret YOUR_API_SECRET"
            )
            return

        # Send initial message
        status_msg = await update.message.reply_text("🔄 Testing Binance API connection... Please wait.")

        # Test the API connection
        if self.trading_bot.binance_api:
            try:
                account_info = self.trading_bot.binance_api.get_account_info()
                if account_info:
                    balance = self.trading_bot.binance_api.get_balance()
                    positions = self.trading_bot.binance_api.get_open_positions()
                    
                    await status_msg.edit_text(
                        f"✅ API connection test successful!\n\n"
                        f"Mode: {'Testnet' if self.trading_bot.config['use_testnet'] else 'Production'}\n"
                        f"Account Status: {account_info.get('status', 'Unknown')}\n"
                        f"Balance: ${balance['total'] if balance else 'Unknown'} USDT\n"
                        f"Open Positions: {len([p for p in positions if float(p['positionAmt']) != 0])}\n\n"
                        f"Your API is working correctly!"
                    )
                else:
                    await status_msg.edit_text(
                        "❌ Failed to get account information. Please check your API credentials."
                    )
            except Exception as e:
                await status_msg.edit_text(
                    f"❌ Error testing API connection: {str(e)}\n\n"
                    f"Please check your API credentials and permissions."
                )
        else:
            await status_msg.edit_text(
                "❌ Binance API not initialized. Please check your API credentials."
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        if not await self.is_authorized(update):
            return

        query = update.callback_query
        await query.answer()

        if query.data == "select_trading_mode":
            await self.show_trading_mode_selection(update, context)
            return

        if query.data.startswith("start_mode_"):
            mode = query.data.replace("start_mode_", "")
            if mode in TRADING_MODES:
                self.trading_bot.config["trading_mode"] = mode
                self.trading_bot.apply_trading_mode_settings()
                if self.trading_bot.start_trading():
                    await query.edit_message_text(
                        f"Trading started with {mode.capitalize()} mode!\n\n"
                        f"• Leverage: {self.trading_bot.config['leverage']}x\n"
                        f"• Take Profit: {self.trading_bot.config['take_profit']}%\n"
                        f"• Stop Loss: {self.trading_bot.config['stop_loss']}%\n"
                        f"• Position Size: {self.trading_bot.config['position_size_percentage']}% of balance\n\n"
                        "You will receive notifications for new trades and signals."
                    )
                else:
                    await query.edit_message_text("Trading is already running")
            return

        if query.data == "stop_trading":
            if self.trading_bot.stop_trading():
                await query.edit_message_text("Trading stopped. No new trades will be opened.")
            else:
                await query.edit_message_text("Trading is already stopped")
        elif query.data == "status":
            await self.status_command(update, context)
        elif query.data == "config":
            await self.config_command(update, context)
        elif query.data == "stats":
            await self.stats_command(update, context)
        elif query.data == "positions":
            await self.positions_command(update, context)
        elif query.data == "toggle_real_trading":
            if not self.trading_bot.config["api_key"] or not self.trading_bot.config["api_secret"]:
                await query.edit_message_text(
                    "⚠️ API credentials not set.\n\n"
                    "Please set your Binance API credentials first:\n"
                    "/set api_key YOUR_API_KEY\n"
                    "/set api_secret YOUR_API_SECRET"
                )
                return
            new_state = not self.trading_bot.config["use_real_trading"]
            self.trading_bot.config["use_real_trading"] = new_state
            await query.edit_message_text(
                f"{'✅ Real trading has been ENABLED!' if new_state else '✅ Real trading has been DISABLED.'}\n\n"
                f"{'The bot will now execute REAL trades on Binance using your account.' if new_state else 'The bot will now operate in simulation mode only.'}\n\n"
                f"{'⚠️ WARNING: Please monitor your trades carefully.' if new_state else ''}"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        if not await self.is_authorized(update):
            return
        await update.message.reply_text(
            "I only respond to commands. Use /help to see available commands."
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Exception while handling an update (Error: {context.error}):", exc_info=context.error)

        chat_id_to_notify = None
        if isinstance(update, Update):
            if update.effective_chat:
                chat_id_to_notify = update.effective_chat.id
            elif update.callback_query and update.callback_query.message:
                chat_id_to_notify = update.callback_query.message.chat.id
            elif update.message:
                chat_id_to_notify = update.message.chat.id

        if chat_id_to_notify:
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id_to_notify,
                    text="An internal error occurred while processing your request. The developers have been notified."
                )
            except Exception as e_send:
                logger.error(f"Failed to send error notification to chat {chat_id_to_notify}: {e_send}")
        else:
            logger.warning("Error handler: Could not determine chat_id from update to send user-facing error message.")

    def run(self):
        """Run the bot"""
        self.application.run_polling()

def main():
    token = TELEGRAM_BOT_TOKEN
    admin_ids = ADMIN_USER_IDS
    
    # Initialize the Telegram bot handler
    telegram_handler = TelegramBotHandler(token, admin_ids)
    
    # Initialize the trading bot
    trading_bot = TradingBot(CONFIG, telegram_handler)
    
    # Set the trading bot in the Telegram handler
    telegram_handler.set_trading_bot(trading_bot)

    print("Binance Futures Trading Bot is starting...")
    print(f"Admin User IDs: {ADMIN_USER_IDS}")
    print(f"Available Trading Modes: {', '.join(TRADING_MODES.keys())}")
    print("Press Ctrl+C to stop")

    # Run the Telegram bot
    telegram_handler.run()

if __name__ == "__main__":
    main()
