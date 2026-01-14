"""
SEKOLAH SCRAPER - PARALLEL VERSION
==================================
Scraping data sekolah dari sekolah.data.kemendikdasmen.go.id
Field: NPSN, Nama, Alamat, Status
Teknik: Direct pagination dengan parallel processing (multiple tabs)
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
    """Scraper untuk data sekolah dengan parallel processing"""

    def __init__(self, max_workers=10, headless=True, debug=False):
        self.max_workers = max_workers
        self.headless = headless
        self.debug = debug
        
        self.base_url = "https://sekolah.data.kemendikdasmen.go.id"
        self.checkpoint_file = "checkpoint.json"
        self.temp_data_file = "temp_data.json"
        self.batch_size = 100
        self.batch_counter = 0
        
        # Pagination parameters
        self.page_size = 48
        self.total_schools = 549894
        self.total_pages = 11457  # 0-11456 (11457 pages total)
        
        self.lock = threading.Lock()
        self.all_data = []
        self.failed_pages = []
        self.processed_pages = 0
        
        print("\n" + "="*70)
        print("  SEKOLAH SCRAPER - PARALLEL VERSION")
        print("="*70)
        print(f"  Workers: {max_workers} (concurrent tabs)")
        print(f"  Headless: {headless}")
        print(f"  Batch Size: {self.batch_size}")
        print(f"  Total Sekolah: {self.total_schools:,}")
        print(f"  Total Pages: {self.total_pages:,} (size={self.page_size})")
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
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            
            # Performance optimization
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(30)
            
            return driver
        
        except Exception as e:
            print(f"[ERROR] Gagal membuat driver: {e}")
            return None

    def extract_school_list(self, driver):
        """Ekstrak daftar sekolah dari halaman"""
        try:
            time.sleep(2)
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
            if self.debug:
                print(f"  Ekstrak list error: {e}")
            return []

    def scrape_page(self, page_num):
        """Scrape satu halaman menggunakan URL pagination langsung"""
        driver = None
        try:
            driver = self.create_driver()
            if not driver:
                return {'page': page_num, 'schools': [], 'success': False}
            
            # Gunakan URL dengan parameter page dan size langsung
            url = f"{self.base_url}/sekolah?page={page_num}&size={self.page_size}"
            
            driver.get(url)
            
            # Tunggu artikel muncul
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except Exception as e:
                if self.debug:
                    print(f"  Page {page_num}: Timeout menunggu artikel")
                return {'page': page_num, 'schools': [], 'success': False}
            
            # Ekstrak schools
            schools = self.extract_school_list(driver)
            
            return {'page': page_num, 'schools': schools, 'success': True}
        
        except Exception as e:
            if self.debug:
                print(f"  Page {page_num} error: {e}")
            return {'page': page_num, 'schools': [], 'success': False}
        finally:
            if driver:
                driver.quit()

    def process_schools(self, schools):
        """Proses schools (bisa diperluas untuk detail scraping)"""
        return schools

    def scrape_all(self, max_pages=None):
        """Fungsi utama scraping dengan parallel processing"""
        start_time = time.time()
        
        # Load checkpoint
        checkpoint = self.load_checkpoint()
        start_page = 0
        
        if checkpoint:
            resume = input(f"\nResume dari halaman {checkpoint['last_page']}? (y/n): ").strip().lower()
            if resume == 'y':
                start_page = checkpoint['last_page'] + 1
                self.all_data = self.load_temp_data()
                print(f"Resume dengan {len(self.all_data)} data existing\n")
        
        print("Memulai proses scraping parallel...\n")
        
        # Tentukan end page
        if max_pages:
            end_page = min(start_page + max_pages, self.total_pages)
        else:
            end_page = self.total_pages
        
        total_pages_to_scrape = end_page - start_page
        
        print(f"Scraping dari page {start_page} sampai {end_page-1}")
        print(f"Total: {total_pages_to_scrape:,} pages dengan {self.max_workers} workers parallel\n")
        
        try:
            # Parallel processing dengan ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit semua tasks
                future_to_page = {
                    executor.submit(self.scrape_page, page): page 
                    for page in range(start_page, end_page)
                }
                
                # Process hasil secara real-time
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    
                    try:
                        result = future.result()
                        
                        if result['success'] and result['schools']:
                            schools = result['schools']
                            processed = self.process_schools(schools)
                            
                            with self.lock:
                                self.all_data.extend(processed)
                                self.processed_pages += 1
                                
                                # Simpan batch
                                if len(self.all_data) % self.batch_size == 0:
                                    self.save_batch()
                            
                            # Progress
                            elapsed = time.time() - start_time
                            rate = len(self.all_data) / elapsed if elapsed > 0 else 0
                            progress = (self.processed_pages / total_pages_to_scrape) * 100
                            
                            print(f"[PAGE {page_num}] {len(schools)} sekolah | "
                                  f"Progress: {progress:.1f}% | "
                                  f"Total: {len(self.all_data):,} | "
                                  f"Rate: {rate:.1f}/s")
                        else:
                            with self.lock:
                                self.failed_pages.append(page_num)
                            if self.debug:
                                print(f"[PAGE {page_num}] FAILED")
                        
                        # Simpan checkpoint setiap 50 pages
                        if self.processed_pages % 50 == 0:
                            self.save_checkpoint(page_num, len(self.all_data))
                            self.save_temp_data(self.all_data)
                    
                    except Exception as e:
                        print(f"[ERROR] Page {page_num}: {e}")
                        with self.lock:
                            self.failed_pages.append(page_num)
        
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Dihentikan oleh user")
        
        # Retry failed pages
        if self.failed_pages:
            print(f"\n{'='*70}")
            print(f"[RETRY] Mencoba ulang {len(self.failed_pages)} pages yang gagal...")
            print(f"{'='*70}\n")
            
            retry_count = 0
            for page in self.failed_pages[:]:
                try:
                    result = self.scrape_page(page)
                    if result['success'] and result['schools']:
                        with self.lock:
                            self.all_data.extend(result['schools'])
                            self.failed_pages.remove(page)
                        retry_count += 1
                        print(f"[RETRY SUCCESS] Page {page}: {len(result['schools'])} sekolah")
                except:
                    pass
            
            print(f"\nRetry berhasil untuk {retry_count}/{len(self.failed_pages)} pages\n")
        
        # Simpan data final
        if self.all_data:
            filename = self.save_to_csv(self.all_data)
            
            elapsed = time.time() - start_time
            print(f"\n{'='*70}")
            print(f"[SELESAI]")
            print(f"  Total sekolah: {len(self.all_data):,}")
            print(f"  Pages berhasil: {self.processed_pages:,}/{total_pages_to_scrape:,}")
            print(f"  Pages gagal: {len(self.failed_pages)}")
            print(f"  Waktu: {elapsed/60:.2f} menit ({elapsed:.0f} detik)")
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
            end_idx = min(start_idx + self.batch_size - 1, len(self.all_data))
            
            batch_data = self.all_data[start_idx-1:end_idx]
            
            if batch_data:
                filename = f"batch_{start_idx}-{end_idx}.csv"
                df = pd.DataFrame(batch_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                if self.debug:
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
            
            # Remove duplicates berdasarkan NPSN
            df = df.drop_duplicates(subset=['npsn'], keep='first')
            
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
                    'processed_pages': self.processed_pages,
                    'total_count': self.total_schools,
                    'failed_pages': self.failed_pages,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)

    def load_checkpoint(self):
        """Load checkpoint"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    if 'failed_pages' in checkpoint:
                        self.failed_pages = checkpoint['failed_pages']
                    return checkpoint
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
    print("  SEKOLAH SCRAPER - PARALLEL VERSION")
    print("="*70)
    
    test_mode = input("\nMode test (scrape 10 halaman saja)? (y/n): ").strip().lower()
    max_pages = 10 if test_mode == 'y' else None
    
    workers = input("Jumlah parallel workers (recommended 10-20, default=10): ").strip()
    workers = int(workers) if workers.isdigit() else 10
    
    headless = input("Gunakan headless browser? (y/n, default=y): ").strip().lower()
    headless = headless != 'n'
    
    debug = input("Aktifkan debug mode? (y/n, default=n): ").strip().lower()
    debug = debug == 'y'
    
    print("\n" + "="*70)
    print("MEMULAI SCRAPER PARALLEL...")
    print(f"WARNING: Akan membuka {workers} browser instances secara bersamaan!")
    print("="*70 + "\n")
    
    confirm = input("Lanjutkan? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Dibatalkan.")
        exit()
    
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