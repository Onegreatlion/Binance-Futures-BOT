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
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# ======== BOT CONFIGURATION ========
# Replace these values with your own
TELEGRAM_BOT_TOKEN = "API_BOT_TELEGRAM"  # Replace with your bot token
ADMIN_USER_IDS = [1234569]    # Replace with your Telegram user ID(s)
# ==================================

# Binance API configuration
BINANCE_API_KEY = "API_KEY"  # Your Binance API key
BINANCE_API_SECRET = "API_SECRET" 
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
    "hedge_mode": True,  # Use hedge mode (separate long and short positions)
    "post_trade_delay_seconds": 2, # jika Anda mau jeda setelah trade(detik)
    "dynamic_watchlist_symbols": [ # Daftar koin XXXUSDT yang diizinkan untuk dipantau
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "DOGEUSDT", 
        "AVAXUSDT", "DOTUSDT", "MATICUSDT", "SHIBUSDT", "TRXUSDT", "LINKUSDT", 
        "LTCUSDT", "ATOMUSDT", "ETCUSDT", "BCHUSDT", "XLMUSDT", "NEARUSDT", "ALGOUSDT",
        "FTMUSDT", "MANAUSDT", "SANDUSDT", "APEUSDT", "AXSUSDT", "FILUSDT", "ICPUSDT",
        # Anda bisa mengambil daftar ini dari API Binance untuk top X by volume jika mau lebih dinamis lagi
        # atau hardcode koin-koin yang Anda percaya.
    ],
    "max_active_dynamic_pairs": 3,  # Jumlah maksimum pair dinamis yang akan ditradingkan
    "min_24h_volume_usdt_for_scan": 5000000, # Min volume 24jam (USDT) agar koin dipertimbangkan (5 Juta USDT)
    "dynamic_scan_interval_seconds": 300, # Seberapa sering scan (detik), misal 5 menit
    "dynamic_pair_selection": True,  # Aktifkan/Nonaktifkan fitur ini     
    "api_call_delay_seconds": 0.5, # Jeda 0.5 detik antar panggilan API klines di scanner    
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

# In TechnicalAnalysis class

