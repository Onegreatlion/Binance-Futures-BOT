# 🤖 Binance Futures Trading Bot with Telegram Notifications 🚀 / Bot Trading Binance Futures dengan Notifikasi Telegram 🇮🇩

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/stargazers"><img src="https://img.shields.io/github/stars/Afinnn954/Binance-Futures-BOT?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/issues"><img src="https://img.shields.io/github/issues/Afinnn954/Binance-Futures-BOT" alt="GitHub Issues"></a>
</p>

**GitHub Repo:** [https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)
**Credit/Support:** Telegram [t.me/JoestarMojo](https://t.me/JoestarMojo)

---

<!-- ENGLISH SECTION -->
<details>
<summary><strong>🇬🇧 English Version (Click to Expand)</strong></summary>

This bot is designed for **automated trading** 📈 on the **Binance Futures** platform based on signals from technical indicators (RSI, EMA, Bollinger Bands) and is fully managed via **Telegram** 📱. It offers various trading modes, risk management features, dynamic pair selection, and real-time notifications to help you automate your trading strategies.

## ✨ Key Features (Detailed) ✨

1.  📊 **Technical Indicators & Strategy**
    *   **RSI + Candle Pattern:**
        *   🟢 **LONG:** RSI below oversold level (e.g., 30) AND the last candle is green.
        *   🔴 **SHORT:** RSI above overbought level (e.g., 70) AND the last candle is red.
    *   **EMA Crossover:** Signals based on the crossover and alignment between a short-period Exponential Moving Average (e.g., EMA 20) and a long-period EMA (e.g., EMA 50) relative to the price.
    *   **Bollinger Bands Breakout:** Detects potential trend reversals or volatility confirmations when the price breaks out of the upper or lower Bollinger Bands.
    *   **Signal Strength Logic:** Signals are evaluated based on the cumulative strength from various indicator conditions to trigger a trade.

2.  🆕 **🔍 Dynamic Pair Selection (NEW!)**
    *   🌊 **Automated Scanning:** Periodically scans a user-defined watchlist of coins (`dynamic_watchlist_symbols`).
    *   💧 **Liquidity Filter:** Considers only coins meeting a minimum 24-hour trading volume (`min_24h_volume_usdt_for_scan`).
    *   🎯 **Signal-Based Selection:** Selects a configurable number of top pairs (`max_active_dynamic_pairs`) exhibiting the strongest trading signals.
    *   🔄 **Dynamic Trading List:** The list of actively traded pairs (`trading_pairs`) can change automatically based on scan results, allowing the bot to adapt to market opportunities.

3.  💼 **Position Management**
    *   **Automatic Position Sizing:** Can be calculated based on a percentage of the available account balance (`position_size_percentage`) or a fixed USDT amount (`position_size_usdt`).
    *   **Take Profit (TP):** `TAKE_PROFIT_MARKET` orders are automatically placed at a predefined profit percentage.
    *   **Stop Loss (SL):** `STOP_MARKET` orders are automatically placed at a predefined loss percentage.
    *   **Hedge Mode:** Supports opening simultaneous LONG and SHORT positions for the same trading pair if your Binance account is set to Hedge Mode.

4.  🛡️ **Risk Management**
    *   **Daily Profit Target:** The bot stops opening new trades if the daily profit percentage target is reached. 🎯
    *   **Daily Loss Limit:** The bot stops opening new trades if the daily loss percentage limit is reached. 🛑
    *   **Flexible Leverage:** Leverage can be configured for each trading mode or set manually.
    *   **Max Daily Trades:** Limits the number of trades per day to prevent over-trading.

5.  ⚙️ **Trading Modes (Default & Customizable)**
    *   **Safe 🐢:** Lower leverage, tighter TP/SL, smaller position size.
    *   **Standard 🚶‍♂️:** Balanced risk/reward parameters.
    *   **Aggressive 🚀:** Higher leverage, wider TP/SL, larger position size.
    *(All trading mode parameters are defined in `TRADING_MODES` and can be customized. The bot applies these settings when a mode is selected).*

6.  🔔 **Telegram Monitoring & Notifications**
    *   **Real-time Trade Notifications:** Instant alerts for new position openings, closings (TP, SL, manual), dynamic pair updates, and errors.
    *   **Daily PnL Tracking:** Daily statistical reports including total PnL, win rate, etc. 💰
    *   **On-Demand Analysis:** Get technical indicator values (`/indicators`) and scanned pair candidates (`/scannedpairs` 🆕).
    *   **Full Bot Control:** Status, configuration, start/stop, manage pairs, and more, directly from Telegram.

---

## 🛠️ Prerequisites

1.  **Python 3.8+** 🐍
2.  **Binance Account:**
    *   API Key and Secret Key for your **Futures** account.
    *   Ensure "Enable Futures" permission is active for the API Key.
    *   Consider IP restrictions for API Key security.
3.  **Telegram Account:**
    *   Create a Telegram bot via [@BotFather](https://t.me/BotFather) to get your **Bot Token**. 🤖
    *   Obtain your Telegram **User ID** (e.g., via [@userinfobot](https://t.me/userinfobot)) for admin authorization. 🆔

---

## 🚀 Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Afinnn954/Binance-Futures-BOT.git
    cd Binance-Futures-BOT
    ```

2.  **Create & Activate Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Ensure `requirements.txt` exists and contains necessary packages (e.g., `python-telegram-bot`, `requests`, `numpy`, `pandas`, `pandas-ta`). Then run:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📝 Initial Configuration

Open the `Futures.py` script (or your main bot file) and edit these sections:

1.  **Telegram & Admin Configuration:**
    ```python
    # ======== BOT CONFIGURATION ========
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ADMIN_USER_IDS = [YOUR_TELEGRAM_USER_ID_HERE] # e.g., [123456789]
    # ==================================
    ```

2.  **Binance API Configuration:**
    ```python
    BINANCE_API_KEY = "YOUR_BINANCE_FUTURES_API_KEY"
    BINANCE_API_SECRET = "YOUR_BINANCE_FUTURES_API_SECRET"
    ```

3.  **Main Bot Settings (`CONFIG` dictionary):**
    ```python
    CONFIG = {
        "api_key": BINANCE_API_KEY,
        "api_secret": BINANCE_API_SECRET,
        
        "trading_pairs": ["BTCUSDT", "ETHUSDT"], # Initial/static pairs if dynamic selection is OFF
                                                 # This list is OVERWRITTEN if dynamic_pair_selection is True.
        
        # --- DYNAMIC PAIR SELECTION (NEW!) ---
        "dynamic_pair_selection": True,        # Set to True to enable this feature.
        "dynamic_watchlist_symbols": [         # Coins the bot will scan if dynamic selection is active.
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", 
            "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "TRXUSDT", 
            # Add more popular and liquid USDT perpetual pairs
        ],
        "max_active_dynamic_pairs": 3,         # Max number of dynamically selected pairs to trade concurrently.
        "min_24h_volume_usdt_for_scan": 10000000, # Minimum 24h volume in USDT for a coin to be considered (e.g., 10M USDT).
        "dynamic_scan_interval_seconds": 300,  # How often to scan for dynamic pairs (e.g., 300s = 5 mins).
        "api_call_delay_seconds": 0.5,         # Small delay between API calls during scanning (prevents rate limits).

        # --- Position & Risk ---
        "position_size_usdt": 100,             # Default USDT amount if use_percentage=False.
        "use_percentage": True,                # True to use percentage of balance for position size.
        "position_size_percentage": 5.0,       # Percentage of available balance per trade (e.g., 5%).
        "take_profit": 0.6,                    # Default Take Profit %.
        "stop_loss": 0.3,                      # Default Stop Loss %.
        "leverage": 10,                        # Default leverage.

        # --- Operational ---
        "trading_enabled": False,              # Bot trading status on start (control via /starttrade).
        "trading_mode": "standard",            # Default trading mode ("safe", "standard", "aggressive").
        "max_daily_trades": 15,                # Max trades per day.
        "signal_check_interval": 30,           # Interval (seconds) to check signals for active pairs.
        "use_testnet": False,                  # True for Binance Testnet, False for Live Production.
        "use_real_trading": False,             # CRITICAL: False for simulation, True for real funds.
        "daily_profit_target": 5.0,            # Daily profit target %.
        "daily_loss_limit": 3.0,               # Daily loss limit %.
        "hedge_mode": True,                    # True if your Binance Futures account is in Hedge Mode.
        "post_trade_delay_seconds": 2,         # Delay (seconds) after a trade before checking signals again.
    }
    ```

4.  **Technical Indicator Settings (`INDICATOR_SETTINGS` dictionary):**
    ```python
    INDICATOR_SETTINGS = {
        "rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_short": 20, "ema_long": 50,
        "bb_period": 20, "bb_std": 2.0,
        "candle_timeframe": "5m",              # Candlestick timeframe (e.g., "1m", "5m", "1h").
        "signal_strength_threshold": 30        # Minimum signal strength required to open a trade.
    }
    ```

5.  **Trading Modes (`TRADING_MODES` dictionary):**
    Review and customize the predefined "safe", "standard", and "aggressive" modes, or add your own. Each mode defines leverage, TP/SL percentages, position size percentage, and max daily trades.

---

## ▶️ How to Use

1.  **Run the Bot:**
    From your terminal (with virtual environment active):
    ```bash
    python Futures.py  # Or your main bot script name
    ```
    The bot will start, connect to Binance and Telegram. Monitor console logs.

2.  **Interact via Telegram:**
    Only `ADMIN_USER_IDS` can use these commands.

    **General & Status:**
    *   `/start` 👋: Main menu.
    *   `/help` ℹ️: List of commands.
    *   `/status` 📊: Bot's current operational status.
    *   `/config` ⚙️: Current bot configuration.
    *   `/stats` 📈: Daily trading statistics.
    *   `/balance` 💰: Binance Futures account balance.
    *   `/positions` 📂: Current open positions.
    *   `/trades` 📜: Recent trade history.
    *   `/indicators <SYMBOL>` 📉: Technical indicators for a symbol (e.g., `/indicators BTCUSDT`).

    **Trading Control:**
    *   `/starttrade` ▶️: Starts automated trading.
    *   `/stoptrade` ⏹️: Stops automated trading.
    *   `/closeall` ❌: Closes all open positions (use cautiously!).

    **Settings & Configuration:**
    *   `/set <param> <value>` 🔧: General config change (e.g., `/set leverage 15`).
    *   `/setleverage <val>` 🔩, `/setmode <mode>`, `/addpair <sym>`, `/removepair <sym>`, `/setprofit <tp%> <sl%>` 🎯.

    🆕 **Dynamic Pair Selection Commands:**
    *   `/toggledynamic` (To be implemented): Toggles `dynamic_pair_selection` True/False.
    *   `/watchlist <add|remove|list> [SYMBOL]` (To be implemented): Manages `dynamic_watchlist_symbols`.
    *   `/setdynamicpairs <count>` (To be implemented): Sets `max_active_dynamic_pairs`.
    *   `/setminvolume <usdt_amount>` (To be implemented): Sets `min_24h_volume_usdt_for_scan`.
    *   `/scannedpairs` 🕵️: Displays the last set of dynamically scanned candidate pairs and their signal strength.

    **Real Trading & API:**
    *   `/enablereal` 💵: **Activates real trading. USE WITH EXTREME CAUTION!**
    *   `/disablereal` 🎮: Deactivates real trading (simulation mode).
    *   `/toggletestnet` 🧪: Switches between Live and Testnet APIs.
    *   `/testapi` 📡: Tests Binance API connection.

---

## 📂 Bot Structure

*   `BinanceFuturesAPI`: Handles Binance Futures API interactions.
*   `TechnicalAnalysis`: Calculates technical indicators using `pandas_ta`.
*   `TradingBot`: Core trading logic, signal processing, order management, dynamic pair scanning.
*   `TelegramBotHandler`: Manages Telegram interactions and notifications.
*   `main()`: Initializes and runs the bot.

---

## ⚠️ Important Notes & Risk Warning ⚠️

*   **HIGH RISK:** Cryptocurrency Futures trading is speculative and carries substantial risk. You can lose your entire capital. This bot is a tool and **does not guarantee profits**. Use at your own discretion and risk.
*   **NOT FINANCIAL ADVICE:** This content is for informational purposes only and should not be construed as financial advice. Always Do Your Own Research (DYOR).
*   **API KEY SECURITY:** Protect your API Key and Secret Key. Never share them or commit them to public repositories.
*   **TEST THOROUGHLY:** Before deploying with real funds, extensively test the bot on Binance **Testnet** and/or in simulation mode (`use_real_trading = False`).
*   **MONITOR PERFORMANCE:** Even when automated, actively monitor the bot's performance and market conditions.
*   **DYNAMIC PAIR RISKS:** While dynamic pair selection can find opportunities, it might also pick highly volatile or less understood pairs if your watchlist and liquidity filters are not set carefully.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
This script is provided "AS IS", without warranty of any kind. The user assumes all responsibility for its use.

---

⭐ If you find this bot useful, please consider starring this repository! ⭐
[https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

**Credit/Support:** Telegram [t.me/JoestarMojo](https://t.me/JoestarMojo)

</details>

---
---

<!-- INDONESIAN SECTION -->
<details open> <!-- `open` membuat bagian ini terbuka secara default -->
<summary><strong>🇮🇩 Versi Bahasa Indonesia (Klik untuk Memperluas/Menyempitkan)</strong></summary>

Bot ini dirancang untuk **trading otomatis** 📈 pada platform **Binance Futures** berdasarkan sinyal dari indikator teknikal (RSI, EMA, Bollinger Bands) dan dikelola sepenuhnya melalui **Telegram** 📱. Bot ini menawarkan berbagai mode trading, manajemen risiko, pemilihan pair dinamis, dan notifikasi real-time untuk membantu Anda mengotomatiskan strategi trading Anda.

## ✨ Fitur Utama (Detail) ✨

1.  📊 **Indikator Teknikal & Strategi**
    *   **RSI + Pola Candle:**
        *   🟢 **LONG:** RSI di bawah level oversold (misal, 30) DAN candle terakhir berwarna hijau.
        *   🔴 **SHORT:** RSI di atas level overbought (misal, 70) DAN candle terakhir berwarna merah.
    *   **EMA Crossover:** Sinyal berdasarkan persilangan dan keselarasan antara Exponential Moving Average periode pendek (misal, EMA 20) dan periode panjang (misal, EMA 50) relatif terhadap harga.
    *   **Bollinger Bands Breakout:** Mendeteksi potensi pembalikan tren atau konfirmasi volatilitas ketika harga menembus batas atas atau bawah Bollinger Bands.
    *   **Logika Kekuatan Sinyal:** Sinyal dievaluasi berdasarkan akumulasi kekuatan dari berbagai kondisi indikator untuk memicu trading.

2.  🆕 **🔍 Pemilihan Pair Dinamis (BARU!)**
    *   🌊 **Pemindaian Otomatis:** Secara periodik memindai daftar pantau koin yang ditentukan pengguna (`dynamic_watchlist_symbols`).
    *   💧 **Filter Likuiditas:** Hanya mempertimbangkan koin yang memenuhi volume trading minimum 24 jam (`min_24h_volume_usdt_for_scan`).
    *   🎯 **Seleksi Berbasis Sinyal:** Memilih sejumlah pair teratas (dapat dikonfigurasi, `max_active_dynamic_pairs`) yang menunjukkan sinyal trading terkuat.
    *   🔄 **Daftar Trading Dinamis:** Daftar pair yang aktif ditradingkan (`trading_pairs`) dapat berubah secara otomatis berdasarkan hasil pemindaian, memungkinkan bot beradaptasi dengan peluang pasar.

3.  💼 **Manajemen Posisi**
    *   **Ukuran Posisi Otomatis:** Dapat dihitung berdasarkan persentase dari saldo akun yang tersedia (`position_size_percentage`) atau jumlah USDT tetap (`position_size_usdt`).
    *   **Take Profit (TP):** Order `TAKE_PROFIT_MARKET` ditempatkan secara otomatis pada persentase keuntungan yang telah ditentukan.
    *   **Stop Loss (SL):** Order `STOP_MARKET` ditempatkan secara otomatis pada persentase kerugian yang telah ditentukan.
    *   **Hedge Mode:** Mendukung pembukaan posisi LONG dan SHORT secara bersamaan untuk pasangan trading yang sama jika akun Binance Anda diatur ke Mode Hedge.

4.  🛡️ **Manajemen Risiko**
    *   **Target Profit Harian:** Bot akan berhenti membuka trading baru jika target persentase keuntungan harian tercapai. 🎯
    *   **Batas Kerugian Harian:** Bot akan berhenti membuka trading baru jika batas persentase kerugian harian tercapai. 🛑
    *   **Leverage Fleksibel:** Leverage dapat dikonfigurasi untuk setiap mode trading atau diatur secara manual.
    *   **Maks. Trading Harian:** Membatasi jumlah trading per hari untuk mencegah over-trading.

5.  ⚙️ **Mode Trading (Default & Dapat Disesuaikan)**
    *   **Safe 🐢:** Leverage lebih rendah, TP/SL lebih ketat, ukuran posisi lebih kecil.
    *   **Standard 🚶‍♂️:** Parameter risiko/imbalan yang seimbang.
    *   **Aggressive 🚀:** Leverage lebih tinggi, TP/SL lebih lebar, ukuran posisi lebih besar.
    *(Semua parameter mode trading didefinisikan dalam `TRADING_MODES` dan dapat disesuaikan. Bot menerapkan pengaturan ini saat mode dipilih).*

6.  🔔 **Pemantauan & Notifikasi Telegram**
    *   **Notifikasi Trading Real-time:** Peringatan instan untuk pembukaan posisi baru, penutupan (TP, SL, manual), pembaruan pair dinamis, dan error.
    *   **Pelacakan PnL Harian:** Laporan statistik harian termasuk total PnL, win rate, dll. 💰
    *   **Analisis Sesuai Permintaan:** Dapatkan nilai indikator teknikal (`/indicators`) dan kandidat pair hasil scan (`/scannedpairs` 🆕).
    *   **Kontrol Bot Penuh:** Status, konfigurasi, start/stop, kelola pair, dan lainnya, langsung dari Telegram.

---

## 🛠️ Prasyarat

1.  **Python 3.8+** 🐍
2.  **Akun Binance:**
    *   API Key dan Secret Key untuk akun **Futures** Anda.
    *   Pastikan izin "Enable Futures" aktif untuk API Key tersebut.
    *   Pertimbangkan restriksi IP untuk keamanan API Key.
3.  **Akun Telegram:**
    *   Buat bot Telegram melalui [@BotFather](https://t.me/BotFather) untuk mendapatkan **Bot Token**. 🤖
    *   Dapatkan **User ID** Telegram Anda (misal, melalui [@userinfobot](https://t.me/userinfobot)) untuk otorisasi admin. 🆔

---

## 🚀 Instalasi

1.  **Clone Repositori:**
    ```bash
    git clone https://github.com/Afinnn954/Binance-Futures-BOT.git
    cd Binance-Futures-BOT
    ```

2.  **Buat & Aktifkan Lingkungan Virtual (Sangat Disarankan):**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Instal Dependensi:**
    Pastikan file `requirements.txt` ada dan berisi paket yang diperlukan (misal, `python-telegram-bot`, `requests`, `numpy`, `pandas`, `pandas-ta`). Lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📝 Konfigurasi Awal

Buka file skrip `Futures.py` (atau file bot utama Anda) dan edit bagian-bagian ini:

1.  **Konfigurasi Telegram & Admin:**
    ```python
    # ======== BOT CONFIGURATION ========
    TELEGRAM_BOT_TOKEN = "MASUKKAN_TOKEN_BOT_TELEGRAM_ANDA"
    ADMIN_USER_IDS = [MASUKKAN_USER_ID_TELEGRAM_ANDA] # misal: [123456789]
    # ==================================
    ```

2.  **Konfigurasi API Binance:**
    ```python
    BINANCE_API_KEY = "MASUKKAN_API_KEY_BINANCE_FUTURES_ANDA"
    BINANCE_API_SECRET = "MASUKKAN_API_SECRET_BINANCE_FUTURES_ANDA"
    ```

3.  **Pengaturan Utama Bot (Kamus `CONFIG`):**
    ```python
    CONFIG = {
        "api_key": BINANCE_API_KEY,
        "api_secret": BINANCE_API_SECRET,
        
        "trading_pairs": ["BTCUSDT", "ETHUSDT"], # Pair awal/statis jika pemilihan dinamis NONAKTIF.
                                                 # Daftar ini akan DIGANTI jika dynamic_pair_selection = True.
        
        # --- PEMILIHAN PAIR DINAMIS (BARU!) ---
        "dynamic_pair_selection": True,        # Atur ke True untuk mengaktifkan fitur ini.
        "dynamic_watchlist_symbols": [         # Daftar koin yang akan dipindai bot jika dinamis aktif.
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", 
            "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "TRXUSDT", 
            # Tambahkan lebih banyak koin populer dan likuid lainnya
        ],
        "max_active_dynamic_pairs": 3,         # Jumlah maksimal pair dinamis yang akan ditradingkan bersamaan.
        "min_24h_volume_usdt_for_scan": 10000000, # Volume 24 jam minimum dalam USDT agar koin dipertimbangkan (misal 10 Juta USDT).
        "dynamic_scan_interval_seconds": 300,  # Seberapa sering memindai pair dinamis (misal 300 detik = 5 menit).
        "api_call_delay_seconds": 0.5,         # Jeda kecil antar panggilan API saat memindai (mencegah rate limit).

        # --- Posisi & Risiko ---
        "position_size_usdt": 100,             # Jumlah USDT default jika use_percentage=False.
        "use_percentage": True,                # True untuk menggunakan persentase balance.
        "position_size_percentage": 5.0,       # Persentase balance yang digunakan per trade (misal 5%).
        "take_profit": 0.6,                    # Default Take Profit %.
        "stop_loss": 0.3,                      # Default Stop Loss %.
        "leverage": 10,                        # Default leverage.

        # --- Operasional ---
        "trading_enabled": False,              # Status trading bot saat mulai (kontrol via /starttrade).
        "trading_mode": "standard",            # Mode trading default ("safe", "standard", "aggressive").
        "max_daily_trades": 15,                # Maksimum trade per hari.
        "signal_check_interval": 30,           # Interval (detik) pengecekan sinyal untuk pair aktif.
        "use_testnet": False,                  # True untuk Binance Testnet, False untuk Live/Produksi.
        "use_real_trading": False,             # KRUSIAL: False untuk simulasi, True untuk dana riil.
        "daily_profit_target": 5.0,            # Target profit harian %.
        "daily_loss_limit": 3.0,               # Batas kerugian harian %.
        "hedge_mode": True,                    # True jika akun Binance Futures Anda dalam Mode Hedge.
        "post_trade_delay_seconds": 2,         # Jeda (detik) setelah trade sebelum cek sinyal lagi.
    }
    ```

4.  **Pengaturan Indikator Teknikal (Kamus `INDICATOR_SETTINGS`):**
    ```python
    INDICATOR_SETTINGS = {
        "rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_short": 20, "ema_long": 50,
        "bb_period": 20, "bb_std": 2.0,
        "candle_timeframe": "5m",              # Timeframe candlestick (misal "1m", "5m", "1h").
        "signal_strength_threshold": 30        # Kekuatan sinyal minimum untuk membuka trade.
    }
    ```

5.  **Mode Trading (Kamus `TRADING_MODES`):**
    Tinjau dan sesuaikan mode "safe", "standard", dan "aggressive" yang sudah ada, atau tambahkan mode Anda sendiri. Setiap mode mendefinisikan leverage, persentase TP/SL, persentase ukuran posisi, dan maks trade harian.

---

## ▶️ Cara Pakai

1.  **Jalankan Bot:**
    Dari terminal Anda (dengan lingkungan virtual aktif):
    ```bash
    python Futures.py  # Atau nama file skrip utama bot Anda
    ```
    Bot akan mulai, terhubung ke Binance dan Telegram. Pantau log di konsol.

2.  **Interaksi via Telegram:**
    Hanya `ADMIN_USER_IDS` yang dapat menggunakan perintah ini.

    **Umum & Status:**
    *   `/start` 👋: Menu utama.
    *   `/help` ℹ️: Daftar perintah.
    *   `/status` 📊: Status operasional bot.
    *   `/config` ⚙️: Konfigurasi bot.
    *   `/stats` 📈: Statistik trading harian.
    *   `/balance` 💰: Saldo akun Binance Futures.
    *   `/positions` 📂: Posisi terbuka saat ini.
    *   `/trades` 📜: Histori trading terbaru.
    *   `/indicators <SIMBOL>` 📉: Indikator teknikal untuk simbol (misal, `/indicators BTCUSDT`).

    **Kontrol Trading:**
    *   `/starttrade` ▶️: Memulai trading otomatis.
    *   `/stoptrade` ⏹️: Menghentikan trading otomatis.
    *   `/closeall` ❌: Menutup semua posisi terbuka (gunakan dengan hati-hati!).

    **Pengaturan & Konfigurasi:**
    *   `/set <param> <nilai>` 🔧: Mengubah konfigurasi umum (misal, `/set leverage 15`).
    *   `/setleverage <nilai>` 🔩, `/setmode <mode>`, `/addpair <simbol>`, `/removepair <simbol>`, `/setprofit <target_profit%> <loss_limit%>` 🎯.

    🆕 **Perintah Pemilihan Pair Dinamis:**
    *   `/toggledynamic` (Untuk diimplementasikan): Mengubah status `dynamic_pair_selection` True/False.
    *   `/watchlist <add|remove|list> [SIMBOL]` (Untuk diimplementasikan): Mengelola `dynamic_watchlist_symbols`.
    *   `/setdynamicpairs <jumlah>` (Untuk diimplementasikan): Mengatur `max_active_dynamic_pairs`.
    *   `/setminvolume <jumlah_usdt>` (Untuk diimplementasikan): Mengatur `min_24h_volume_usdt_for_scan`.
    *   `/scannedpairs` 🕵️: Menampilkan hasil pemindaian pair dinamis terakhir beserta kekuatan sinyalnya.

    **Trading Riil & API:**
    *   `/enablereal` 💵: **Mengaktifkan trading riil. GUNAKAN DENGAN SANGAT HATI-HATI!**
    *   `/disablereal` 🎮: Menonaktifkan trading riil (mode simulasi).
    *   `/toggletestnet` 🧪: Beralih antara API Live dan Testnet.
    *   `/testapi` 📡: Menguji koneksi API Binance.

---

## 📂 Struktur Bot

*   `BinanceFuturesAPI`: Menangani interaksi API Binance Futures.
*   `TechnicalAnalysis`: Menghitung indikator teknikal menggunakan `pandas_ta`.
*   `TradingBot`: Logika trading inti, pemrosesan sinyal, manajemen order, pemindaian pair dinamis.
*   `TelegramBotHandler`: Mengelola interaksi Telegram dan notifikasi.
*   `main()`: Inisialisasi dan menjalankan bot.

---

## ⚠️ Catatan Penting & Peringatan Risiko ⚠️

*   **RISIKO TINGGI:** Trading Cryptocurrency Futures bersifat spekulatif dan memiliki risiko tinggi. Anda bisa kehilangan seluruh modal Anda. Bot ini adalah alat dan **tidak menjamin keuntungan**. Gunakan atas kebijaksanaan dan risiko Anda sendiri.
*   **BUKAN NASIHAT KEUANGAN:** Konten ini hanya untuk tujuan informasi dan tidak boleh dianggap sebagai nasihat keuangan. Selalu Lakukan Riset Anda Sendiri (DYOR).
*   **KEAMANAN API KEY:** Lindungi API Key dan Secret Key Anda. Jangan pernah membagikannya atau menyimpannya di repositori publik.
*   **UJI SECARA MENYELURUH:** Sebelum menggunakan dana riil, uji bot secara ekstensif di **Testnet** Binance dan/atau dalam mode simulasi (`use_real_trading = False`).
*   **PANTAU KINERJA:** Meskipun otomatis, pantau kinerja bot dan kondisi pasar secara aktif.
*   **RISIKO PAIR DINAMIS:** Meskipun pemilihan pair dinamis dapat menemukan peluang, ia juga dapat memilih pair yang sangat volatil atau kurang dipahami jika daftar pantau dan filter likuiditas Anda tidak diatur dengan cermat.

---

## 📜 Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT. Lihat file `LICENSE` untuk detailnya.
Skrip ini disediakan "SEBAGAIMANA ADANYA", tanpa jaminan apa pun. Pengguna bertanggung jawab penuh atas penggunaannya.

---

⭐ Jika Anda merasa bot ini bermanfaat, pertimbangkan untuk memberikan bintang pada repositori ini! ⭐
[https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

**Credit/Support:** Telegram [t.me/JoestarMojo](https://t.me/JoestarMojo)

</details>
