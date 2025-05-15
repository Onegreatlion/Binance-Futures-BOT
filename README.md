# Bot Trading Binance Futures dengan Notifikasi Telegram

Bot ini dirancang untuk melakukan trading otomatis pada platform Binance Futures berdasarkan sinyal dari indikator teknikal (RSI, EMA, Bollinger Bands) dan dikelola sepenuhnya melalui Telegram. Bot ini menawarkan berbagai mode trading, manajemen risiko, dan notifikasi real-time untuk membantu Anda mengotomatiskan strategi trading Anda.

## Fitur Utama (Detail)

1.  **Indikator Teknikal & Strategi**
    *   **RSI + Pola Candle:**
        *   LONG: RSI di bawah level oversold (misal, 30) DAN candle terakhir berwarna hijau.
        *   SHORT: RSI di atas level overbought (misal, 70) DAN candle terakhir berwarna merah.
    *   **EMA Crossover:** Sinyal berdasarkan persilangan antara Exponential Moving Average periode pendek (misal, EMA 20) dan periode panjang (misal, EMA 50).
    *   **Bollinger Bands Breakout:** Deteksi potensi pembalikan atau kelanjutan tren ketika harga menembus batas atas atau bawah Bollinger Bands.

2.  **Manajemen Posisi**
    *   **Ukuran Posisi Otomatis:** Dihitung berdasarkan persentase dari saldo akun yang tersedia dan leverage yang digunakan.
    *   **Take Profit (TP):** Order `TAKE_PROFIT_MARKET` ditempatkan secara otomatis pada persentase keuntungan yang ditentukan dari harga masuk (misal, +0.6% untuk mode *Safe*).
    *   **Stop Loss (SL):** Order `STOP_MARKET` ditempatkan secara otomatis pada persentase kerugian yang ditentukan dari harga masuk (misal, -0.3% untuk mode *Safe*).
    *   **Hedge Mode:** Mendukung pembukaan posisi LONG dan SHORT secara bersamaan untuk pasangan trading yang sama (`positionSide='LONG'` atau `'SHORT'`).

3.  **Manajemen Risiko**
    *   **Target Profit Harian:** Bot akan berhenti membuka trading baru jika target persentase keuntungan harian tercapai.
    *   **Batas Kerugian Harian:** Bot akan berhenti membuka trading baru jika batas persentase kerugian harian tercapai.
    *   **Leverage Fleksibel:** Leverage dapat dikonfigurasi untuk setiap mode trading atau diatur secara manual.
    *   **Ukuran Posisi Persentase:** Mengontrol risiko per trading dengan menentukan ukuran posisi sebagai persentase dari total saldo.

4.  **Mode Trading (Default & Dapat Disesuaikan)**
    *   **Safe:**
        *   Leverage: 5x
        *   Take Profit: 0.6%
        *   Stop Loss: 0.3%
        *   Ukuran Posisi: 10% dari saldo
        *   Maks. Trading Harian: 10
    *   **Standard:**
        *   Leverage: 10x
        *   Take Profit: 1.0%
        *   Stop Loss: 0.5%
        *   Ukuran Posisi: 15% dari saldo
        *   Maks. Trading Harian: 15
    *   **Aggressive:**
        *   Leverage: 20x
        *   Take Profit: 1.5%
        *   Stop Loss: 0.7%
        *   Ukuran Posisi: 20% dari saldo
        *   Maks. Trading Harian: 20
    *(Semua parameter mode trading ini dan lainnya dapat disesuaikan lebih lanjut melalui konfigurasi atau perintah Telegram).*

5.  **Pemantauan & Notifikasi Telegram**
    *   **Notifikasi Trading Real-time:** Pemberitahuan instan untuk pembukaan posisi baru, penutupan posisi (karena TP, SL, atau manual), dan error yang terjadi.
    *   **Pelacakan Profit/Loss (PnL) Harian:** Laporan statistik harian yang dikirim melalui Telegram, termasuk total PnL, win rate, dll.
    *   **Analisis Indikator Sesuai Permintaan:** Dapatkan analisis indikator teknikal terbaru untuk pasangan trading tertentu menggunakan perintah `/indicators [simbol]`.
    *   **Status Bot & Konfigurasi:** Pantau status bot dan lihat/ubah konfigurasi langsung dari Telegram.

## Prasyarat

1.  **Python 3.8+**
2.  **Akun Binance:**
    *   API Key dan Secret Key untuk akun Futures.
    *   Pastikan API Key memiliki izin untuk "Enable Futures".
    *   Untuk keamanan, pertimbangkan untuk mengaktifkan restriksi IP untuk API Key Anda jika memungkinkan.