class TechnicalAnalysis:
    def __init__(self, binance_api):
        self.binance_api = binance_api
        self.settings = INDICATOR_SETTINGS

    def calculate_indicators(self, symbol: str, timeframe: str = None) -> dict | None:
        """
        Calculates technical indicators for a given symbol and timeframe.

        Args:
            symbol (str): The trading symbol (e.g., "BTCUSDT").
            timeframe (str, optional): The candle timeframe (e.g., "5m", "1h"). 
                                       Defaults to self.settings['candle_timeframe'].

        Returns:
            dict | None: A dictionary containing calculated indicators and other relevant data,
                         or None if calculation fails or data is insufficient.
        """
        if timeframe is None:
            timeframe = self.settings.get('candle_timeframe', '5m') # Default jika tidak ada di settings

        # Tentukan panjang data minimum yang dibutuhkan berdasarkan indikator terpanjang
        # Misalnya, EMA_long + beberapa candle ekstra untuk stabilitas BB dan RSI
        ema_long_period = self.settings.get('ema_long', 50)
        bb_period = self.settings.get('bb_period', 20)
        rsi_period = self.settings.get('rsi_period', 14)
        
        # Ambil periode terpanjang dan tambahkan buffer (misal 20-30 candle)
        # Ini untuk memastikan pandas_ta punya cukup data untuk menghasilkan nilai non-NaN
        # di akhir series untuk semua indikator.
        required_initial_candles = max(ema_long_period, bb_period, rsi_period)
        buffer_candles = 30 # Buffer untuk stabilitas dan periode awal NaN
        limit_request = required_initial_candles + buffer_candles
        
        logger.debug(f"[{symbol}@{timeframe}] Requesting klines from API, limit: {limit_request}")
        
        df: pd.DataFrame | None = None
        try:
            df = self.binance_api.get_klines(symbol, timeframe, limit=limit_request)
        except Exception as e_klines:
            logger.error(f"[{symbol}@{timeframe}] Exception during API call to get_klines: {e_klines}", exc_info=True)
            return None

        # --- Validasi DataFrame Awal ---
        if df is None:
            logger.error(f"[{symbol}@{timeframe}] get_klines returned None. Cannot calculate indicators.")
            return None
        
        if not isinstance(df, pd.DataFrame):
            logger.error(f"[{symbol}@{timeframe}] get_klines did not return a pandas DataFrame (type: {type(df)}). Cannot calculate.")
            return None
            
        if df.empty:
            logger.error(f"[{symbol}@{timeframe}] get_klines returned an empty DataFrame. Cannot calculate indicators.")
            return None

        # Periksa apakah jumlah baris yang dikembalikan cukup, setidaknya untuk indikator terpanjang
        if len(df) < required_initial_candles:
            logger.error(
                f"[{symbol}@{timeframe}] Insufficient data returned by get_klines. "
                f"Got {len(df)} rows, needed at least {required_initial_candles} for primary indicators. Aborting calculation."
            )
            return None
        
        # --- Persiapan Kolom dan Kalkulasi Indikator ---
        try:
            # Pastikan kolom OHLCV ada dan bertipe numerik
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in ohlcv_cols:
                if col not in df.columns:
                    logger.error(f"[{symbol}@{timeframe}] DataFrame missing required column: '{col}'.")
                    return None
                # Konversi ke float jika belum (get_klines idealnya sudah melakukan ini)
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                # Jika setelah konversi masih ada NaN di kolom penting seperti 'close', ini masalah
                if col == 'close' and df[col].isnull().any():
                    logger.error(f"[{symbol}@{timeframe}] 'close' column contains NaN values after numeric conversion. Cannot proceed.")
                    return None
            
            # Hapus baris dengan NaN di 'close' jika ada, sebelum kalkulasi TA
            # Ini penting karena TA lib tidak suka NaN di input utama
            df.dropna(subset=['close'], inplace=True)
            if len(df) < required_initial_candles: # Cek lagi setelah dropna
                logger.error(f"[{symbol}@{timeframe}] Insufficient data after dropping NaN 'close' values. Got {len(df)}, needed {required_initial_candles}.")
                return None

            # 1. RSI (Relative Strength Index)
            rsi_len = self.settings.get('rsi_period', 14)
            df['rsi'] = ta.rsi(close=df['close'], length=rsi_len)
            
            # 2. EMAs (Exponential Moving Averages)
            ema_s_len = self.settings.get('ema_short', 20)
            ema_l_len = self.settings.get('ema_long', 50)
            df['ema_short'] = ta.ema(close=df['close'], length=ema_s_len)
            df['ema_long'] = ta.ema(close=df['close'], length=ema_l_len)
            
            # 3. Bollinger Bands
            bb_len = self.settings.get('bb_period', 20)
            bb_std = self.settings.get('bb_std', 2.0)
            bbands_df = ta.bbands(close=df['close'], length=bb_len, std=bb_std)
            
            if bbands_df is not None and not bbands_df.empty:
                # Nama kolom output pandas-ta bisa bervariasi sedikit, pastikan formatnya benar
                # Umumnya: BBL_{length}_{stddev}, BBM_{length}_{stddev}, BBU_{length}_{stddev}
                # Untuk stddev float, pandas-ta mungkin menggunakan format seperti '2.0' atau '2'
                # Kita coba beberapa format umum jika yang pertama gagal
                bb_std_str = f"{bb_std:.1f}" # Misal "2.0"
                bb_l_col = f'BBL_{bb_len}_{bb_std_str}'
                bb_m_col = f'BBM_{bb_len}_{bb_std_str}'
                bb_u_col = f'BBU_{bb_len}_{bb_std_str}'

                if bb_l_col not in bbands_df.columns: # Coba format std tanpa desimal jika .0
                    bb_std_str_alt = str(int(bb_std)) if bb_std == int(bb_std) else bb_std_str
                    bb_l_col = f'BBL_{bb_len}_{bb_std_str_alt}'
                    bb_m_col = f'BBM_{bb_len}_{bb_std_str_alt}'
                    bb_u_col = f'BBU_{bb_len}_{bb_std_str_alt}'
                
                if bb_l_col in bbands_df.columns:
                    df['bb_lower'] = bbands_df[bb_l_col]
                    df['bb_middle'] = bbands_df[bb_m_col]
                    df['bb_upper'] = bbands_df[bb_u_col]
                else:
                    logger.warning(f"[{symbol}@{timeframe}] Could not find expected Bollinger Bands columns (e.g., {bb_l_col}). Setting BBs to NaN.")
                    df['bb_lower'], df['bb_middle'], df['bb_upper'] = pd.NA, pd.NA, pd.NA
            else:
                logger.warning(f"[{symbol}@{timeframe}] pandas_ta.bbands returned None or empty. Setting BBs to NaN.")
                df['bb_lower'], df['bb_middle'], df['bb_upper'] = pd.NA, pd.NA, pd.NA
            
            # 4. Candle Color
            df['candle_color'] = np.where(df['close'] >= df['open'], 'green', 'red')
            
            # 5. Candle Size Percentage
            # Hindari pembagian dengan nol jika 'open' bisa 0 atau NaN
            df['candle_size_pct'] = ((df['close'] - df['open']).abs() / df['open'].replace(0, np.nan) * 100).fillna(0.0)
            
            # --- Ekstrak Baris Data Terakhir ---
            if df.empty: # Cek lagi jika df menjadi kosong karena error di atas
                logger.error(f"[{symbol}@{timeframe}] DataFrame is empty before selecting the latest row after TA calculations.")
                return None
                
            latest_indicators_row = df.iloc[-1].copy() # Baris terakhir untuk sinyal saat ini
            previous_indicators_row = df.iloc[-2].copy() if len(df) > 1 else None # Baris sebelumnya

            # --- Validasi Akhir untuk NaN di Indikator Kritis pada Baris Terakhir ---
            # Indikator ini harus ada nilainya (bukan NaN) untuk menghasilkan sinyal yang valid
            critical_ta_cols_for_signal = ['rsi', 'ema_short', 'ema_long', 'bb_middle']
            nan_in_critical = latest_indicators_row[critical_ta_cols_for_signal].isnull().any()

            if nan_in_critical:
                rsi_val_str = f"{latest_indicators_row['rsi']:.2f}" if pd.notna(latest_indicators_row['rsi']) else "NaN"
                ema_s_val_str = f"{latest_indicators_row['ema_short']:.4f}" if pd.notna(latest_indicators_row['ema_short']) else "NaN"
                ema_l_val_str = f"{latest_indicators_row['ema_long']:.4f}" if pd.notna(latest_indicators_row['ema_long']) else "NaN"
                bb_m_val_str = f"{latest_indicators_row['bb_middle']:.4f}" if pd.notna(latest_indicators_row['bb_middle']) else "NaN"
                
                logger.warning(
                    f"[{symbol}@{timeframe}] Latest indicator row contains NaN in critical TA values: "
                    f"RSI: {rsi_val_str}, EMA_S: {ema_s_val_str}, EMA_L: {ema_l_val_str}, BB_M: {bb_m_val_str}. "
                    "Cannot generate a reliable signal."
                )
                return None # Jika ada NaN di indikator penting, jangan hasilkan sinyal

        except KeyError as e_key:
            logger.error(f"[{symbol}@{timeframe}] KeyError during indicator calculation. Missing column or wrong TA lib output format for '{e_key}'.", exc_info=True)
            return None
        except Exception as e_calc: # Tangkap error umum lainnya selama kalkulasi
            logger.error(f"[{symbol}@{timeframe}] Unexpected error during indicator calculation: {e_calc}", exc_info=True)
            return None
            
        # Jika semua berhasil, kembalikan dictionary hasil
        return {
            'symbol': symbol,
            'timestamp': latest_indicators_row['timestamp'], # Seharusnya pd.Timestamp dari get_klines
            'close': latest_indicators_row['close'],
            'rsi': latest_indicators_row['rsi'],
            'ema_short': latest_indicators_row['ema_short'],
            'ema_long': latest_indicators_row['ema_long'],
            'bb_upper': latest_indicators_row['bb_upper'],
            'bb_middle': latest_indicators_row['bb_middle'],
            'bb_lower': latest_indicators_row['bb_lower'],
            'candle_color': latest_indicators_row['candle_color'],
            'candle_size_pct': latest_indicators_row['candle_size_pct'],
            'previous': previous_indicators_row, # Bisa None jika hanya ada 1 baris data
            # 'df': df # Opsional: Mengembalikan seluruh df bisa memakan banyak memori jika sering dipanggil.
                      # Berguna untuk debugging, tapi mungkin tidak untuk produksi.
        }
        
    def get_signal(self, symbol, timeframe=None):
        """Get trading signal based on technical indicators"""
        if not timeframe:
            timeframe = self.settings['candle_timeframe']
        
        indicators = self.calculate_indicators(symbol, timeframe)
        if not indicators:
            # calculate_indicators sudah melakukan logging, jadi tidak perlu log lagi di sini
            return None
            
        signal = {
            'symbol': symbol,
            'timestamp': indicators['timestamp'],
            'price': indicators['close'],
            'action': 'WAIT',
            'strength': 0,
            'reasons': []
        }
        
        # Defensive check for NaN values that might have slipped through calculate_indicators
        # or if a calculation failed silently for a specific indicator not checked above.
        if pd.isna(indicators['rsi']) or pd.isna(indicators['ema_short']) or \
           pd.isna(indicators['ema_long']) or pd.isna(indicators['bb_upper']) or \
           pd.isna(indicators['bb_lower']):
            logger.warning(f"[{symbol}@{timeframe}] Critical indicator is NaN. RSI: {indicators['rsi']}, EMA_S: {indicators['ema_short']}, EMA_L: {indicators['ema_long']}, BB_U: {indicators['bb_upper']}, BB_L: {indicators['bb_lower']}. Skipping signal generation.")
            signal['reasons'].append("Critical indicator is NaN")
            return signal # Return WAIT signal

        logger.debug(
            f"[{symbol}@{timeframe}] Indicators Check: "
            f"Close={indicators['close']:.4f}, RSI={indicators['rsi']:.2f}, "
            f"EMA_S={indicators['ema_short']:.4f}, EMA_L={indicators['ema_long']:.4f}, "
            f"BB_U={indicators['bb_upper']:.4f}, BB_L={indicators['bb_lower']:.4f}, "
            f"Candle='{indicators['candle_color']}'"
        )

        # --- RSI + Candle Color Strategy ---
        rsi_is_oversold = indicators['rsi'] < self.settings['rsi_oversold']
        rsi_is_overbought = indicators['rsi'] > self.settings['rsi_overbought']
        candle_is_green = indicators['candle_color'] == 'green'
        candle_is_red = indicators['candle_color'] == 'red'

        logger.debug(
            f"[{symbol}@{timeframe}] RSI Conditions: "
            f"Oversold={rsi_is_oversold} (RSI {indicators['rsi']:.2f} < {self.settings['rsi_oversold']}), "
            f"Overbought={rsi_is_overbought} (RSI {indicators['rsi']:.2f} > {self.settings['rsi_overbought']}), "
            f"GreenCandle={candle_is_green}, RedCandle={candle_is_red}"
        )

        if rsi_is_oversold and candle_is_green:
            signal['action'] = 'LONG'
            signal['strength'] += 30
            signal['reasons'].append(f"RSI oversold ({indicators['rsi']:.2f}) & green candle")
            logger.debug(f"[{symbol}@{timeframe}] Condition: RSI LONG. Action: {signal['action']}, Strength: {signal['strength']}")
        elif rsi_is_overbought and candle_is_red:
            signal['action'] = 'SHORT'
            signal['strength'] += 30
            signal['reasons'].append(f"RSI overbought ({indicators['rsi']:.2f}) & red candle")
            logger.debug(f"[{symbol}@{timeframe}] Condition: RSI SHORT. Action: {signal['action']}, Strength: {signal['strength']}")

        # --- EMA Strategy ---
        # Ensure EMAs are not NaN before comparison
        ema_s_valid = not pd.isna(indicators['ema_short'])
        ema_l_valid = not pd.isna(indicators['ema_long'])

        ema_is_bullish = False
        ema_is_bearish = False

        if ema_s_valid and ema_l_valid:
            ema_is_bullish = indicators['close'] > indicators['ema_short'] and indicators['ema_short'] > indicators['ema_long']
            ema_is_bearish = indicators['close'] < indicators['ema_short'] and indicators['ema_short'] < indicators['ema_long']
        
        logger.debug(
            f"[{symbol}@{timeframe}] EMA Conditions: ValidS={ema_s_valid}, ValidL={ema_l_valid}, "
            f"Bullish={ema_is_bullish}, Bearish={ema_is_bearish}"
        )

        if ema_is_bullish:
            if signal['action'] == 'LONG':  # Confirming
                signal['strength'] += 20
                signal['reasons'].append("EMA bullish confirmation")
            elif signal['action'] == 'WAIT':  # Primary
                signal['action'] = 'LONG'
                signal['strength'] += 20  # Base strength for EMA signal
                signal['reasons'].append("EMA bullish crossover")
            logger.debug(f"[{symbol}@{timeframe}] Condition: EMA Bullish. Action: {signal['action']}, Strength: {signal['strength']}")
        elif ema_is_bearish:
            if signal['action'] == 'SHORT':  # Confirming
                signal['strength'] += 20
                signal['reasons'].append("EMA bearish confirmation")
            elif signal['action'] == 'WAIT':  # Primary
                signal['action'] = 'SHORT'
                signal['strength'] += 20
                signal['reasons'].append("EMA bearish crossover")
            logger.debug(f"[{symbol}@{timeframe}] Condition: EMA Bearish. Action: {signal['action']}, Strength: {signal['strength']}")

        # --- Bollinger Bands Strategy ---
        bb_u_valid = not pd.isna(indicators['bb_upper'])
        bb_l_valid = not pd.isna(indicators['bb_lower'])

        price_above_bb_upper = False
        price_below_bb_lower = False

        if bb_u_valid:
            price_above_bb_upper = indicators['close'] > indicators['bb_upper']
        if bb_l_valid:
            price_below_bb_lower = indicators['close'] < indicators['bb_lower']

        logger.debug(
            f"[{symbol}@{timeframe}] BB Conditions: ValidU={bb_u_valid}, ValidL={bb_l_valid}, "
            f"AboveUpper={price_above_bb_upper}, BelowLower={price_below_bb_lower}"
        )

        if price_above_bb_upper: # Potential SHORT reversal
            if signal['action'] == 'SHORT': # Confirming
                signal['strength'] += 20
                signal['reasons'].append("BB price above upper (confirms SHORT)")
            elif signal['action'] == 'WAIT': # Primary
                signal['action'] = 'SHORT'
                signal['strength'] += 15
                signal['reasons'].append("BB price above upper (potential SHORT reversal)")
            logger.debug(f"[{symbol}@{timeframe}] Condition: BB Above Upper. Action: {signal['action']}, Strength: {signal['strength']}")
        elif price_below_bb_lower: # Potential LONG reversal
            if signal['action'] == 'LONG': # Confirming
                signal['strength'] += 20
                signal['reasons'].append("BB price below lower (confirms LONG)")
            elif signal['action'] == 'WAIT': # Primary
                signal['action'] = 'LONG'
                signal['strength'] += 15
                signal['reasons'].append("BB price below lower (potential LONG reversal)")
            logger.debug(f"[{symbol}@{timeframe}] Condition: BB Below Lower. Action: {signal['action']}, Strength: {signal['strength']}")

        # --- Final Strength Check & Decision ---
        signal_threshold = self.settings.get('signal_strength_threshold', 30) # Ambil dari settings jika ada, default 30
        logger.debug(f"[{symbol}@{timeframe}] Pre-threshold Check: Action={signal['action']}, Strength={signal['strength']}, Threshold={signal_threshold}")

        if signal['action'] != 'WAIT' and signal['strength'] < signal_threshold:
            logger.info(
                f"[{symbol}@{timeframe}] Strength {signal['strength']} < {signal_threshold}. "
                f"Reverting Action '{signal['action']}' to 'WAIT'."
            )
            signal['action'] = 'WAIT'
            signal['reasons'] = [f"Final strength {signal['strength']}/{signal_threshold} insufficient"] # Overwrite reasons
            signal['strength'] = 0 # Reset strength jika di-revert
        elif signal['action'] == 'WAIT' and not signal['reasons']: # Jika tetap WAIT dan tidak ada alasan spesifik
             signal['reasons'].append(f"No strong signal found (strength {signal['strength']}/{signal_threshold})")


        if signal['action'] != 'WAIT':
            logger.warning(
                f"[{symbol}@{timeframe}] <<< TRADE SIGNAL >>> "
                f"Action: {signal['action']}, Strength: {signal['strength']}/{signal_threshold}, "
                f"Price: {signal['price']:.4f}, Reasons: {'; '.join(signal['reasons'])}"
            )
        else:
            logger.info(
                f"[{symbol}@{timeframe}] Final Decision: "
                f"Action: {signal['action']}, Strength: {signal['strength']}/{signal_threshold}, "
                f"Price: {signal['price']:.4f}, Reasons: {'; '.join(signal['reasons'])}"
            )
            
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
        self.dynamic_pair_scanner_thread = None
        self.currently_scanned_pairs = [] # Untuk menyimpan hasil scan terakhir (list of signal_data dicts)
        self.active_trading_pairs_lock = threading.Lock() # Lock untuk akses aman ke self.config["trading_pairs"]
        
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

