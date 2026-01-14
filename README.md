# SCRAPER DATA SEKOLAH KEMENDIKBUDDASMEN

Aplikasi scraper berbasis Python untuk mengumpulkan data sekolah secara komprehensif dari portal resmi Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi (sekolah.data.kemendikbuddasmen.go.id).

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Data yang Dikumpulkan](#data-yang-dikumpulkan)
- [Instalasi dan Setup](#instalasi-dan-setup)
- [Cara Penggunaan](#cara-penggunaan)
- [Fitur Resume/Checkpoint](#fitur-resumecheckpoint)
- [Struktur Output](#struktur-output)
- [Tips dan Troubleshooting](#tips-dan-troubleshooting)
- [Catatan Penting](#catatan-penting)
- [Kontribusi](#kontribusi)
- [Lisensi](#lisensi)
- [Kontak](#kontak)
- [Acknowledgments](#acknowledgments)

## Fitur Utama

### 1. Ekstraksi Data Komprehensif

- Mengumpulkan 40+ field data dari setiap profil sekolah
- Ekstraksi otomatis dari berbagai section: profil umum, statistik, kurikulum, pembelajaran, dan alamat
- Penanganan data kosong dengan placeholder '-' untuk konsistensi data

### 2. Multi-Threading

- Scraping paralel menggunakan ThreadPoolExecutor
- Konfigurasi jumlah worker sesuai kebutuhan (default: 2 workers)
- Optimasi kecepatan tanpa membebani server target

### 3. Sistem Checkpoint & Resume

- Penyimpanan progress otomatis setiap halaman
- Kemampuan melanjutkan scraping dari titik terakhir jika terhenti
- File checkpoint dalam format JSON dengan timestamp

### 4. Backup Data Bertahap

- Penyimpanan batch otomatis setiap 50 data
- File backup terpisah: `batch_1-50.csv`, `batch_51-100.csv`, dst
- Mitigasi kehilangan data pada proses panjang

### 5. Headless Browser Support

- Mode headless untuk efisiensi resource
- Opsi tampilan browser untuk debugging
- Anti-detection mechanism untuk stabilitas scraping

### 6. Debug Mode

- Logging detail untuk troubleshooting
- Pelacakan error per elemen
- Monitoring proses scraping real-time

## Data yang Dikumpulkan

### A. Identitas dan Profil Umum

- [x] NPSN (Nomor Pokok Sekolah Nasional)
- [x] Nama Sekolah
- [x] Alamat Sekolah
- [ ] Alamat Jalan (lengkap)
- [ ] URL Profil Sekolah
- [ ] URL SK Operasional

### B. Informasi Administratif

- [ ] Akreditasi
- [x] Status Sekolah (Negeri/Swasta)
- [ ] Bentuk Pendidikan
- [ ] Yayasan (untuk sekolah swasta)
- [ ] Kepala Sekolah
- [ ] Operator

### C. Kontak

- [ ] Telepon
- [ ] Email
- [ ] Website Sekolah

### D. Statistik Sekolah

- [ ] Jumlah Guru
- [ ] Jumlah Siswa Laki- [ ]laki
- [ ] Jumlah Siswa Perempuan
- [ ] Jumlah Rombongan Belajar
- [ ] Daya Tampung Siswa
- [ ] Jumlah Ruang Kelas
- [ ] Jumlah Laboratorium
- [ ] Jumlah Perpustakaan

### E. Kurikulum dan Utilitas

- [ ] Kurikulum yang Digunakan
- [ ] Penyelenggaraan
- [ ] Akses Internet
- [ ] Sumber Listrik
- [ ] Daya Listrik
- [ ] Luas Tanah

### F. Proses Pembelajaran

- [ ] Rasio Siswa per Rombongan Belajar
- [ ] Rasio Rombongan Belajar per Ruang Kelas
- [ ] Rasio Siswa per Guru
- [ ] Persentase Guru Berkualifikasi
- [ ] Persentase Guru Bersertifikat
- [ ] Persentase Guru PNS
- [ ] Persentase Ruang Kelas Layak

### G. Lokasi

- [ ] Koordinat Lintang
- [ ] Koordinat Bujur
- [ ] Link Google Maps

## Instalasi dan Setup

### Persyaratan Sistem

- Python 3.13.5 atau lebih tinggi
- Google Chrome Browser (versi terbaru)
- ChromeDriver (otomatis dikelola oleh Selenium)
- Koneksi internet stabil

### Langkah Instalasi

1. **Clone atau Download Repository**

   ```bash
   git clone https://github.com/zulfikriyahya/scraping-dikdasmen.git
   cd scraping-dikdasmen
   ```

2. **Buat Virtual Environment (Opsional tapi Disarankan)**

   ```bash
   python3 -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   **File requirements.txt:**

   ```
   selenium>=4.15.0
   beautifulsoup4>=4.12.0
   openpyxl>=3.1.0
   requests>=2.31.0
   pandas>=2.0.0
   ```

4. **Verifikasi Instalasi Chrome**
   Pastikan Google Chrome terinstal di sistem Anda. Selenium akan otomatis mendownload ChromeDriver yang sesuai.

## Cara Penggunaan

### Mode Dasar

1. **Jalankan Script**

   ```bash
   python3 stable-lite.py
   ```

2. **Konfigurasi Interaktif**
   Script akan menampilkan prompt untuk konfigurasi:

   ```
   Mode test (3 halaman)? (y/n): n
   Jumlah workers (default=2): 3
   Headless browser? (y/n, default=y): y
   Debug mode? (y/n, default=n): n
   ```

### Parameter Konfigurasi

| Parameter | Deskripsi             | Nilai Default | Rekomendasi               |
| --------- | --------------------- | ------------- | ------------------------- |
| Mode Test | Scrape 3 halaman saja | n             | Gunakan 'y' untuk testing |
| Workers   | Jumlah thread paralel | 2             | 2-4 untuk koneksi stabil  |
| Headless  | Browser tanpa GUI     | y             | 'y' untuk produksi        |
| Debug     | Logging detail        | n             | 'y' untuk troubleshooting |

### Mode Produksi

```bash
# Scraping penuh dengan konfigurasi optimal
python stable-lite.py
# Input: n, 3, y, n
```

### Mode Testing

```bash
# Testing dengan 3 halaman dan tampilan browser
python stable-lite.py
# Input: y, 2, n, y
```

### Penggunaan Programmatic

```python
from scraper import SekolahScraperSelenium

# Inisialisasi scraper
scraper = SekolahScraperSelenium(
    max_workers=3,
    headless=True,
    debug=False
)

# Jalankan scraping (max 5 halaman)
data = scraper.scrape_all(max_pages=5)

# Akses data
print(f"Total data: {len(data)}")
```

## Fitur Resume/Checkpoint

### Cara Kerja Checkpoint

Aplikasi secara otomatis menyimpan progress setiap halaman dalam dua file:

1. **checkpoint.json** - Informasi progress

   ```json
   {
     "last_page": 5,
     "processed_count": 250,
     "total_count": 0,
     "timestamp": "2026-01-13T22:53:44.187084"
   }
   ```

2. **temp_data.json** - Data sementara yang sudah terkumpul

### Melanjutkan Scraping yang Terhenti

Jika scraping terhenti (error, keyboard interrupt, dll):

1. Jalankan ulang script
2. Sistem akan mendeteksi checkpoint
3. Konfirmasi resume:
   ```
   Lanjutkan dari halaman 5? (y/n): y
   ```
4. Scraping berlanjut dari halaman terakhir

### Reset Progress

Untuk memulai dari awal, hapus file checkpoint:

```bash
rm checkpoint.json temp_data.json
```

## Struktur Output

### File Output Utama

**data_sekolah_YYYYMMDD_HHMMSS.csv**

- Format: CSV dengan encoding UTF-8-SIG (support Excel)
- Delimiter: koma (,)
- Header: baris pertama
- Data kosong: diisi dengan '-'

### File Backup Batch

**batch_1-50.csv, batch_51-100.csv, ...**

- Dibuat otomatis setiap 50 data
- Format sama dengan file utama
- Berguna untuk recovery parsial

### Contoh Struktur Data

```csv
npsn,nama_sekolah,alamat_sekolah,status_sekolah,...
P9999999,PKBM SUKAMAJU MANDIRI,Jl. Contoh No. 123,Swasta,...
20123456,SDN 01 JAKARTA,Jl. Merdeka No. 45,Negeri,...
```

### Import ke Excel

1. Buka Excel
2. File → Open → Pilih file CSV
3. Data akan otomatis terformat dengan benar (encoding UTF-8-SIG)

### Import ke Database

```python
import pandas as pd
import sqlite3

# Baca CSV
df = pd.read_csv('data_sekolah_20260113_220000.csv')

# Simpan ke SQLite
conn = sqlite3.connect('sekolah.db')
df.to_sql('sekolah', conn, if_exists='replace', index=False)
conn.close()
```

## Tips dan Troubleshooting

### Optimasi Kecepatan

1. **Sesuaikan Jumlah Workers**

   - Koneksi cepat: 3-4 workers
   - Koneksi lambat: 1-2 workers
   - Over-threading dapat menyebabkan timeout

2. **Gunakan Headless Mode**

   - Hemat resource RAM dan CPU
   - Lebih stabil untuk scraping panjang

3. **Scraping pada Jam Off-Peak**
   - Server lebih responsif pada malam hari
   - Mengurangi kemungkinan rate limiting

### Troubleshooting Umum

#### Error: "ChromeDriver not found"

**Solusi:**

```bash
# Update Selenium (akan auto-download ChromeDriver)
pip install --upgrade selenium
```

#### Error: Timeout atau Element Not Found

**Solusi:**

- Tingkatkan delay di `time.sleep()`
- Kurangi jumlah workers
- Aktifkan debug mode untuk analisis

#### Data Banyak yang Kosong ('-')

**Penyebab:**

- Struktur HTML berubah
- Data memang tidak tersedia di website

**Solusi:**

- Periksa sumber data manual
- Sesuaikan selector di kode jika struktur berubah

#### Script Berhenti Mendadak

**Solusi:**

- Cek koneksi internet
- Gunakan fitur resume/checkpoint
- Periksa batch backup terakhir

### Monitoring Progress

Aplikasi menampilkan progress real-time:

```
[HALAMAN 5] Scraping...
  Ditemukan 50 sekolah
  Halaman 5 selesai | Total: 250 | 2.5/s
```

Informasi yang ditampilkan:

- Halaman saat ini
- Jumlah sekolah per halaman
- Total data terkumpul
- Kecepatan scraping (data/detik)

## Catatan Penting

### Etika Scraping

1. **Respect robots.txt**

   - Scraper ini menggunakan delay antar request
   - Tidak membebani server target

2. **Rate Limiting**

   - Delay 2-5 detik antar halaman
   - Tidak melakukan request bersamaan berlebihan

3. **Penggunaan Data**
   - Data untuk keperluan riset dan analisis
   - Hormati privasi dan kebijakan penggunaan data

### Batasan

1. **Struktur Website**

   - Scraper bergantung pada struktur HTML saat ini
   - Update website dapat memerlukan penyesuaian kode

2. **Data Dinamis**

   - Beberapa data mungkin dimuat via JavaScript
   - Selenium menangani sebagian besar kasus

3. **Kelengkapan Data**
   - Tidak semua sekolah memiliki data lengkap
   - Field kosong diisi dengan '-'

### Maintenance

Periksa dan update secara berkala:

- Dependency Python (khususnya Selenium)
- Struktur selector jika website berubah
- ChromeDriver compatibility

## Kontribusi

Kontribusi sangat diterima untuk pengembangan project ini:

### Cara Berkontribusi

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -m 'Menambah fitur baru'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

### Area Kontribusi

- Peningkatan efisiensi scraping
- Penambahan field data baru
- Perbaikan bug dan error handling
- Dokumentasi dan tutorial
- Testing dan quality assurance

### Code Style

- Gunakan Bahasa Indonesia untuk komentar
- Ikuti PEP 8 untuk Python code style
- Tambahkan docstring untuk fungsi baru
- Update README untuk fitur baru

## Lisensi

Project ini dilisensikan di bawah [MIT License](LICENSE).

## Kontak

### Pelaporan Bug

Gunakan GitHub Issues untuk melaporkan bug atau meminta fitur baru.

### Diskusi

Untuk diskusi umum dan pertanyaan, gunakan GitHub Discussions.

### Support

- Email: support@example.com
- Dokumentasi: [Wiki Project](https://github.com/zulfikriyahya/scraping-dikdasmen/wiki)
- FAQ: [Frequently Asked Questions](https://github.com/zulfikriyahya/scraping-dikdasmen/wiki/FAQ)

## Acknowledgments

### Teknologi yang Digunakan

- **Selenium WebDriver** - Browser automation
- **BeautifulSoup4** - HTML parsing
- **Pandas** - Data manipulation
- **OpenPyXL** - Excel file handling

### Referensi

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

### Sumber Data

Data bersumber dari:

- Portal Data Sekolah Kemendikbuddasmen
- URL: https://sekolah.data.kemendikbuddasmen.go.id

### Disclaimer

Aplikasi ini dibuat untuk tujuan edukasi dan riset. Pengguna bertanggung jawab atas penggunaan data yang dikumpulkan sesuai dengan hukum dan regulasi yang berlaku.

---

**Versi:** 1.0.0  
**Terakhir Diperbarui:** Januari 2026  
**Status:** Aktif Dikembangkan

Untuk informasi lebih lanjut, silakan kunjungi [dokumentasi lengkap](https://github.com/zulfikriyahya/scraping-dikdasmen/wiki).