3.  **Akun Telegram:**
    *   Buat bot Telegram baru melalui [@BotFather](https://t.me/BotFather) untuk mendapatkan **Bot Token**.
    *   Dapatkan **User ID** Telegram Anda (misalnya, melalui bot seperti [@userinfobot](https://t.me/userinfobot)). Ini diperlukan untuk otorisasi admin.

## Instalasi

1.  **Clone atau Unduh Repositori:**
    ```bash
    # Jika menggunakan git
    # git clone <https://github.com/Afinnn954/Binance-Futures-BOT>
    # cd <Binance-Futures-BOT>

    # Atau cukup unduh file .py ke direktori baru
    ```

2.  **Buat Lingkungan Virtual (Sangat Disarankan):**
    ```bash
    python -m venv venv
    ```
    Aktifkan lingkungan virtual:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

3.  **Instal Dependensi:**
    Pastikan Anda memiliki file `requirements.txt` (seperti yang disediakan di awal) dalam direktori yang sama dengan skrip Anda, lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```

## Konfigurasi Awal

Buka file skrip Python (`binance-futures-bot.py`) dan edit bagian konfigurasi berikut:

1.  **Konfigurasi Bot Telegram:**
    ```python
    # ======== BOT CONFIGURATION ========
    TELEGRAM_BOT_TOKEN = "BOT_TOKEN_ANDA"  # Ganti dengan token bot Telegram Anda
    ADMIN_USER_IDS = [123456789]    # Ganti dengan User ID Telegram Anda (bisa lebih dari satu, pisahkan dengan koma, misal: [123, 456])
    # ==================================
    ```

2.  **Konfigurasi API Binance:**
    ```python
    # Binance API configuration
    BINANCE_API_KEY = "API_KEY_BINANCE_ANDA"  # Ganti dengan API Key Binance Futures Anda
    BINANCE_API_SECRET = "API_SECRET_BINANCE_ANDA" # Ganti dengan API Secret Binance Futures Anda
    ```

3.  **Pengaturan Awal Bot (Opsional, dapat diubah via Telegram):**
    Dalam kamus `CONFIG`:
    ```python
    CONFIG = {
        # ...
        "trading_pairs": ["BTCUSDT", "ETHUSDT"], # Pasangan default yang akan ditradingkan
        "trading_mode": "safe",     # Mode trading awal
        "use_testnet": True,        # True untuk Testnet, False untuk Production (Live)
        "use_real_trading": False,  # True untuk mengaktifkan trading riil (GUNAKAN DENGAN SANGAT HATI-HATI!)
        "daily_profit_target": 5.0, # Target profit harian default (%)
        "daily_loss_limit": 3.0,    # Batas kerugian harian default (%)
        # ...
    }
    ```

## Cara Pakai

1.  **Jalankan Bot:**
    Dari terminal atau command prompt (pastikan lingkungan virtual aktif):
    ```bash
    python binance-futures-bot.py
    ```
    Bot akan mulai berjalan, dan Anda akan melihat log di konsol. Ia akan terhubung ke Telegram.

2.  **Interaksi dengan Bot di Telegram:**
    Buka chat dengan bot Anda di Telegram. Hanya pengguna yang `ADMIN_USER_IDS`-nya terdaftar yang dapat menggunakan perintah berikut:

    **Perintah Umum:**
    *   `/start`: Memulai interaksi dengan bot dan menampilkan menu utama.
    *   `/help`: Menampilkan daftar perintah yang tersedia dan fungsinya.
    *   `/status`: Menampilkan status bot saat ini (berjalan/berhenti, mode trading aktif, statistik ringkas, dll.).
    *   `/config`: Menampilkan konfigurasi bot saat ini secara detail.
    *   `/set [parameter] [nilai]`: Mengubah parameter konfigurasi.
        *   Contoh: `/set leverage 15`
        *   Parameter umum yang bisa diatur: `leverage`, `trading_mode`, `take_profit`, `stop_loss`, `position_size_percentage`, `daily_profit_target`, `daily_loss_limit`, `api_key`, `api_secret`, `use_testnet`, `use_real_trading`.
    *   `/trades`: Menampilkan histori beberapa trading terakhir (aktif dan selesai).
    *   `/stats`: Menampilkan statistik trading harian (total trade, win/loss, PnL %, PnL USDT).
    *   `/balance`: Menampilkan saldo akun Binance Futures Anda (total, tersedia, PnL belum terealisasi).
    *   `/positions`: Menampilkan semua posisi terbuka saat ini di Binance Futures.
    *   `/indicators [simbol]`: Menampilkan nilai indikator teknikal terbaru untuk simbol tertentu (misal: `/indicators BTCUSDT`).

    **Perintah Trading:**
    *   `/starttrade`: Memulai proses trading otomatis. Anda akan diminta memilih mode trading (Safe, Standard, Aggressive) atau menggunakan mode yang sudah dikonfigurasi.
    *   `/stoptrade`: Menghentikan proses trading otomatis. Bot tidak akan membuka posisi baru, tetapi posisi yang sudah terbuka akan tetap dikelola (TP/SL).
    *   `/closeall`: Menutup semua posisi terbuka saat ini di Binance Futures menggunakan order MARKET (gunakan dengan hati-hati).

    **Perintah Pengaturan Lanjutan:**
    *   `/setleverage [nilai]`: Mengatur leverage default yang akan digunakan bot (misal: `/setleverage 10`).
    *   `/setmode [mode]`: Mengatur mode trading (`safe`, `standard`, `aggressive`). Ini akan menerapkan parameter TP, SL, leverage, dll., dari mode tersebut.
    *   `/addpair [simbol]`: Menambahkan pasangan trading ke daftar yang dipantau bot (misal: `/addpair ADAUSDT`).
    *   `/removepair [simbol]`: Menghapus pasangan trading dari daftar.
    *   `/setprofit [target_profit] [loss_limit]`: Mengatur target profit harian (%) dan batas kerugian harian (%) (misal: `/setprofit 5 3` untuk target 5% dan batas rugi 3%).

    **Perintah Trading Riil & Testnet:**
    *   `/enablereal`: Mengaktifkan trading riil menggunakan API Binance. **PERHATIAN: Ini akan menggunakan dana sungguhan! Pastikan API Key Anda benar dan Anda memahami risikonya.**
    *   `/disablereal`: Menonaktifkan trading riil. Bot akan kembali beroperasi dalam mode simulasi (tidak ada order riil yang ditempatkan).
    *   `/toggletestnet`: Beralih antara penggunaan API Binance Testnet (untuk pengujian) dan API Produksi/Live.
    *   `/testapi`: Menguji koneksi ke API Binance Futures menggunakan kredensial yang dikonfigurasi dan melaporkan statusnya.

## Struktur Bot

*   `BinanceFuturesAPI`: Kelas yang bertanggung jawab untuk semua interaksi dengan API Binance Futures (mendapatkan data, menempatkan order, dll.).
*   `TechnicalAnalysis`: Kelas yang menghitung berbagai indikator teknikal (RSI, EMA, Bollinger Bands) menggunakan `pandas_ta` dari data klines.
*   `TradingBot`: Kelas inti yang berisi logika trading, manajemen status (aktif/berhenti), pemrosesan sinyal, penempatan order melalui `BinanceFuturesAPI`, dan pemantauan trading.
*   `TelegramBotHandler`: Kelas yang menangani semua interaksi dengan pengguna melalui Telegram, memproses perintah, dan mengirimkan notifikasi.
*   `main()`: Fungsi utama untuk menginisialisasi semua komponen bot dan menjalankan loop Telegram.

## Catatan Penting & Peringatan Risiko

*   **RISIKO TINGGI:** Trading Cryptocurrency Futures sangat spekulatif dan memiliki tingkat risiko yang tinggi. Anda bisa kehilangan seluruh modal Anda. Bot ini adalah alat dan tidak menjamin keuntungan. Gunakan dengan risiko Anda sendiri.
*   **BUKAN NASIHAT KEUANGAN:** Informasi dan alat yang disediakan oleh bot ini adalah untuk tujuan edukasi dan otomatisasi saja, dan bukan merupakan nasihat keuangan.
*   **KEAMANAN API KEY:** Jaga kerahasiaan API Key dan Secret Key Anda. Jangan pernah membagikannya atau menyimpannya di repositori publik jika Anda melakukan fork. Pertimbangkan untuk menggunakan variabel lingkungan atau file konfigurasi terpisah yang tidak di-commit ke git.
*   **UJI COBA DI TESTNET:** Sebelum menggunakan dana riil, lakukan pengujian ekstensif di **Testnet** Binance untuk memahami perilaku bot dan menyesuaikan parameter strategi Anda.
*   **PANTAU SECARA AKTIF:** Meskipun bot ini dirancang untuk otomatisasi, penting untuk memantau kinerjanya secara berkala, terutama saat menggunakan dana riil.
*   **PENGEMBANGAN LEBIH LANJUT:** Skrip ini menyediakan dasar yang fungsional. Anda didorong untuk memodifikasi, meningkatkan, dan menyesuaikannya dengan strategi dan kebutuhan manajemen risiko Anda sendiri.

## Lisensi

Skrip ini disediakan "SEBAGAIMANA ADANYA" tanpa jaminan apa pun, tersurat maupun tersirat. Pengguna bertanggung jawab penuh atas penggunaan skrip ini dan segala konsekuensi finansial atau lainnya yang mungkin timbul.
