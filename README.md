# 🤖 Binance Futures Trading Bot with Telegram Notifications 🚀 / Bot Trading Binance Futures dengan Notifikasi Telegram 🇮🇩

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/stargazers"><img src="https://img.shields.io/github/stars/Afinnn954/Binance-Futures-BOT?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/issues"><img src="https://img.shields.io/github/issues/Afinnn954/Binance-Futures-BOT" alt="GitHub Issues"></a>
</p>

**GitHub Repo:** [https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

---

<!-- ENGLISH SECTION -->
<details>
<summary><strong>🇬🇧 English Version (Click to Expand)</strong></summary>

This bot is designed for **automated trading** 📈 on the **Binance Futures** platform based on signals from technical indicators (RSI, EMA, Bollinger Bands) and is fully managed via **Telegram** 📱. It offers various trading modes, risk management features, and real-time notifications to help you automate your trading strategies.

## ✨ Key Features (Detailed) ✨

1.  📊 **Technical Indicators & Strategy**
    *   **RSI + Candle Pattern:**
        *   🟢 **LONG:** RSI below oversold level (e.g., 30) AND the last candle is green.
        *   🔴 **SHORT:** RSI above overbought level (e.g., 70) AND the last candle is red.
    *   **EMA Crossover:** Signals based on the crossover between a short-period Exponential Moving Average (e.g., EMA 20) and a long-period EMA (e.g., EMA 50).
    *   **Bollinger Bands Breakout:** Detects potential trend reversals or continuations when the price breaks out of the upper or lower Bollinger Bands.

2.  💼 **Position Management**
    *   **Automatic Position Sizing:** Calculated based on a percentage of the available account balance and the leverage used.
    *   **Take Profit (TP):** `TAKE_PROFIT_MARKET` orders are automatically placed at a predefined profit percentage from the entry price (e.g., +0.6% for *Safe* mode).
    *   **Stop Loss (SL):** `STOP_MARKET` orders are automatically placed at a predefined loss percentage from the entry price (e.g., -0.3% for *Safe* mode).
    *   **Hedge Mode:** Supports opening simultaneous LONG and SHORT positions for the same trading pair (`positionSide='LONG'` or `'SHORT'`).

3.  🛡️ **Risk Management**
    *   **Daily Profit Target:** The bot will stop opening new trades if the daily profit percentage target is reached. 🎯
    *   **Daily Loss Limit:** The bot will stop opening new trades if the daily loss percentage limit is reached. 🛑
    *   **Flexible Leverage:** Leverage can be configured for each trading mode or set manually.
    *   **Percentage Position Size:** Controls risk per trade by defining the position size as a percentage of the total balance.

4.  ⚙️ **Trading Modes (Default & Customizable)**
    *   **Safe 🐢:**
        *   Leverage: 5x
        *   Take Profit: 0.6%
        *   Stop Loss: 0.3%
        *   Position Size: 10% of balance
        *   Max Daily Trades: 10
    *   **Standard 🚶‍♂️:**
        *   Leverage: 10x
        *   Take Profit: 1.0%
        *   Stop Loss: 0.5%
        *   Position Size: 15% of balance
        *   Max Daily Trades: 15
    *   **Aggressive 🚀:**
        *   Leverage: 20x
        *   Take Profit: 1.5%
        *   Stop Loss: 0.7%
        *   Position Size: 20% of balance
        *   Max Daily Trades: 20
    *(All these trading mode parameters and more can be further customized via configuration or Telegram commands).*

5.  🔔 **Telegram Monitoring & Notifications**
    *   **Real-time Trade Notifications:** Instant alerts for new position openings, position closings (due to TP, SL, or manual), and any errors encountered.
    *   **Daily Profit/Loss (PnL) Tracking:** Daily statistical reports sent via Telegram, including total PnL, win rate, etc. 💰
    *   **On-Demand Indicator Analysis:** Get the latest technical indicator analysis for a specific trading pair using the `/indicators [symbol]` command.
    *   **Bot Status & Configuration:** Monitor bot status and view/change configurations directly from Telegram.

---

## 🛠️ Prerequisites

1.  **Python 3.8+** 🐍
2.  **Binance Account:**
    *   API Key and Secret Key for your **Futures** account.
    *   Ensure the API Key has "Enable Futures" permission.
    *   For security, consider enabling IP restrictions for your API Key if possible.
3.  **Telegram Account:**
    *   Create a new Telegram bot via [@BotFather](https://t.me/BotFather) to get your **Bot Token**. 🤖
    *   Obtain your Telegram **User ID** (e.g., via a bot like [@userinfobot](https://t.me/userinfobot)). This is required for admin authorization. 🆔

---

## 🚀 Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Afinnn954/Binance-Futures-BOT.git
    cd Binance-Futures-BOT
    ```

2.  **Create a Virtual Environment (Highly Recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

3.  **Install Dependencies:**
    Ensure you have the `requirements.txt` file in the directory, then run:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📝 Initial Configuration

Open the `binance-futures-bot.py` script file and edit the following configuration sections:

1.  **Telegram Bot Configuration:**
    ```python
    # ======== BOT CONFIGURATION ========
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ADMIN_USER_IDS = [YOUR_TELEGRAM_USER_ID_HERE] # e.g., [123456789] or [123, 456]
    # ==================================
    ```

2.  **Binance API Configuration:**
    ```python
    # Binance API configuration
    BINANCE_API_KEY = "YOUR_BINANCE_API_KEY_HERE"
    BINANCE_API_SECRET = "YOUR_BINANCE_API_SECRET_HERE"
    ```

3.  **Initial Bot Settings (Optional, can be changed via Telegram):**
    In the `CONFIG` dictionary:
    ```python
    CONFIG = {
        # ...
        "trading_pairs": ["BTCUSDT", "ETHUSDT"], # Default trading pairs
        "trading_mode": "safe",     # Initial trading mode
        "use_testnet": True,        # True for Testnet, False for Production (Live)
        "use_real_trading": False,  # True for real trading (USE WITH EXTREME CAUTION!)
        "daily_profit_target": 5.0, # Default daily profit target (%)
        "daily_loss_limit": 3.0,    # Default daily loss limit (%)
        # ...
    }
    ```

---

## ▶️ How to Use

1.  **Run the Bot:**
    From your terminal or command prompt (ensure the virtual environment is active):
    ```bash
    python binance-futures-bot.py
    ```
    The bot will start running, and you'll see logs in the console. It will connect to Telegram.

2.  **Interact with the Bot on Telegram:**
    Open a chat with your bot on Telegram. Only users whose `ADMIN_USER_IDS` are listed can use the following commands:

    **General Commands:**
    *   `/start` 👋: Initiates interaction with the bot and displays the main menu.
    *   `/help` ℹ️: Displays the list of available commands and their functions.
    *   `/status` 📊: Shows the current status of the bot.
    *   `/config` ⚙️: Displays the current bot configuration.
    *   `/set [parameter] [value]` 🔧: Changes a configuration parameter.
        *   Example: `/set leverage 15`
    *   `/trades` 📜: Shows the history of the last few trades.
    *   `/stats` 📈: Displays daily trading statistics.
    *   `/balance` 💰: Shows your Binance Futures account balance.
    *   `/positions` 📂: Displays all current open positions.
    *   `/indicators [symbol]` 📉: Shows the latest technical indicator values.

    **Trading Commands:**
    *   `/starttrade` ▶️: Starts the automated trading process.
    *   `/stoptrade` ⏹️: Stops the automated trading process.
    *   `/closeall` ❌: Closes all current open positions (use with caution).

    **Advanced Settings Commands:**
    *   `/setleverage [value]` 🔩: Sets the default leverage.
    *   `/setmode [mode]` 🔄: Sets the trading mode (`safe`, `standard`, `aggressive`).
    *   `/addpair [symbol]` ➕: Adds a trading pair.
    *   `/removepair [symbol]` ➖: Removes a trading pair.
    *   `/setprofit [target_profit] [loss_limit]` 🎯: Sets the daily profit target (%) and loss limit (%).

    **Real Trading & Testnet Commands:**
    *   `/enablereal` 💵: Enables real trading. **WARNING: Uses real funds!**
    *   `/disablereal` 🎮: Disables real trading (returns to simulation mode).
    *   `/toggletestnet` 🧪: Switches between Testnet and Production (Live) API.
    *   `/testapi` 📡: Tests the connection to the Binance Futures API.

---

## 📂 Bot Structure

*   `BinanceFuturesAPI`: Class responsible for all interactions with the Binance Futures API.
*   `TechnicalAnalysis`: Class that calculates various technical indicators (`pandas_ta`).
*   `TradingBot`: Core class containing trading logic, status management, signal processing, and order placement.
*   `TelegramBotHandler`: Class that handles all user interactions via Telegram and sends notifications.
*   `main()`: Main function to initialize all bot components and run the Telegram loop.

---

## ⚠️ Important Notes & Risk Warning ⚠️

*   **HIGH RISK:** Trading Cryptocurrency Futures is highly speculative and carries a high level of risk. You can lose your entire capital. This bot is a tool and **does not guarantee profits**. Use at your own risk.
*   **NOT FINANCIAL ADVICE:** This is not financial advice. Do Your Own Research (DYOR).
*   **API KEY SECURITY:** Keep your API Key and Secret Key confidential. Never share them.
*   **TEST ON TESTNET:** Before using real funds, conduct extensive testing on the Binance **Testnet**.
*   **MONITOR ACTIVELY:** Even though automated, monitor its performance, especially when real funds are involved.
*   **FURTHER DEVELOPMENT:** This script is a functional base. You are free to modify and enhance it.

---

## 📜 License

This script is distributed under the MIT License.
This script is provided "AS IS" without warranty of any kind. The user assumes full responsibility for the use of this script.

---

⭐ If you find this bot useful, please consider starring this repository! ⭐
[https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

</details>

---
---

<!-- INDONESIAN SECTION -->
<details open> <!-- `open` makes this section expanded by default -->
<summary><strong>🇮🇩 Versi Bahasa Indonesia (Klik untuk Memperluas/Menyempitkan)</strong></summary>

Bot ini dirancang untuk melakukan **trading otomatis** 📈 pada platform **Binance Futures** berdasarkan sinyal dari indikator teknikal (RSI, EMA, Bollinger Bands) dan dikelola sepenuhnya melalui **Telegram** 📱. Bot ini menawarkan berbagai mode trading, manajemen risiko, dan notifikasi real-time untuk membantu Anda mengotomatiskan strategi trading Anda.

## ✨ Fitur Utama (Detail) ✨

1.  📊 **Indikator Teknikal & Strategi**
    *   **RSI + Pola Candle:**
        *   🟢 **LONG:** RSI di bawah level oversold (misal, 30) DAN candle terakhir berwarna hijau.
        *   🔴 **SHORT:** RSI di atas level overbought (misal, 70) DAN candle terakhir berwarna merah.
    *   **EMA Crossover:** Sinyal berdasarkan persilangan antara Exponential Moving Average periode pendek (misal, EMA 20) dan periode panjang (misal, EMA 50).
    *   **Bollinger Bands Breakout:** Deteksi potensi pembalikan atau kelanjutan tren ketika harga menembus batas atas atau bawah Bollinger Bands.

2.  💼 **Manajemen Posisi**
    *   **Ukuran Posisi Otomatis:** Dihitung berdasarkan persentase dari saldo akun yang tersedia dan leverage yang digunakan.
    *   **Take Profit (TP):** Order `TAKE_PROFIT_MARKET` ditempatkan secara otomatis pada persentase keuntungan yang ditentukan dari harga masuk (misal, +0.6% untuk mode *Safe*).
    *   **Stop Loss (SL):** Order `STOP_MARKET` ditempatkan secara otomatis pada persentase kerugian yang ditentukan dari harga masuk (misal, -0.3% untuk mode *Safe*).
    *   **Hedge Mode:** Mendukung pembukaan posisi LONG dan SHORT secara bersamaan untuk pasangan trading yang sama (`positionSide='LONG'` atau `'SHORT'`).

3.  🛡️ **Manajemen Risiko**
    *   **Target Profit Harian:** Bot akan berhenti membuka trading baru jika target persentase keuntungan harian tercapai. 🎯
    *   **Batas Kerugian Harian:** Bot akan berhenti membuka trading baru jika batas persentase kerugian harian tercapai. 🛑
    *   **Leverage Fleksibel:** Leverage dapat dikonfigurasi untuk setiap mode trading atau diatur secara manual.
    *   **Ukuran Posisi Persentase:** Mengontrol risiko per trading dengan menentukan ukuran posisi sebagai persentase dari total saldo.

4.  ⚙️ **Mode Trading (Default & Dapat Disesuaikan)**
    *   **Safe 🐢:**
        *   Leverage: 5x
        *   Take Profit: 0.6%
        *   Stop Loss: 0.3%
        *   Ukuran Posisi: 10% dari saldo
        *   Maks. Trading Harian: 10
    *   **Standard 🚶‍♂️:**
        *   Leverage: 10x
        *   Take Profit: 1.0%
        *   Stop Loss: 0.5%
        *   Ukuran Posisi: 15% dari saldo
        *   Maks. Trading Harian: 15
    *   **Aggressive 🚀:**
        *   Leverage: 20x
        *   Take Profit: 1.5%
        *   Stop Loss: 0.7%
        *   Ukuran Posisi: 20% dari saldo
        *   Maks. Trading Harian: 20
    *(Semua parameter mode trading ini dan lainnya dapat disesuaikan lebih lanjut melalui konfigurasi atau perintah Telegram).*

5.  🔔 **Pemantauan & Notifikasi Telegram**
    *   **Notifikasi Trading Real-time:** Pemberitahuan instan untuk pembukaan posisi baru, penutupan posisi (karena TP, SL, atau manual), dan error yang terjadi.
    *   **Pelacakan Profit/Loss (PnL) Harian:** Laporan statistik harian yang dikirim melalui Telegram, termasuk total PnL, win rate, dll. 💰
    *   **Analisis Indikator Sesuai Permintaan:** Dapatkan analisis indikator teknikal terbaru untuk pasangan trading tertentu menggunakan perintah `/indicators [simbol]`.
    *   **Status Bot & Konfigurasi:** Pantau status bot dan lihat/ubah konfigurasi langsung dari Telegram.

---

## 🛠️ Prasyarat

1.  **Python 3.8+** 🐍
2.  **Akun Binance:**
    *   API Key dan Secret Key untuk akun **Futures**.
    *   Pastikan API Key memiliki izin untuk "Enable Futures".
    *   Untuk keamanan, pertimbangkan untuk mengaktifkan restriksi IP untuk API Key Anda jika memungkinkan.
3.  **Akun Telegram:**
    *   Buat bot Telegram baru melalui [@BotFather](https://t.me/BotFather) untuk mendapatkan **Bot Token**. 🤖
    *   Dapatkan **User ID** Telegram Anda (misalnya, melalui bot seperti [@userinfobot](https://t.me/userinfobot)). Ini diperlukan untuk otorisasi admin. 🆔

---

## 🚀 Instalasi

1.  **Clone Repositori:**
    ```bash
    git clone https://github.com/Afinnn954/Binance-Futures-BOT.git
    cd Binance-Futures-BOT
    ```

2.  **Buat Lingkungan Virtual (Sangat Disarankan):**
    ```bash
    python -m venv venv
    ```
    Aktifkan lingkungan virtual:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

3.  **Instal Dependensi:**
    Pastikan Anda memiliki file `requirements.txt` dalam direktori, lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📝 Konfigurasi Awal

Buka file skrip `binance-futures-bot.py` dan edit bagian konfigurasi berikut:

1.  **Konfigurasi Bot Telegram:**
    ```python
    # ======== BOT CONFIGURATION ========
    TELEGRAM_BOT_TOKEN = "MASUKKAN_BOT_TOKEN_ANDA_DISINI"
    ADMIN_USER_IDS = [MASUKKAN_USER_ID_TELEGRAM_ANDA] # misal: [123456789] atau [123, 456]
    # ==================================
    ```

2.  **Konfigurasi API Binance:**
    ```python
    # Binance API configuration
    BINANCE_API_KEY = "MASUKKAN_API_KEY_BINANCE_ANDA"
    BINANCE_API_SECRET = "MASUKKAN_API_SECRET_BINANCE_ANDA"
    ```

3.  **Pengaturan Awal Bot (Opsional, dapat diubah via Telegram):**
    Dalam kamus `CONFIG`:
    ```python
    CONFIG = {
        # ...
        "trading_pairs": ["BTCUSDT", "ETHUSDT"], # Pasangan default
        "trading_mode": "safe",     # Mode trading awal
        "use_testnet": True,        # True untuk Testnet, False untuk Production (Live)
        "use_real_trading": False,  # True untuk trading riil (HATI-HATI!)
        "daily_profit_target": 5.0, # Target profit harian default (%)
        "daily_loss_limit": 3.0,    # Batas kerugian harian default (%)
        # ...
    }
    ```

---

## ▶️ Cara Pakai

1.  **Jalankan Bot:**
    Dari terminal atau command prompt (pastikan lingkungan virtual aktif):
    ```bash
    python binance-futures-bot.py
    ```
    Bot akan mulai berjalan, dan Anda akan melihat log di konsol. Ia akan terhubung ke Telegram.

2.  **Interaksi dengan Bot di Telegram:**
    Buka chat dengan bot Anda di Telegram. Hanya pengguna yang `ADMIN_USER_IDS`-nya terdaftar yang dapat menggunakan perintah berikut:

    **Perintah Umum:**
    *   `/start` 👋: Memulai interaksi dengan bot dan menampilkan menu utama.
    *   `/help` ℹ️: Menampilkan daftar perintah yang tersedia dan fungsinya.
    *   `/status` 📊: Menampilkan status bot saat ini.
    *   `/config` ⚙️: Menampilkan konfigurasi bot saat ini.
    *   `/set [parameter] [nilai]` 🔧: Mengubah parameter konfigurasi.
        *   Contoh: `/set leverage 15`
    *   `/trades` 📜: Menampilkan histori beberapa trading terakhir.
    *   `/stats` 📈: Menampilkan statistik trading harian.
    *   `/balance` 💰: Menampilkan saldo akun Binance Futures Anda.
    *   `/positions` 📂: Menampilkan semua posisi terbuka saat ini.
    *   `/indicators [simbol]` 📉: Menampilkan nilai indikator teknikal terbaru.

    **Perintah Trading:**
    *   `/starttrade` ▶️: Memulai proses trading otomatis.
    *   `/stoptrade` ⏹️: Menghentikan proses trading otomatis.
    *   `/closeall` ❌: Menutup semua posisi terbuka saat ini (gunakan dengan hati-hati).

    **Perintah Pengaturan Lanjutan:**
    *   `/setleverage [nilai]` 🔩: Mengatur leverage default.
    *   `/setmode [mode]` 🔄: Mengatur mode trading (`safe`, `standard`, `aggressive`).
    *   `/addpair [simbol]` ➕: Menambahkan pasangan trading.
    *   `/removepair [simbol]` ➖: Menghapus pasangan trading.
    *   `/setprofit [target_profit] [loss_limit]` 🎯: Mengatur target profit harian (%) dan batas kerugian harian (%).

    **Perintah Trading Riil & Testnet:**
    *   `/enablereal` 💵: Mengaktifkan trading riil. **PERHATIAN: Menggunakan dana sungguhan!**
    *   `/disablereal` 🎮: Menonaktifkan trading riil (kembali ke mode simulasi).
    *   `/toggletestnet` 🧪: Beralih antara Testnet dan API Produksi (Live).
    *   `/testapi` 📡: Menguji koneksi ke API Binance Futures.

---

## 📂 Struktur Bot

*   `BinanceFuturesAPI`: Kelas untuk interaksi dengan API Binance Futures.
*   `TechnicalAnalysis`: Kelas untuk menghitung indikator teknikal (`pandas_ta`).
*   `TradingBot`: Kelas inti logika trading, status, pemrosesan sinyal, dan order.
*   `TelegramBotHandler`: Kelas untuk menangani interaksi Telegram dan notifikasi.
*   `main()`: Fungsi utama untuk inisialisasi dan menjalankan bot.

---

## ⚠️ Catatan Penting & Peringatan Risiko ⚠️

*   **RISIKO TINGGI:** Trading Cryptocurrency Futures sangat spekulatif. Anda bisa kehilangan seluruh modal Anda. Bot ini adalah alat dan **tidak menjamin keuntungan**. Gunakan dengan risiko Anda sendiri.
*   **BUKAN NASIHAT KEUANGAN:** Ini bukan nasihat keuangan. Lakukan riset Anda sendiri (DYOR).
*   **KEAMANAN API KEY:** Jaga kerahasiaan API Key dan Secret Key Anda. Jangan pernah membagikannya.
*   **UJI COBA DI TESTNET:** Sebelum menggunakan dana riil, lakukan pengujian ekstensif di **Testnet** Binance.
*   **PANTAU SECARA AKTIF:** Meskipun otomatis, pantau kinerjanya, terutama saat dana riil terlibat.
*   **PENGEMBANGAN LEBIH LANJUT:** Skrip ini adalah dasar. Anda bebas memodifikasi dan meningkatkannya.

---

## 📜 Lisensi

Skrip ini didistribusikan di bawah Lisensi MIT.
Skrip ini disediakan "SEBAGAIMANA ADANYA" tanpa jaminan apa pun. Pengguna bertanggung jawab penuh atas penggunaan skrip ini.

---

⭐ Jika Anda merasa bot ini bermanfaat, pertimbangkan untuk memberikan bintang pada repositori ini! ⭐
[https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

</details>
