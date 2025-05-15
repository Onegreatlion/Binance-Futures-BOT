# 🤖 Binance Futures Trading Bot dengan Notifikasi Telegram 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/stargazers"><img src="https://img.shields.io/github/stars/Afinnn954/Binance-Futures-BOT?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/Afinnn954/Binance-Futures-BOT/issues"><img src="https://img.shields.io/github/issues/Afinnn954/Binance-Futures-BOT" alt="GitHub Issues"></a>
</p>

Bot ini dirancang untuk melakukan **trading otomatis** 📈 pada platform **Binance Futures** berdasarkan sinyal dari indikator teknikal (RSI, EMA, Bollinger Bands) dan dikelola sepenuhnya melalui **Telegram** 📱. Bot ini menawarkan berbagai mode trading, manajemen risiko, dan notifikasi real-time untuk membantu Anda mengotomatiskan strategi trading Anda.

**Repo GitHub:** [https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)

---

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

Skrip ini didistribusikan di bawah Lisensi MIT. Lihat `LICENSE` untuk informasi lebih lanjut (jika ada file LICENSE).
Skrip ini disediakan "SEBAGAIMANA ADANYA" tanpa jaminan apa pun. Pengguna bertanggung jawab penuh atas penggunaan skrip ini.

---

⭐ Jika Anda merasa bot ini bermanfaat, pertimbangkan untuk memberikan bintang pada repositori ini! ⭐
[https://github.com/Afinnn954/Binance-Futures-BOT](https://github.com/Afinnn954/Binance-Futures-BOT)