# Di dalam class TradingBot:
    def get_liquid_pairs_from_watchlist(self):
        """
        Fetches pairs from the dynamic_watchlist_symbols that meet minimum 24h volume criteria.
        Returns a list of liquid symbol strings.
        """
        if not self.binance_api:
            logger.warning("Binance API not available for liquidity check. Returning full watchlist.")
            return self.config.get("dynamic_watchlist_symbols", [])

        watchlist = self.config.get("dynamic_watchlist_symbols", [])
        min_volume_usdt = self.config.get("min_24h_volume_usdt_for_scan", 0)
        liquid_pairs = []

        if not watchlist:
            logger.info("Dynamic watchlist is empty.")
            return []

        try:
            all_tickers_data = self.binance_api.get_ticker_24hr() # Fetches all symbols
            if not all_tickers_data:
                logger.error("Failed to fetch 24h ticker data for liquidity check.")
                return watchlist # Fallback to full watchlist if API fails

            tickers_map = {item['symbol']: item for item in all_tickers_data}

            for symbol in watchlist:
                ticker_info = tickers_map.get(symbol)
                if ticker_info:
                    # For futures, 'quoteVolume' is the volume in the quote asset (e.g., USDT)
                    volume_24h_usdt = float(ticker_info.get('quoteVolume', 0))
                    if volume_24h_usdt >= min_volume_usdt:
                        liquid_pairs.append(symbol)
                    else:
                        logger.debug(f"DynamicScan: {symbol} skipped, volume {volume_24h_usdt:.2f} USDT < {min_volume_usdt:.2f} USDT")
                else:
                    logger.debug(f"DynamicScan: No 24h ticker data found for {symbol} in watchlist.")
            
            logger.info(f"DynamicScan: Found {len(liquid_pairs)} liquid pairs for scanning: {liquid_pairs}")
            return liquid_pairs
            
        except Exception as e:
            logger.error(f"DynamicScan: Error during liquidity check: {e}", exc_info=True)
            return watchlist # Fallback

    def dynamic_pair_scan_loop(self):
        """
        Periodically scans watchlist pairs for trading signals and updates 
        the active self.config["trading_pairs"] list.
        """
        logger.info("Dynamic Pair Scanner loop initiated.")
        while self.running:
            scan_successful = False
            try:
                if not self.config.get("dynamic_pair_selection", False):
                    logger.debug("Dynamic pair selection is disabled. Scanner sleeping.")
                    # Sleep for a bit even if disabled to check self.running periodically
                    time.sleep(self.config.get("dynamic_scan_interval_seconds", 300) / 10) 
                    continue

                logger.info("DynamicScan: Starting new scan cycle...")
                
                potential_pairs = self.get_liquid_pairs_from_watchlist()
                if not potential_pairs:
                    logger.info("DynamicScan: No liquid pairs from watchlist to scan this cycle.")
                    # Mark scan as "successful" in terms of not erroring, to ensure full sleep
                    scan_successful = True 
                    time.sleep(self.config.get("dynamic_scan_interval_seconds", 300))
                    continue

                candidate_signals = []
                for symbol_to_scan in potential_pairs:
                    if not self.running:  # Check if bot stopped during scan
                        logger.info("DynamicScan: Bot stopping, aborting current scan.")
                        return # Exit loop
                    
                    logger.debug(f"DynamicScan: Evaluating signal for candidate: {symbol_to_scan}")
                    # Menggunakan timeframe default dari settings indikator
                    signal_data = self.technical_analysis.get_signal(symbol_to_scan) 
                    
                    if signal_data and signal_data['action'] != 'WAIT' and \
                       signal_data['strength'] >= self.config.get("signal_strength_threshold", 30):
                        candidate_signals.append(signal_data)
                        logger.info(
                            f"DynamicScan: Strong signal for {symbol_to_scan} - "
                            f"Action: {signal_data['action']}, Strength: {signal_data['strength']}"
                        )
                    # Jeda kecil antar API call untuk klines, terutama jika banyak pair
                    time.sleep(self.config.get("api_call_delay_seconds", 0.5)) 


                candidate_signals.sort(key=lambda x: x['strength'], reverse=True)
                self.currently_scanned_pairs = candidate_signals # Store for potential display/debug

                max_active = self.config.get("max_active_dynamic_pairs", 1)
                # Ambil hanya simbol dari sinyal yang dipilih
                new_dynamic_active_pairs = [s['symbol'] for s in candidate_signals[:max_active]]

                with self.active_trading_pairs_lock:
                    # Ambil daftar pair trading saat ini
                    # Jika ada pair yang dihardcode dan tidak ingin di-overwrite, logika ini perlu disesuaikan
                    # Saat ini, ini akan mengganti seluruh daftar `trading_pairs`
                    current_trading_pairs = list(self.config.get("trading_pairs", []))
                    
                    if set(new_dynamic_active_pairs) != set(current_trading_pairs):
                        self.config["trading_pairs"] = new_dynamic_active_pairs # Update daftar aktif
                        logger.warning(
                            f"DynamicScan: Active trading pairs UPDATED. "
                            f"Old: {current_trading_pairs}, New: {self.config['trading_pairs']}"
                        )
                        self.send_notification(
                            f"🔄 <b>Dynamic Trading Pairs Updated</b> 🔄\n\n"
                            f"Now actively monitoring: {', '.join(self.config['trading_pairs']) if self.config['trading_pairs'] else 'None'}\n"
                            f"(Scan found {len(candidate_signals)} candidates from {len(potential_pairs)} liquid pairs)"
                        )
                    else:
                        logger.info(f"DynamicScan: No change to active trading pairs: {self.config['trading_pairs']}")
                
                scan_successful = True # Scan cycle completed successfully

            except Exception as e:
                logger.error(f"DynamicScan: Error in dynamic_pair_scan_loop: {e}", exc_info=True)
                # Jika error, tidur lebih singkat agar bisa coba lagi, tapi jangan 0
                time.sleep(60) # Misal 1 menit jika ada error
            
            finally:
                # Tidur sebelum scan berikutnya, hanya jika scan berhasil atau tidak ada error fatal
                # Jika scan_successful adalah True, berarti loop berjalan normal
                if scan_successful:
                    interval = self.config.get("dynamic_scan_interval_seconds", 300)
                    logger.debug(f"DynamicScan: Cycle complete. Sleeping for {interval} seconds.")
                    # Tidur dengan cara yang bisa diinterupsi oleh self.running = False
                    for _ in range(interval):
                        if not self.running:
                            break
                        time.sleep(1)
                # Jika scan_successful False, berarti ada exception, tidur singkat sudah dilakukan di blok except

        logger.info("Dynamic Pair Scanner loop has stopped.")
        
