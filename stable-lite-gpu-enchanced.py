"""
SEKOLAH SCRAPER - ULTRA FAST VERSION WITH GPU
==============================================
Scraping data sekolah dari sekolah.data.kemendikdasmen.go.id
Field: NPSN, Nama, Alamat, Status
Teknik: Maximum parallel processing + GPU acceleration
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import multiprocessing
from queue import Queue
import asyncio


class SekolahScraperUltraFast:
    """Scraper ultra cepat dengan GPU support dan maximum parallelization"""

    def __init__(self, max_workers=50, headless=True, debug=False, use_gpu=True):
        self.max_workers = max_workers
        self.headless = headless
        self.debug = debug
        self.use_gpu = use_gpu
        
        self.base_url = "https://sekolah.data.kemendikdasmen.go.id"
        self.checkpoint_file = "checkpoint.json"
        self.temp_data_file = "temp_data.json"
        self.batch_size = 200
        self.batch_counter = 0
        
        # Pagination parameters
        self.page_size = 48
        self.total_schools = 549894
        self.total_pages = 11457  # 0-11456 (11457 pages total)
        
        self.lock = threading.Lock()
        self.all_data = []
        self.failed_pages = []
        self.processed_pages = 0
        
        # Performance metrics
        self.start_time = None
        self.pages_per_second = 0
        
        print("\n" + "="*70)
        print("  SEKOLAH SCRAPER - ULTRA FAST VERSION")
        print("="*70)
        print(f"  Workers: {max_workers} (MAXIMUM PARALLELIZATION)")
        print(f"  GPU Acceleration: {'ENABLED' if use_gpu else 'DISABLED'}")
        print(f"  Headless: {headless}")
        print(f"  Batch Size: {self.batch_size}")
        print(f"  Total Sekolah: {self.total_schools:,}")
        print(f"  Total Pages: {self.total_pages:,} (size={self.page_size})")
        print("="*70 + "\n")

    def create_driver(self):
        """Buat WebDriver instance dengan GPU acceleration"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            # Basic flags
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # GPU Acceleration
            if self.use_gpu:
                chrome_options.add_argument('--enable-gpu')
                chrome_options.add_argument('--enable-accelerated-2d-canvas')
                chrome_options.add_argument('--enable-accelerated-video-decode')
                chrome_options.add_argument('--ignore-gpu-blocklist')
                chrome_options.add_argument('--enable-gpu-rasterization')
                chrome_options.add_argument('--enable-zero-copy')
            else:
                chrome_options.add_argument('--disable-gpu')
            
            # Maximum performance optimization
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-pdf-viewer')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-permissions-api')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-offer-store-unmasked-wallet-cards')
            chrome_options.add_argument('--disable-speech-api')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
            chrome_options.add_argument('--force-color-profile=srgb')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--mute-audio')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Memory optimization
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disk-cache-size=1')
            chrome_options.add_argument('--media-cache-size=1')
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.media_stream": 2,
                "profile.default_content_setting_values.media_stream_mic": 2,
                "profile.default_content_setting_values.media_stream_camera": 2,
                "profile.default_content_setting_values.geolocation": 2,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(0)
            
            return driver
        
        except Exception as e:
            print(f"[ERROR] Gagal membuat driver: {e}")
            return None

    def extract_school_list(self, driver):
        """Ekstrak daftar sekolah dari halaman - OPTIMIZED"""
        try:
            # Minimal wait time
            time.sleep(1)
            
            # Direct parsing tanpa beautifulsoup untuk speed
            page_source = driver.page_source
            
            schools = []
            
            # Regex pattern untuk extract data lebih cepat
            npsn_pattern = re.compile(r'NPSN\s*:\s*(\w+)')
            
            # Parse dengan BeautifulSoup
            soup = BeautifulSoup(page_source, 'lxml')  # lxml lebih cepat dari html.parser
            articles = soup.find_all('article')
            
            for article in articles:
                try:
                    # NPSN
                    npsn = ''
                    npsn_text = article.find(string=lambda x: x and 'NPSN' in str(x))
                    if npsn_text:
                        match = npsn_pattern.search(str(npsn_text))
                        if match:
                            npsn = match.group(1).strip()
                    
                    # Nama Sekolah
                    nama = ''
                    nama_elem = article.find('h3')
                    if nama_elem:
                        nama = nama_elem.get_text(strip=True)
                    
                    # Status
                    status = ''
                    status_elem = article.find('div', class_=lambda x: x and ('text-orange-600' in str(x) or 'font-semibold' in str(x)))
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
                
                except:
                    continue
            
            return schools
        
        except Exception as e:
            if self.debug:
                print(f"  Ekstrak error: {e}")
            return []

    def scrape_page(self, page_num):
        """Scrape satu halaman - ULTRA OPTIMIZED"""
        driver = None
        try:
            driver = self.create_driver()
            if not driver:
                return {'page': page_num, 'schools': [], 'success': False}
            
            url = f"{self.base_url}/sekolah?page={page_num}&size={self.page_size}"
            driver.get(url)
            
            # Optimized wait
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except:
                return {'page': page_num, 'schools': [], 'success': False}
            
            schools = self.extract_school_list(driver)
            
            return {'page': page_num, 'schools': schools, 'success': len(schools) > 0}
        
        except Exception as e:
            if self.debug:
                print(f"  Page {page_num} error: {e}")
            return {'page': page_num, 'schools': [], 'success': False}
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def scrape_all(self, max_pages=None):
        """Fungsi utama scraping - ULTRA FAST PARALLEL"""
        self.start_time = time.time()
        
        # Load checkpoint
        checkpoint = self.load_checkpoint()
        start_page = 0
        
        if checkpoint:
            resume = input(f"\nResume dari halaman {checkpoint['last_page']}? (y/n): ").strip().lower()
            if resume == 'y':
                start_page = checkpoint['last_page'] + 1
                self.all_data = self.load_temp_data()
                print(f"Resume dengan {len(self.all_data)} data existing\n")
        
        print("="*70)
        print("MEMULAI ULTRA FAST SCRAPING...")
        print("="*70 + "\n")
        
        # Tentukan end page
        if max_pages:
            end_page = min(start_page + max_pages, self.total_pages)
        else:
            end_page = self.total_pages
        
        total_pages_to_scrape = end_page - start_page
        
        print(f"Range: Page {start_page} - {end_page-1}")
        print(f"Total: {total_pages_to_scrape:,} pages")
        print(f"Workers: {self.max_workers} parallel instances")
        print(f"GPU: {'ENABLED' if self.use_gpu else 'DISABLED'}\n")
        
        # Progress tracking thread
        def print_progress():
            last_count = 0
            while self.processed_pages < total_pages_to_scrape:
                time.sleep(5)
                current_count = len(self.all_data)
                elapsed = time.time() - self.start_time
                
                # Calculate rates
                schools_per_sec = current_count / elapsed if elapsed > 0 else 0
                pages_per_sec = self.processed_pages / elapsed if elapsed > 0 else 0
                
                # New items in last 5 seconds
                new_items = current_count - last_count
                last_count = current_count
                
                # ETA calculation
                remaining_pages = total_pages_to_scrape - self.processed_pages
                eta_seconds = remaining_pages / pages_per_sec if pages_per_sec > 0 else 0
                eta_minutes = eta_seconds / 60
                
                progress = (self.processed_pages / total_pages_to_scrape) * 100
                
                print(f"\n{'='*70}")
                print(f"[PROGRESS] {progress:.1f}% | Pages: {self.processed_pages:,}/{total_pages_to_scrape:,}")
                print(f"[DATA] Total: {current_count:,} sekolah | New (5s): +{new_items}")
                print(f"[SPEED] {schools_per_sec:.1f} sekolah/s | {pages_per_sec:.2f} pages/s")
                print(f"[ETA] {eta_minutes:.1f} minutes remaining")
                print(f"[FAILED] {len(self.failed_pages)} pages")
                print(f"{'='*70}\n")
        
        # Start progress thread
        progress_thread = threading.Thread(target=print_progress, daemon=True)
        progress_thread.start()
        
        try:
            # MAXIMUM PARALLEL PROCESSING
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit semua tasks sekaligus
                future_to_page = {
                    executor.submit(self.scrape_page, page): page 
                    for page in range(start_page, end_page)
                }
                
                completed = 0
                
                # Process hasil
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    completed += 1
                    
                    try:
                        result = future.result(timeout=30)
                        
                        if result['success'] and result['schools']:
                            schools = result['schools']
                            
                            with self.lock:
                                self.all_data.extend(schools)
                                self.processed_pages += 1
                                
                                # Simpan batch
                                if len(self.all_data) >= (self.batch_counter + 1) * self.batch_size:
                                    self.save_batch()
                        else:
                            with self.lock:
                                self.failed_pages.append(page_num)
                        
                        # Auto-save setiap 100 pages
                        if self.processed_pages % 100 == 0:
                            self.save_checkpoint(page_num, len(self.all_data))
                            self.save_temp_data(self.all_data)
                    
                    except Exception as e:
                        if self.debug:
                            print(f"[ERROR] Page {page_num}: {e}")
                        with self.lock:
                            self.failed_pages.append(page_num)
        
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Dihentikan oleh user")
        
        # Retry failed pages dengan workers lebih sedikit
        if self.failed_pages and len(self.failed_pages) < 1000:
            print(f"\n{'='*70}")
            print(f"[RETRY] Mencoba {len(self.failed_pages)} pages yang gagal...")
            print(f"{'='*70}\n")
            
            retry_workers = min(10, self.max_workers)
            
            with ThreadPoolExecutor(max_workers=retry_workers) as executor:
                retry_futures = {
                    executor.submit(self.scrape_page, page): page 
                    for page in self.failed_pages[:]
                }
                
                for future in as_completed(retry_futures):
                    page = retry_futures[future]
                    try:
                        result = future.result(timeout=30)
                        if result['success'] and result['schools']:
                            with self.lock:
                                self.all_data.extend(result['schools'])
                                self.failed_pages.remove(page)
                            print(f"[RETRY OK] Page {page}: {len(result['schools'])} sekolah")
                    except:
                        pass
        
        # Simpan final
        if self.all_data:
            filename = self.save_to_csv(self.all_data)
            
            elapsed = time.time() - self.start_time
            
            print(f"\n{'='*70}")
            print(f"[SELESAI - ULTRA FAST MODE]")
            print(f"{'='*70}")
            print(f"  Total sekolah: {len(self.all_data):,}")
            print(f"  Pages sukses: {self.processed_pages:,}/{total_pages_to_scrape:,}")
            print(f"  Pages gagal: {len(self.failed_pages)}")
            print(f"  Waktu total: {elapsed/60:.2f} menit ({elapsed:.0f} detik)")
            print(f"  Kecepatan: {len(self.all_data)/elapsed:.1f} sekolah/detik")
            print(f"  Kecepatan: {self.processed_pages/elapsed:.2f} pages/detik")
            print(f"  File output: {filename}")
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
            start_idx = (self.batch_counter * self.batch_size)
            end_idx = min(start_idx + self.batch_size, len(self.all_data))
            
            batch_data = self.all_data[start_idx:end_idx]
            
            if batch_data:
                filename = f"batch_{start_idx+1}-{end_idx}.csv"
                df = pd.DataFrame(batch_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                self.batch_counter += 1
        
        except Exception as e:
            if self.debug:
                print(f"  Batch save error: {e}")

    def save_to_csv(self, data):
        """Simpan ke CSV"""
        try:
            filename = f"data_sekolah_ultrafast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            df = pd.DataFrame(data)
            columns = ['npsn', 'nama_sekolah', 'alamat_sekolah', 'status_sekolah']
            df = df[columns]
            df = df.drop_duplicates(subset=['npsn'], keep='first')
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            return filename
        
        except Exception as e:
            print(f"[ERROR] Gagal simpan CSV: {e}")
            return None

    def save_checkpoint(self, page, count):
        """Simpan checkpoint"""
        with self.lock:
            try:
                with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'last_page': page,
                        'processed_count': count,
                        'processed_pages': self.processed_pages,
                        'total_count': self.total_schools,
                        'failed_pages': self.failed_pages[:100],  # Simpan max 100 failed pages
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2)
            except:
                pass

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
                    json.dump(data, f, ensure_ascii=False)
            except:
                pass

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
    print("  SEKOLAH SCRAPER - ULTRA FAST VERSION WITH GPU")
    print("="*70)
    print("\n  WARNING: Mode ini akan menggunakan resources maksimum!")
    print("  Pastikan sistem Anda memiliki:")
    print("  - RAM: Minimum 8GB (recommended 16GB+)")
    print("  - CPU: Multi-core processor")
    print("  - GPU: NVIDIA/AMD untuk acceleration")
    print("  - Internet: Stable high-speed connection")
    print("\n" + "="*70 + "\n")
    
    test_mode = input("Mode test (scrape 50 halaman)? (y/n): ").strip().lower()
    max_pages = 50 if test_mode == 'y' else None
    
    workers = input("Jumlah parallel workers (10-100, recommended 50, default=50): ").strip()
    workers = int(workers) if workers.isdigit() and int(workers) > 0 else 50
    workers = min(workers, 100)  # Max 100 workers
    
    use_gpu = input("Gunakan GPU acceleration? (y/n, default=y): ").strip().lower()
    use_gpu = use_gpu != 'n'
    
    headless = input("Gunakan headless browser? (y/n, default=y): ").strip().lower()
    headless = headless != 'n'
    
    debug = input("Aktifkan debug mode? (y/n, default=n): ").strip().lower()
    debug = debug == 'y'
    
    print("\n" + "="*70)
    print("KONFIGURASI:")
    print(f"  Workers: {workers}")
    print(f"  GPU: {'ENABLED' if use_gpu else 'DISABLED'}")
    print(f"  Headless: {headless}")
    print(f"  Mode: {'TEST (50 pages)' if test_mode == 'y' else 'FULL (11,457 pages)'}")
    print("="*70 + "\n")
    
    confirm = input("MULAI SCRAPING ULTRA FAST? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Dibatalkan.")
        exit()
    
    print("\n" + "="*70)
    print("LAUNCHING ULTRA FAST MODE...")
    print("="*70 + "\n")
    
    try:
        scraper = SekolahScraperUltraFast(
            max_workers=workers,
            headless=headless,
            debug=debug,
            use_gpu=use_gpu
        )
        
        data = scraper.scrape_all(max_pages=max_pages)
    
    except KeyboardInterrupt:
        print("\n\n[EXIT] Program dihentikan oleh user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()