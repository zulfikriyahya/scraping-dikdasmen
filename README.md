# SCRAPER DATA SEKOLAH KEMENDIKBUDDASMEN

Proyek ini bertujuan untuk melakukan scraping data sekolah dari situs resmi Direktorat Jenderal Pendidikan Dasar dan Menengah (Dikdasmen) Kemendikbud RI. Data yang diambil meliputi informasi lengkap sekolah termasuk data akreditasi dan referensi dari dua sumber:
- **Data Referensi**: [https://sekolah.data.kemendikdasmen.go.id](https://sekolah.data.kemendikdasmen.go.id)

---

![Screenshoot](./screenshoot.png)

---

## Daftar Isi
- [Fitur Utama](#fitur-utama)
- [Data yang Dikumpulkan](#data-yang-dikumpulkan)
- [Instalasi dan Setup](#instalasi-dan-setup)
- [Cara Penggunaan](#cara-penggunaan)
- [Fitur Resume/Checkpoint](#fitur-resumecheckpoint)
- [Struktur Output](#struktur-output)
- [Tips dan Troubleshooting](#tips-dan-troubleshooting)
- [Catatan Penting](#catatan-penting)

---

## Fitur Utama

- **Scraping Komprehensif**: Mengambil data dari ~560,000+ sekolah di seluruh Indonesia
- **Dual Source Data**: Mengumpulkan data dari dua website resmi Kemendikbud
- **Resume/Checkpoint System**: Dapat melanjutkan proses scraping yang terinterupsi
- **Progress Tracking**: Menampilkan progress real-time dengan estimasi waktu
- **Auto-Save**: Menyimpan checkpoint setiap halaman dan backup setiap 100 halaman
- **Excel Output**: Hasil disimpan dalam format Excel (.xlsx) dengan dua sheet terpisah
- **Error Handling**: Robust error handling untuk koneksi tidak stabil

---

## Data yang Dikumpulkan

### Sheet 1: Data Akreditasi
- NPSN (Nomor Pokok Sekolah Nasional)
- Nama Sekolah
- 8 Standar Nasional Pendidikan:
  - Standar Isi
  - Standar Proses
  - Standar Kelulusan
  - Standar Tenaga Pendidik
  - Standar Sarana Prasarana
  - Standar Pengelolaan
  - Standar Pembiayaan
  - Standar Penilaian
- Tahun Akreditasi
- Nilai Akhir
- Status Akreditasi (A/B/C/TT)
- Link Sertifikat Akreditasi

### Sheet 2: Data Referensi
- **Identitas**: NPSN, Nama, Alamat Lengkap
- **Lokasi**: Desa/Kelurahan, Kecamatan, Kabupaten, Provinsi
- **Status**: Status Sekolah, Bentuk Pendidikan, Jenjang Pendidikan
- **Kelembagaan**: Kementerian Pembina, Naungan, NPYP
- **Legalitas**: 
  - No & Tanggal SK Pendirian
  - No & Tanggal SK Operasional
  - Link File SK Operasional
- **Akreditasi**: Status dan Link Sertifikat
- **Fasilitas**: Luas Tanah, Akses Internet, Sumber Listrik
- **Kontak**: Telepon, Fax, Email, Website
- **Koordinat**: Lintang dan Bujur (untuk mapping)
- **Operator**: Nama operator data sekolah

---

## Instalasi dan Setup

### Prasyarat
- Python 3.7 atau lebih tinggi
- Koneksi internet yang stabil
- Minimal 1GB ruang penyimpanan kosong

### Langkah Instalasi

1. **Clone repositori**:
   ```bash
   git clone https://github.com/zulfikriyahya/scraping-dikdasmen.git
   cd scraping-dikdasmen
   ```

2. **Buat virtual environment** (opsional tapi direkomendasikan):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # atau
   venv\Scripts\activate     # Windows
   ```

3. **Instal dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

### Dependensi yang Dibutuhkan
```
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
openpyxl>=3.0.10
```

---

## Cara Penggunaan

### Menjalankan Scraper

```bash
python main.py
```

### Flow Program

1. **Cek Checkpoint**: Program akan mengecek apakah ada proses scraping sebelumnya yang terinterupsi
   
2. **Resume atau Mulai Baru**: 
   - Jika checkpoint ditemukan, Anda dapat memilih untuk melanjutkan atau mulai dari awal
   - Jika tidak ada checkpoint, program akan mulai scraping baru

3. **Konfirmasi**: Program akan menampilkan informasi total sekolah dan estimasi waktu

4. **Proses Scraping**: 
   - Scraping berjalan otomatis dengan progress tracking
   - Data disimpan setiap halaman selesai
   - Backup dibuat setiap 100 halaman

5. **Selesai**: File Excel final akan disimpan dengan timestamp

### Contoh Output Terminal

```
======================================================================
  SCRAPING SEMUA DATA SEKOLAH KEMENDIKDASMEN
======================================================================

 Mengambil informasi total sekolah...

======================================================================
 Total Sekolah    : 560,228
 Total Halaman    : 140,057
 Mulai dari       : Halaman 1
  Estimasi waktu   : 467.0 jam
======================================================================

  Tekan ENTER untuk mulai scraping...

======================================================================
 HALAMAN 1/140,057 | Progress: 0.00%
======================================================================

[1/4] Sekolah #1/560,228
     ETA: 466.9 jam | Kecepatan: 3600 sekolah/jam
    https://sekolah.data.kemendikdasmen.go.id/index.php/Chome/profil/xxxxx
    Akreditasi: 12345678 - SD NEGERI 1 JAKARTA
    Referensi: SD NEGERI 1 JAKARTA

 Checkpoint disimpan: Halaman 1, Sekolah 4/560,228
```

---

## 🔄 Fitur Resume/Checkpoint

### Cara Kerja

Scraper menyimpan progress secara otomatis dalam dua file:
- `scraper_checkpoint.json`: Menyimpan halaman terakhir dan jumlah sekolah yang telah diproses
- `temp_data.json`: Menyimpan data sementara yang telah di-scrape

### Melanjutkan Scraping yang Terinterupsi

1. Jalankan kembali program:
   ```bash
   python main.py
   ```

2. Program akan mendeteksi checkpoint dan menampilkan:
   ```
   CHECKPOINT DITEMUKAN!
   ======================================================================
      Halaman terakhir  : 50
      Progress sekolah  : 200/560,228
      Persentase        : 0.04%
      Waktu tersimpan   : 2024-01-15 14:30:45
   ======================================================================
   
   Lanjutkan dari checkpoint? (y/n):
   ```

3. Ketik `y` untuk melanjutkan atau `n` untuk mulai dari awal

### Menghentikan Scraping dengan Aman

- Tekan `Ctrl + C` kapan saja
- Program akan menyimpan progress terakhir
- Data yang telah di-scrape akan tetap tersimpan
- Anda dapat melanjutkan nanti dari checkpoint

---

## Struktur Output

### File yang Dihasilkan

1. **File Excel Utama**: `data_sekolah_final_YYYYMMDD_HHMMSS.xlsx`
   - Sheet 1: Data Akreditasi
   - Sheet 2: Data Referensi

2. **File Backup**: `data_sekolah_backup_page_XXX.xlsx`
   - Dibuat setiap 100 halaman
   - Berguna jika proses terinterupsi

3. **File Checkpoint**: 
   - `scraper_checkpoint.json`: Info progress
   - `temp_data.json`: Data sementara

### Lokasi File
Semua file disimpan di direktori yang sama dengan script Python.

---

## Tips dan Troubleshooting

### Tips Penggunaan

1. **Koneksi Internet**: 
   - Pastikan koneksi stabil untuk hasil optimal
   - Gunakan koneksi kabel jika memungkinkan

2. **Waktu Eksekusi**:
   - Scraping penuh membutuhkan ~20 hari non-stop
   - Gunakan fitur resume untuk scraping bertahap
   - Pertimbangkan menjalankan di server atau VPS

3. **Resource Management**:
   - Script menggunakan delay 1-1.5 detik antar request
   - Tidak membebani server target
   - Memory usage relatif rendah (~200MB)

4. **Backup Data**:
   - File backup otomatis dibuat setiap 100 halaman
   - Simpan file backup di lokasi terpisah untuk keamanan

### Troubleshooting

#### Program Berhenti Tiba-tiba
```bash
# Jalankan kembali, program akan otomatis resume
python main.py
# Pilih 'y' saat ditanya untuk lanjutkan dari checkpoint
```

#### Error "Connection Timeout"
- Cek koneksi internet
- Program akan otomatis retry
- Jika error berulang >10x, program akan berhenti otomatis

#### Error "No module named 'requests'"
```bash
pip install -r requirements.txt
```

#### File Excel Tidak Bisa Dibuka
- Pastikan tidak ada program lain yang membuka file
- Cek apakah Excel terbaru terinstal
- Gunakan LibreOffice jika Excel bermasalah

#### Progress Sangat Lambat
- Normal, estimasi 3600 sekolah/jam
- Delay sengaja ditambahkan untuk menghormati server
- Pertimbangkan running di server dengan koneksi lebih baik

---

## Catatan Penting

### Legal dan Etika

1. **Data Publik**: 
   - Semua data yang di-scrape adalah data publik yang tersedia di website resmi Kemendikbud
   - Gunakan data sesuai peraturan dan etika yang berlaku

2. **Rate Limiting**: 
   - Script menggunakan delay antar request untuk tidak membebani server
   - Jangan modifikasi delay agar server tidak overload

3. **Terms of Service**: 
   - Pastikan scraping tidak melanggar ToS website
   - Gunakan untuk keperluan riset, pendidikan, atau analisis data

### Batasan Teknis

1. **Struktur HTML**: 
   - Perubahan struktur website dapat mempengaruhi hasil scraping
   - Update script jika terjadi perubahan struktur

2. **Data Kosong**: 
   - Beberapa sekolah mungkin tidak memiliki data lengkap
   - Field kosong akan muncul sebagai string kosong di Excel

3. **Waktu Eksekusi**: 
   - Total waktu ~20 hari untuk scraping penuh
   - Pertimbangkan scraping bertahap atau filter tertentu

### Penggunaan Bertanggung Jawab

- **Jangan** menjalankan multiple instances secara bersamaan
- **Jangan** mengurangi delay antar request
- **Lakukan** scraping di luar jam sibuk jika memungkinkan
- **Gunakan** data untuk keperluan positif dan legal

---

## Kontribusi

Kontribusi sangat diterima! Silakan:
1. Fork repositori ini
2. Buat branch baru (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

---

## Lisensi

Proyek ini dibuat untuk keperluan edukasi dan riset. Pastikan penggunaan data sesuai dengan peraturan yang berlaku.

---

## Kontak

Jika ada pertanyaan atau masalah, silakan buat issue di GitHub repository atau hubungi maintainer.

---

## Acknowledgments

- Data bersumber dari [Kemendikbud Ristek](https://www.kemdikbud.go.id/)
- [Dapodik](https://dapo.kemdikbud.go.id/) untuk sistem data pendidikan

---

**Happy Scraping! Gunakan dengan Bijak!**