# Di dalam class TradingBot:

    def start_trading(self):
        """Start the trading bot and its associated threads."""
        if self.running:
            logger.info("Trading bot is already running.")
            return False # Bot sudah berjalan
            
        self.running = True # Set flag utama bahwa bot aktif
        logger.info("Attempting to start trading bot...")
        
        # Terapkan pengaturan mode trading
        self.apply_trading_mode_settings()

        # Atur mode hedge jika diaktifkan dan API tersedia
        if self.config.get("hedge_mode", False) and self.binance_api:
            try:
                logger.info("Attempting to set position mode to Hedge Mode.")
                result = self.binance_api.change_position_mode(True) # True untuk Hedge Mode
                if result and isinstance(result, dict) and result.get('code') == 200:
                    logger.info(f"Successfully set position mode to Hedge Mode. Response: {result.get('msg', 'OK')}")
                elif result and isinstance(result, dict) and "already" in result.get('msg', '').lower():
                     logger.info(f"Position mode already set as Hedge Mode or no change needed: {result.get('msg')}")
                else:
                    logger.warning(f"Failed to confirm Hedge Mode setting or unexpected response: {result}")
            except Exception as e:
                logger.error(f"Error setting hedge mode: {e}", exc_info=True)

        # Mulai thread untuk memeriksa sinyal trading pada pair yang aktif
        self.signal_check_thread = threading.Thread(target=self.signal_check_loop)
        self.signal_check_thread.daemon = True # Agar thread berhenti saat program utama berhenti
        self.signal_check_thread.start()
        logger.info("Signal check thread started.")
        
        # Mulai thread pemindai pair dinamis jika fitur diaktifkan
        if self.config.get("dynamic_pair_selection", False):
            self.dynamic_pair_scanner_thread = threading.Thread(target=self.dynamic_pair_scan_loop)
            self.dynamic_pair_scanner_thread.daemon = True
            self.dynamic_pair_scanner_thread.start()
            logger.info("Dynamic Pair Scanner thread started.")

        # Mulai thread untuk memproses antrian notifikasi
        # Pastikan process_notification_queue sudah diadaptasi dari fixed_bot.py
        self.notification_thread = threading.Thread(target=self.process_notification_queue)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        logger.info("Notification processor thread started.")

        # Reset statistik harian saat memulai trading
        self.reset_daily_stats()
        
        # Kirim notifikasi bahwa bot telah dimulai
        # Gunakan HTML untuk format yang lebih baik
        start_notification_message = (
            f"🚀 <b>Trading Bot Started</b> 🚀\n\n"
            f"<b>Mode:</b> {self.config.get('trading_mode', 'N/A').capitalize()}\n"
            f"<b>Leverage:</b> {self.config.get('leverage', 0)}x\n"
            f"<b>Take Profit:</b> {self.config.get('take_profit', 0.0)}%\n"
            f"<b>Stop Loss:</b> {self.config.get('stop_loss', 0.0)}%\n"
            f"<b>Position Size:</b> {self.config.get('position_size_percentage', 0.0)}% of balance\n"
            f"<b>Daily Profit Target:</b> {self.config.get('daily_profit_target', 0.0)}%\n"
            f"<b>Daily Loss Limit:</b> {self.config.get('daily_loss_limit', 0.0)}%\n"
            # Tampilkan trading_pairs hanya jika dynamic selection OFF
            f"<b>Trading Pairs:</b> {', '.join(self.config.get('trading_pairs', [])) if not self.config.get('dynamic_pair_selection', False) and self.config.get('trading_pairs', []) else ('Dynamic Selection Active' if self.config.get('dynamic_pair_selection', False) else 'None Configured')}\n"
            f"<b>Dynamic Pair Selection:</b> {'✅ Enabled' if self.config.get('dynamic_pair_selection', False) else '❌ Disabled'}\n"
            f"<b>Real Trading:</b> {'✅ Enabled' if self.config.get('use_real_trading', False) else '❌ Disabled (Simulation)'}"
        )
        self.send_notification(start_notification_message)        
        
        logger.info("Trading bot successfully started and all associated threads are running.")
        return True

    def stop_trading(self):
        """Gracefully stop the trading bot and its associated threads."""
        if not self.running:
            logger.info("Trading bot is not running or already in the process of stopping.")
            return False # Bot tidak berjalan atau sudah dihentikan

        logger.warning("Initiating trading bot stop sequence...")
        self.running = False  # Flag utama untuk menghentikan semua loop di thread

        # 1. Hentikan thread Dynamic Pair Scanner (jika berjalan)
        # Ini harus dihentikan lebih dulu karena bisa mengubah daftar trading_pairs
        if self.dynamic_pair_scanner_thread and self.dynamic_pair_scanner_thread.is_alive():
            logger.info("Waiting for Dynamic Pair Scanner thread to join...")
            try:
                # Loop di dynamic_pair_scan_loop memeriksa self.running
                self.dynamic_pair_scanner_thread.join(timeout=10.0) # Beri waktu yang cukup
                if self.dynamic_pair_scanner_thread.is_alive():
                    logger.warning("Dynamic Pair Scanner thread did not join in time.")
                else:
                    logger.info("Dynamic Pair Scanner thread joined successfully.")
            except Exception as e:
                logger.error(f"Error while joining Dynamic Pair Scanner thread: {e}", exc_info=True)
        else:
            logger.info("Dynamic Pair Scanner thread was not running or already joined.")

        # 2. Hentikan thread Signal Check
        if self.signal_check_thread and self.signal_check_thread.is_alive():
            logger.info("Waiting for Signal Check thread to join...")
            try:
                # Loop di signal_check_loop memeriksa self.running
                self.signal_check_thread.join(timeout=self.config.get("signal_check_interval", 30) + 5.0) # Timeout berdasarkan intervalnya + buffer
                if self.signal_check_thread.is_alive():
                    logger.warning("Signal Check thread did not join in time.")
                else:
                    logger.info("Signal Check thread joined successfully.")
            except Exception as e:
                logger.error(f"Error while joining Signal Check thread: {e}", exc_info=True)
        else:
            logger.info("Signal Check thread was not running or already joined.")

        # 3. Kirim notifikasi "Bot Stopped" (jika memungkinkan)
        # Ini dikirim sebelum menghentikan notification_thread agar ada kesempatan diproses
        final_stop_message = "⏹️ <b>Trading Bot Stopped</b> ⏹️"
        logger.info(f"Attempting to queue final stop notification: {final_stop_message}")
        self.send_notification(final_stop_message) 
        # Beri sedikit waktu agar pesan masuk antrian dan mungkin diproses
        # Ini adalah upaya terbaik; jika notification_thread sudah bermasalah, mungkin tidak terkirim.
        time.sleep(0.5) # Jeda singkat agar antrian notifikasi bisa diproses

        # 4. Hentikan thread Notification Processor
        if self.notification_thread and self.notification_thread.is_alive():
            logger.info("Signalling Notification Processor thread to stop and waiting for it to join...")
            try:
                # Kirim sinyal 'None' untuk memberitahu thread agar berhenti (jika process_notification_queue mendukungnya)
                # process_notification_queue juga harus memeriksa self.running
                self.notification_queue.put((None, None), block=False) # Non-blocking, jika penuh tidak apa-apa
            except queue.Full:
                logger.warning("Notification queue was full when trying to put stop sentinel. Thread might be busy or stuck.")
            
            try:
                self.notification_thread.join(timeout=15.0) # Beri waktu lebih lama untuk memproses sisa antrian + sentinel
                if self.notification_thread.is_alive():
                    logger.warning("Notification Processor thread did not join in time. Some final notifications might be lost.")
                else:
                    logger.info("Notification Processor thread joined successfully.")
            except Exception as e:
                logger.error(f"Error while joining Notification Processor thread: {e}", exc_info=True)
        else:
            logger.info("Notification Processor thread was not running or already joined.")

        # Bersihkan antrian notifikasi untuk memastikan tidak ada yang tertinggal jika thread gagal join
        # Meskipun idealnya thread yang sedang berjalan yang akan mengosongkannya.
        if hasattr(self, 'notification_queue'): # Pastikan atribut ada
            logger.debug("Clearing any remaining items in the notification queue...")
            while not self.notification_queue.empty():
                try:
                    self.notification_queue.get_nowait()
                    self.notification_queue.task_done()
                except queue.Empty:
                    break # Antrian sudah kosong
            logger.debug("Notification queue cleared.")
        
        logger.warning("Trading bot stop sequence complete. Bot is now stopped.")
        return True
        
    def signal_check_loop(self):
        logger.info("Signal check loop (for active trading pairs) initiated.")
        
        while self.running:
            try:
                if not self.check_daily_limits():
                    logger.info("Daily limits reached. Stopping trading from signal_check_loop.")
                    self.stop_trading() # stop_trading akan handle self.running = False
                    break # Keluar dari loop ini
                
                if DAILY_STATS["total_trades"] >= self.config.get("max_daily_trades", 10):
                    logger.info(
                        f"Max daily trades ({DAILY_STATS['total_trades']}/{self.config.get('max_daily_trades',10)}) reached. "
                        "Stopping trading."
                    )
                    # Notifikasi dan stop sudah dihandle di dalam check_daily_limits jika diimplementasikan di sana
                    # atau tambahkan notifikasi di sini jika perlu
                    self.stop_trading()
                    break
                
                active_pairs_this_iteration = []
                with self.active_trading_pairs_lock:
                    # Buat salinan dari daftar pair yang aktif untuk diiterasi
                    # Ini penting karena daftar bisa diubah oleh dynamic_pair_scan_loop
                    active_pairs_this_iteration = list(self.config.get("trading_pairs", []))

                if not active_pairs_this_iteration:
                    if not self.config.get("dynamic_pair_selection", False):
                        logger.debug("SignalCheck: No trading pairs configured and dynamic selection is OFF. Idling.")
                    else:
                        logger.debug("SignalCheck: No active trading pairs currently (waiting for dynamic scanner). Idling.")
                    # Tetap tidur sesuai interval utama, jangan spin CPU
                    time.sleep(self.config.get("signal_check_interval", 30))
                    continue

                logger.debug(f"SignalCheck: Checking signals for active pairs: {active_pairs_this_iteration}")
                for symbol_to_trade in active_pairs_this_iteration:
                    if not self.running: # Cek lagi jika bot dihentikan di tengah iterasi pair
                        logger.info("SignalCheck: Bot stopping, aborting current pair checks.")
                        break 

                    # Cek apakah sudah ada trade aktif untuk simbol ini
                    has_active_trade_for_symbol = any(
                        t['symbol'] == symbol_to_trade and not t.get('completed', False) for t in ACTIVE_TRADES
                    )
                    if has_active_trade_for_symbol:
                        logger.debug(f"SignalCheck: Skipping {symbol_to_trade}, active trade exists.")
                        continue
                        
                    logger.debug(f"SignalCheck: Evaluating signal for active pair: {symbol_to_trade}")
                    signal = self.technical_analysis.get_signal(symbol_to_trade) # Timeframe default
                    
                    if signal and signal['action'] != 'WAIT': # Tidak perlu cek strength lagi, get_signal sudah handle
                        logger.info(f"SignalCheck: Processing signal for {symbol_to_trade}: {signal['action']}")
                        self.process_signal(signal) # Ini yang akan membuka posisi
                        # Mungkin tambahkan jeda kecil setelah berhasil memproses sinyal & membuka trade
                        time.sleep(self.config.get("post_trade_delay_seconds", 2)) 
                    # Jeda antar pemeriksaan simbol jika diperlukan untuk rate limit API
                    # time.sleep(self.config.get("api_call_delay_seconds", 0.2))


                if not self.running: break # Cek setelah loop pair

                logger.debug(f"SignalCheck: Cycle complete. Sleeping for {self.config.get('signal_check_interval', 30)}s.")
                # Tidur dengan cara yang bisa diinterupsi
                interval = self.config.get("signal_check_interval", 30)
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"SignalCheck: Error in signal_check_loop: {e}", exc_info=True)
                # Tidur lebih lama jika ada error, tapi tetap bisa diinterupsi
                for _ in range(30): # Misal 30 detik
                    if not self.running: break
                    time.sleep(1)
                    
        logger.info("Signal check loop has stopped.")
        
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
        self.application.add_handler(CommandHandler("scannedpairs", self.scanned_pairs_command))
        
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
        if not await self.is_authorized(update):
            return

        help_text = (
            "<b>Available commands:</b>\n\n"
            "<u>Core Commands:</u>\n"
            "  /start - Start the bot & show main menu\n"
            "  /help - Show this help message\n"
            "  /status - Show current bot status\n"
            "  /config - Show current configuration\n"
            "  /set <code>[param] [value]</code> - Set general config parameter\n"
            "  /trades - Show recent trades\n"
            "  /stats - Show daily trading statistics\n"
            "  /balance - Show your Binance account balance\n"
            "  /positions - Show open positions\n"
            "  /indicators <code>[SYMBOL]</code> - Show indicators for a symbol\n\n"
            "<u>Trading Control:</u>\n"
            "  /starttrade - Start trading (will prompt for mode)\n"
            "  /stoptrade - Stop trading\n"
            "  /closeall - Close all open positions (if any)\n\n"
            "<u>Trading Settings:</u>\n"
            "  /setleverage <code>[value]</code> - Set leverage (e.g., 10)\n"
            "  /setmode <code>[mode]</code> - Set trading mode (safe, standard, aggressive)\n"
            "  /setprofit <code>[target%] [limit%]</code> - Set daily profit target & loss limit\n\n"
            "<u>Dynamic Pair Selection (if enabled via /toggledynamic):</u>\n"
            "  /toggledynamic - Enable/Disable dynamic pair selection\n"
            "  /watchlist <code>[add/remove/list] [SYMBOL]</code> - Manage dynamic watchlist\n"
            "  /setdynamicpairs <code>[count]</code> - Set max active dynamic pairs\n"
            "  /setminvolume <code>[USDT_volume]</code> - Set min 24h USDT volume for scan\n"
            "  /setscaninterval <code>[seconds]</code> - Set dynamic scan interval\n"
            "  /scannedpairs - Show last scanned dynamic pair candidates\n\n"
            "<u>API & Real Trading:</u>\n"
            "  /enablereal - Enable REAL trading (use with caution!)\n"
            "  /disablereal - Disable real trading (simulation mode)\n"
            "  /toggletestnet - Switch between Binance Testnet & Production API\n"
            "  /testapi - Test your Binance API connection\n\n"
            "<i>Use parameters without brackets. E.g., /setleverage 10</i>"
        )
        await update.message.reply_text(help_text, parse_mode=constants.ParseMode.HTML)    
    

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return

        # Tentukan objek pesan yang akan di-reply atau diedit
        message_object_to_interact_with = None
        if update.callback_query:
            message_object_to_interact_with = update.callback_query.message
        elif update.message:
            message_object_to_interact_with = update.message
        
        if not message_object_to_interact_with:
            logger.error("status_command: Could not determine message object from update.")
            # Jika chat ada, coba kirim pesan error ke chat tersebut
            if update.effective_chat:
                try:
                    await update.effective_chat.send_message("Error: Could not process status request due to missing message context.")
                except Exception as e_send:
                    logger.error(f"status_command: Failed to send error message to chat: {e_send}")
            return
            
        if not self.trading_bot: # Periksa apakah trading_bot sudah di-set
            logger.warning("status_command: self.trading_bot is not initialized.")
            try:
                await message_object_to_interact_with.reply_text("Trading bot is not initialized. Please check bot setup.")
            except Exception as e_reply:
                 logger.error(f"status_command: Failed to reply when trading_bot is None: {e_reply}")
            return

        # --- Akses konfigurasi melalui self.trading_bot.config ---
        bot_config = self.trading_bot.config # Buat referensi singkat

        dynamic_selection_status = "❌ Disabled"
        active_dynamic_pairs_text = ""
        # Gunakan bot_config untuk mengakses setting dynamic_pair_selection
        if bot_config.get("dynamic_pair_selection", False):
            dynamic_selection_status = "✅ Enabled"
            # Akses aman ke daftar pair yang mungkin diubah oleh thread lain
            with self.trading_bot.active_trading_pairs_lock:
                 active_pairs = bot_config.get("trading_pairs", []) # Ambil dari bot_config
            active_dynamic_pairs_text = f"\n  Active Dynamic Pairs: {', '.join(active_pairs) if active_pairs else 'None selected yet'}"
            
        active_trades = [t for t in ACTIVE_TRADES if not t.get('completed', False)]
        completed_trades = COMPLETED_TRADES # Ini adalah variabel global, pastikan konsisten

        total_profit_pct_leveraged = 0.0 # Ganti nama agar lebih jelas
        win_count = 0
        loss_count = 0
        total_profit_usdt = 0.0

        for trade in completed_trades:
            # Gunakan profit USDT untuk menentukan win/loss agar lebih akurat
            profit_this_trade_usdt = trade.get('profit_usdt', 0.0)
            total_profit_usdt += profit_this_trade_usdt
            
            # Akumulasi leveraged profit percentage jika ada
            total_profit_pct_leveraged += trade.get('leveraged_profit_pct', 0.0)

            if profit_this_trade_usdt > 0: # Menang jika profit USDT > 0
                win_count += 1
            elif profit_this_trade_usdt < 0: # Kalah jika profit USDT < 0 (abaikan jika 0)
                loss_count += 1
        
        # Hitung win rate berdasarkan trade yang menghasilkan profit atau loss
        actual_trades_for_win_rate = win_count + loss_count
        win_rate = (win_count / actual_trades_for_win_rate * 100) if actual_trades_for_win_rate > 0 else 0.0
        
        real_trading_status = "✅ Enabled" if bot_config.get("use_real_trading", False) else "❌ Disabled (Simulation)"

        status_text = (
            f"📊 <b>BOT STATUS</b> 📊\n\n"
            f"<b>Trading:</b> {'✅ Running' if self.trading_bot.running else '❌ Stopped'}\n"
            f"<b>Mode:</b> {bot_config.get('trading_mode', 'N/A').capitalize()}\n"
            f"<b>Leverage:</b> {bot_config.get('leverage', 0)}x\n"
            f"<b>Take Profit:</b> {bot_config.get('take_profit', 0.0)}%\n"
            f"<b>Stop Loss:</b> {bot_config.get('stop_loss', 0.0)}%\n\n"
            f"<b>Real Trading:</b> {real_trading_status}\n"
            f"<b>Active Trades:</b> {len(active_trades)}\n"
            f"<b>Completed Trades (Win/Loss/Total):</b> {win_count}/{loss_count}/{len(completed_trades)}\n"
            f"<b>Total P/L (Leveraged %):</b> {total_profit_pct_leveraged:.2f}%\n" # Total dari leveraged_profit_pct
            f"<b>Total P/L (USDT):</b> ${total_profit_usdt:.2f}\n"
            f"<b>Win Rate:</b> {win_rate:.1f}% ({win_count}/{actual_trades_for_win_rate})\n\n"
            f"<u>Dynamic Pair Selection:</u>\n"
            f"  <b>Status:</b> {dynamic_selection_status}"
            f"{active_dynamic_pairs_text}\n"
            f"  Watchlist Size: {len(bot_config.get('dynamic_watchlist_symbols',[]))}\n"
            f"  Max Active Dynamic: {bot_config.get('max_active_dynamic_pairs',0)}\n\n"
            f"<b>Currently Monitored Pairs:</b> {', '.join(bot_config.get('trading_pairs', ['N/A']))}\n" # Pair yang benar-benar dipantau
            f"<b>Daily Profit Target:</b> {bot_config.get('daily_profit_target', 0.0)}%\n"
            f"<b>Daily Loss Limit:</b> {bot_config.get('daily_loss_limit', 0.0)}%"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Start Trading", callback_data="select_trading_mode"),
             InlineKeyboardButton("⏹️ Stop Trading", callback_data="stop_trading")],
            [InlineKeyboardButton("📊 Daily Stats", callback_data="stats"), # Ganti nama tombol jika ini lebih cocok
             InlineKeyboardButton("📈 Open Positions", callback_data="positions")],
            [InlineKeyboardButton("⚙️ Bot Settings", callback_data="config"),
             InlineKeyboardButton(f"{'🔴 Disable' if bot_config.get('use_real_trading', False) else '🟢 Enable'} Real Trading",
                                 callback_data="toggle_real_trading")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            if update.callback_query: # Jika ini adalah callback dari tombol
                await update.callback_query.edit_message_text(
                    text=status_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
            else: # Jika ini adalah command /status biasa
                await message_object_to_interact_with.reply_text(
                    text=status_text,
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"status_command: Failed to send/edit status message: {e}", exc_info=True)
            # Fallback jika edit gagal (misal, pesan terlalu tua atau tidak berubah)
            if update.callback_query: # Hanya coba kirim baru jika edit gagal pada callback
                try:
                    await message_object_to_interact_with.reply_text( # Seharusnya .send_message jika mau baru
                        text=status_text,
                        reply_markup=reply_markup,
                        parse_mode=constants.ParseMode.HTML
                    )
                except Exception as e_fallback:
                    logger.error(f"status_command: Fallback reply_text also failed: {e_fallback}")
    
    async def scanned_pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update):
            return
        if not self.trading_bot:
            await update.message.reply_text("Trading bot not initialized.")
            return
        
        if not self.trading_bot.config.get("dynamic_pair_selection", False):
            await update.message.reply_text(
                "Dynamic pair selection is currently disabled.\n"
                "Enable it via config or a command (e.g., /toggledynamic)."
            )
            return

        scanned_info = "🔎 <b>Last Scanned Dynamic Pair Candidates</b> 🔍\n\n"
        if not self.trading_bot.currently_scanned_pairs: # Atribut ini harus diisi oleh dynamic_pair_scan_loop
            scanned_info += "No strong signals found in the last scan, or scan has not run yet / found no candidates."
        else:
            # Tampilkan beberapa kandidat teratas saja agar pesan tidak terlalu panjang
            display_limit = 10 
            for i, signal_data in enumerate(self.trading_bot.currently_scanned_pairs[:display_limit]):
                scanned_info += (
                    f"<b>{i+1}. {signal_data['symbol']}</b>:\n"
                    f"  Action: <i>{signal_data['action']}</i>, Strength: {signal_data['strength']}\n"
                    f"  Price: ${signal_data['price']:.4f}\n"
                    f"  Reasons: {'; '.join(signal_data.get('reasons', ['N/A']))}\n\n"
                )
            if len(self.trading_bot.currently_scanned_pairs) > display_limit:
                scanned_info += f"... and {len(self.trading_bot.currently_scanned_pairs) - display_limit} more candidates.\n"
        
        scanned_info += f"\nCurrently active trading pairs: {', '.join(self.trading_bot.config.get('trading_pairs',[])) if self.trading_bot.config.get('trading_pairs',[]) else 'None'}"
            
        # Batasi panjang pesan
        if len(scanned_info) > constants.MessageLimit.TEXT_LENGTH: # Gunakan konstanta dari PTB
            scanned_info = scanned_info[:constants.MessageLimit.TEXT_LENGTH - 20] + "\n... (message truncated)"
            
        await update.message.reply_text(scanned_info, parse_mode=constants.ParseMode.HTML)
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
