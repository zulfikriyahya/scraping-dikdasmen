"""
SEKOLAH SCRAPER - Production Ready
===================================
Scraping data sekolah dari sekolah.data.kemendikdasmen.go.id
Field: NPSN, Nama, Alamat, Status
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class SekolahScraper:
    """Scraper untuk data sekolah"""

    def __init__(self, max_workers=2, headless=True, debug=False):
        self.max_workers = max_workers
        self.headless = headless
        self.debug = debug
        
        self.base_url = "https://sekolah.data.kemendikdasmen.go.id"
        self.checkpoint_file = "checkpoint.json"
        self.temp_data_file = "temp_data.json"
        self.batch_size = 50
        self.batch_counter = 0
        
        self.lock = threading.Lock()
        self.all_data = []
        
        print("\n" + "="*70)
        print("  SEKOLAH SCRAPER - PRODUCTION READY")
        print("="*70)
        print(f"  Workers: {max_workers}")
        print(f"  Headless: {headless}")
        print(f"  Batch Size: {self.batch_size}")
        print("="*70 + "\n")

    def create_driver(self):
        """Buat WebDriver instance"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        
        except Exception as e:
            print(f"[ERROR] Gagal membuat driver: {e}")
            return None

    def extract_school_list(self, driver):
        """Ekstrak daftar sekolah dari halaman"""
        try:
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            schools = []
            articles = soup.find_all('article')
            
            for article in articles:
                try:
                    # NPSN
                    npsn = ''
                    npsn_text = article.find(string=lambda x: x and 'NPSN' in str(x))
                    if npsn_text:
                        match = re.search(r'NPSN\s*:\s*(\w+)', str(npsn_text))
                        if match:
                            npsn = match.group(1).strip()
                    
                    # Nama Sekolah
                    nama = ''
                    nama_elem = article.find('h3')
                    if nama_elem:
                        nama = nama_elem.get_text(strip=True)
                    
                    # Status
                    status = ''
                    status_elem = article.find('div', class_=lambda x: x and 'text-orange-600' in str(x))
                    if not status_elem:
                        status_elem = article.find('div', class_=lambda x: x and 'font-semibold' in str(x))
                    if status_elem:
                        status = status_elem.get_text(strip=True)
                    
                    # Alamat
                    alamat = ''
                    alamat_elem = article.find('div', class_=lambda x: x and 'line-clamp' in str(x) and 'text-xs' in str(x))
                    if alamat_elem:
                        alamat = alamat_elem.get_text(strip=True)
                    
                    if npsn:
                        schools.append({
                            'npsn': npsn,
                            'nama_sekolah': nama if nama else '-',
                            'alamat_sekolah': alamat if alamat else '-',
                            'status_sekolah': status if status else '-'
                        })
                
                except Exception as e:
                    if self.debug:
                        print(f"    Parsing error: {e}")
                    continue
            
            return schools
        
        except Exception as e:
            print(f"  Ekstrak list error: {e}")
            return []

    def scrape_page(self, page_num):
        """Scrape satu halaman"""
        driver = self.create_driver()
        if not driver:
            return []
        
        try:
            url = f"{self.base_url}/sekolah"
            driver.get(url)
            time.sleep(5)
            
            # Navigate ke halaman yang diminta
            for i in range(1, page_num):
                try:
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.p-paginator-next:not(.p-disabled)"))
                    )
                    next_btn.click()
                    time.sleep(3)
                except:
                    print(f"  Tidak bisa navigasi ke halaman {page_num}")
                    return []
            
            # Ekstrak schools
            schools = self.extract_school_list(driver)
            
            return schools
        
        except Exception as e:
            print(f"  Page {page_num} error: {e}")
            return []
        finally:
            driver.quit()

    def process_schools(self, schools):
        """Proses schools (bisa diperluas untuk detail scraping)"""
        return schools

    def scrape_all(self, max_pages=None):
        """Fungsi utama scraping"""
        start_time = time.time()
        
        # Load checkpoint
        checkpoint = self.load_checkpoint()
        start_page = 1
        
        if checkpoint:
            resume = input(f"\nResume dari halaman {checkpoint['last_page']}? (y/n): ").strip().lower()
            if resume == 'y':
                start_page = checkpoint['last_page']
                self.all_data = self.load_temp_data()
                print(f"Resume dengan {len(self.all_data)} data existing\n")
        
        print("Memulai proses scraping...\n")
        
        page = start_page
        
        try:
            while True:
                if max_pages and page > max_pages:
                    break
                
                print(f"[HALAMAN {page}] Scraping...")
                
                # Scrape halaman
                schools = self.scrape_page(page)
                
                if not schools:
                    print(f"  Tidak ada sekolah ditemukan, berhenti")
                    break
                
                print(f"  Ditemukan {len(schools)} sekolah")
                
                # Process schools (bisa parallel jika perlu detail scraping)
                processed = self.process_schools(schools)
                
                with self.lock:
                    self.all_data.extend(processed)
                    
                    # Simpan batch
                    if len(self.all_data) % self.batch_size == 0:
                        self.save_batch()
                
                rate = len(self.all_data) / (time.time() - start_time)
                print(f"  Halaman {page} selesai | Total: {len(self.all_data):,} | Rate: {rate:.1f}/s\n")
                
                # Simpan checkpoint
                self.save_checkpoint(page, len(self.all_data))
                self.save_temp_data(self.all_data)
                
                page += 1
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Dihentikan oleh user")
        
        # Simpan data final
        if self.all_data:
            filename = self.save_to_csv(self.all_data)
            
            elapsed = time.time() - start_time
            print(f"\n{'='*70}")
            print(f"[SELESAI]")
            print(f"  Total sekolah: {len(self.all_data):,}")
            print(f"  Waktu: {elapsed/60:.2f} menit")
            print(f"  Rate: {len(self.all_data)/elapsed:.1f} sekolah/detik")
            print(f"  File: {filename}")
            print(f"{'='*70}\n")
            
            # Cleanup
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
            if os.path.exists(self.temp_data_file):
                os.remove(self.temp_data_file)
        else:
            print("\n[ERROR] Tidak ada data terkumpul!")
        
        return self.all_data

    def save_batch(self):
        """Simpan batch data"""
        try:
            start_idx = (self.batch_counter * self.batch_size) + 1
            end_idx = start_idx + self.batch_size - 1
            
            batch_data = self.all_data[start_idx-1:end_idx]
            
            if batch_data:
                filename = f"batch_{start_idx}-{end_idx}.csv"
                df = pd.DataFrame(batch_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"  Batch disimpan: {filename}")
                
                self.batch_counter += 1
        
        except Exception as e:
            if self.debug:
                print(f"  Batch save error: {e}")

    def save_to_csv(self, data):
        """Simpan ke CSV"""
        try:
            filename = f"data_sekolah_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            df = pd.DataFrame(data)
            
            # Urutan kolom sesuai requirements
            columns = ['npsn', 'nama_sekolah', 'alamat_sekolah', 'status_sekolah']
            df = df[columns]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            return filename
        
        except Exception as e:
            print(f"[ERROR] Gagal simpan CSV: {e}")
            return None

    def save_checkpoint(self, page, count):
        """Simpan checkpoint"""
        with self.lock:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_page': page,
                    'processed_count': count,
                    'total_count': 0,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)

    def load_checkpoint(self):
        """Load checkpoint"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    def save_temp_data(self, data):
        """Simpan data sementara"""
        with self.lock:
            try:
                with open(self.temp_data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                if self.debug:
                    print(f"  Temp save error: {e}")

    def load_temp_data(self):
        """Load data sementara"""
        if os.path.exists(self.temp_data_file):
            try:
                with open(self.temp_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SEKOLAH SCRAPER - PRODUCTION READY")
    print("="*70)
    
    test_mode = input("\nMode test (scrape 3 halaman saja)? (y/n): ").strip().lower()
    max_pages = 3 if test_mode == 'y' else None
    
    workers = input("Jumlah parallel workers (default=2): ").strip()
    workers = int(workers) if workers.isdigit() else 2
    
    headless = input("Gunakan headless browser? (y/n, default=y): ").strip().lower()
    headless = headless != 'n'
    
    debug = input("Aktifkan debug mode? (y/n, default=n): ").strip().lower()
    debug = debug == 'y'
    
    print("\n" + "="*70)
    print("MEMULAI SCRAPER...")
    print("="*70 + "\n")
    
    try:
        scraper = SekolahScraper(
            max_workers=workers,
            headless=headless,
            debug=debug
        )
        
        data = scraper.scrape_all(max_pages=max_pages)
    
    except KeyboardInterrupt:
        print("\n\n[EXIT] Program dihentikan oleh user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()