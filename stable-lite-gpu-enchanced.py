"""
SEKOLAH SCRAPER - PARALLEL VERSION WITH GPU OPTIMIZATION
=========================================================
Scraping data sekolah dari sekolah.data.kemendikdasmen.go.id
Field: NPSN, Nama, Alamat, Status
Teknik: Direct pagination dengan parallel processing (multiple tabs)
Fitur Baru: Auto-detect GPU dan optimasi berdasarkan hardware
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
import platform
import subprocess
import psutil


class HardwareDetector:
    """Deteksi hardware untuk optimasi otomatis"""
    
    def __init__(self):
        self.gpu_info = self.detect_gpu()
        self.cpu_info = self.detect_cpu()
        self.memory_info = self.detect_memory()
    
    def detect_gpu(self):
        """Deteksi GPU yang tersedia"""
        gpu_info = {
            'available': False,
            'name': None,
            'vendor': None,
            'memory_mb': 0,
            'score': 0
        }
        
        try:
            # Coba deteksi NVIDIA GPU
            if self._check_nvidia_gpu():
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', 
                                       '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    output = result.stdout.strip().split(',')
                    gpu_info['available'] = True
                    gpu_info['name'] = output[0].strip()
                    gpu_info['vendor'] = 'NVIDIA'
                    gpu_info['memory_mb'] = int(float(output[1].strip()))
                    gpu_info['score'] = self._calculate_gpu_score(gpu_info['name'], gpu_info['memory_mb'])
                    return gpu_info
        except:
            pass
        
        try:
            # Coba deteksi AMD GPU (Linux)
            if platform.system() == 'Linux':
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                if 'VGA' in result.stdout or 'Display' in result.stdout:
                    for line in result.stdout.split('\n'):
                        if 'AMD' in line or 'Radeon' in line:
                            gpu_info['available'] = True
                            gpu_info['vendor'] = 'AMD'
                            gpu_info['name'] = line.split(':')[-1].strip()
                            gpu_info['score'] = 50  # Default score untuk AMD
                            return gpu_info
        except:
            pass
        
        try:
            # Coba deteksi Intel GPU
            if platform.system() == 'Windows':
                import wmi
                w = wmi.WMI()
                for gpu in w.Win32_VideoController():
                    if 'Intel' in gpu.Name:
                        gpu_info['available'] = True
                        gpu_info['vendor'] = 'Intel'
                        gpu_info['name'] = gpu.Name
                        gpu_info['score'] = 30  # Intel GPU biasanya lebih lemah
                        return gpu_info
        except:
            pass
        
        return gpu_info
    
    def _check_nvidia_gpu(self):
        """Check jika NVIDIA GPU tersedia"""
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, timeout=2)
            return True
        except:
            return False
    
    def _calculate_gpu_score(self, name, memory_mb):
        """Hitung score GPU berdasarkan nama dan memory"""
        score = 0
        
        # Base score dari memory
        score += min(memory_mb / 1024, 24) * 10  # Max 240 points dari 24GB
        
        # Bonus dari model GPU
        name_lower = name.lower()
        if 'rtx' in name_lower:
            if '4090' in name_lower:
                score += 100
            elif '4080' in name_lower:
                score += 90
            elif '4070' in name_lower:
                score += 80
            elif '3090' in name_lower:
                score += 85
            elif '3080' in name_lower:
                score += 75
            elif '3070' in name_lower:
                score += 65
            else:
                score += 50
        elif 'gtx' in name_lower:
            score += 40
        elif 'tesla' in name_lower:
            score += 70
        elif 'quadro' in name_lower:
            score += 60
        
        return int(score)
    
    def detect_cpu(self):
        """Deteksi informasi CPU"""
        cpu_info = {
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'freq_mhz': 0,
            'score': 0
        }
        
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_info['freq_mhz'] = freq.max if freq.max else freq.current
        except:
            cpu_info['freq_mhz'] = 2400  # Default
        
        # Hitung CPU score
        cpu_info['score'] = (cpu_info['threads'] * 10) + (cpu_info['freq_mhz'] / 100)
        
        return cpu_info
    
    def detect_memory(self):
        """Deteksi informasi RAM"""
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3)
        }
    
    def get_optimal_workers(self):
        """Tentukan jumlah optimal workers berdasarkan hardware"""
        gpu_score = self.gpu_info['score']
        cpu_score = self.cpu_info['score']
        
        # Jika GPU lebih baik, gunakan GPU acceleration
        if gpu_score > cpu_score * 1.5 and self.gpu_info['available']:
            # GPU mode: bisa handle lebih banyak workers
            base_workers = min(self.cpu_info['threads'] * 2, 30)
            print(f"\n🎮 GPU MODE ENABLED (GPU Score: {gpu_score:.0f} vs CPU Score: {cpu_score:.0f})")
            print(f"   GPU: {self.gpu_info['name']}")
            print(f"   Recommended workers: {base_workers}")
            return base_workers, True
        else:
            # CPU mode: workers berdasarkan CPU cores
            base_workers = max(self.cpu_info['threads'] - 2, 4)
            base_workers = min(base_workers, 20)
            print(f"\n💻 CPU MODE (CPU Score: {cpu_score:.0f})")
            print(f"   CPU: {self.cpu_info['threads']} threads @ {self.cpu_info['freq_mhz']:.0f}MHz")
            print(f"   Recommended workers: {base_workers}")
            return base_workers, False
    
    def print_hardware_info(self):
        """Tampilkan informasi hardware"""
        print("\n" + "="*70)
        print("  HARDWARE DETECTION")
        print("="*70)
        
        # GPU Info
        if self.gpu_info['available']:
            print(f"  GPU: ✓ {self.gpu_info['vendor']} {self.gpu_info['name']}")
            if self.gpu_info['memory_mb'] > 0:
                print(f"       Memory: {self.gpu_info['memory_mb']/1024:.1f} GB")
            print(f"       Score: {self.gpu_info['score']:.0f}")
        else:
            print(f"  GPU: ✗ Not detected")
        
        # CPU Info
        print(f"  CPU: {self.cpu_info['cores']} cores / {self.cpu_info['threads']} threads")
        print(f"       Frequency: {self.cpu_info['freq_mhz']:.0f} MHz")
        print(f"       Score: {self.cpu_info['score']:.0f}")
        
        # Memory Info
        print(f"  RAM: {self.memory_info['total_gb']:.1f} GB total")
        print(f"       {self.memory_info['available_gb']:.1f} GB available")
        
        print("="*70)


class SekolahScraper:
    """Scraper untuk data sekolah dengan parallel processing dan GPU optimization"""

    def __init__(self, max_workers=None, headless=True, debug=False, use_gpu=None):
        # Hardware detection
        self.hardware = HardwareDetector()
        self.hardware.print_hardware_info()
        
        # Auto-configure workers berdasarkan hardware
        if max_workers is None:
            recommended_workers, gpu_mode = self.hardware.get_optimal_workers()
            self.max_workers = recommended_workers
            self.use_gpu = gpu_mode if use_gpu is None else use_gpu
        else:
            self.max_workers = max_workers
            self.use_gpu = use_gpu if use_gpu is not None else False
        
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
        print("  SEKOLAH SCRAPER - PARALLEL VERSION (GPU-OPTIMIZED)")
        print("="*70)
        print(f"  Mode: {'🎮 GPU-ACCELERATED' if self.use_gpu else '💻 CPU'}")
        print(f"  Workers: {self.max_workers} (concurrent tabs)")
        print(f"  Headless: {headless}")
        print(f"  Batch Size: {self.batch_size}")
        print(f"  Total Sekolah: {self.total_schools:,}")
        print(f"  Total Pages: {self.total_pages:,} (size={self.page_size})")
        print("="*70 + "\n")

    def create_driver(self):
        """Buat WebDriver instance dengan optimasi GPU jika tersedia"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            
            # GPU Optimization
            if self.use_gpu and self.hardware.gpu_info['available']:
                # Enable GPU acceleration
                chrome_options.add_argument('--enable-gpu-rasterization')
                chrome_options.add_argument('--enable-zero-copy')
                chrome_options.add_argument('--enable-native-gpu-memory-buffers')
                chrome_options.add_argument('--ignore-gpu-blocklist')
                
                if self.debug:
                    print("  [GPU] Hardware acceleration enabled")
            else:
                # Disable GPU untuk CPU mode
                chrome_options.add_argument('--disable-gpu')
            
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
        print(f"Total: {total_pages_to_scrape:,} pages dengan {self.max_workers} workers parallel")
        print(f"Hardware mode: {'🎮 GPU-ACCELERATED' if self.use_gpu else '💻 CPU'}\n")
        
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
            print(f"  Mode: {'🎮 GPU-ACCELERATED' if self.use_gpu else '💻 CPU'}")
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
    print("  SEKOLAH SCRAPER - PARALLEL VERSION (GPU-OPTIMIZED)")
    print("="*70)
    
    test_mode = input("\nMode test (scrape 10 halaman saja)? (y/n): ").strip().lower()
    max_pages = 10 if test_mode == 'y' else None
    
    # Auto-detect atau manual workers
    auto = input("Gunakan auto-detect hardware untuk workers? (y/n, default=y): ").strip().lower()
    if auto == 'n':
        workers = input("Jumlah parallel workers (recommended 10-20, default=10): ").strip()
        workers = int(workers) if workers.isdigit() else 10
        
        gpu_mode = input("Paksa gunakan GPU mode? (y/n, default=auto): ").strip().lower()
        use_gpu = True if gpu_mode == 'y' else (False if gpu_mode == 'n' else None)
    else:
        workers = None  # Auto-detect
        use_gpu = None  # Auto-detect
    
    headless = input("Gunakan headless browser? (y/n, default=y): ").strip().lower()
    headless = headless != 'n'
    
    debug = input("Aktifkan debug mode? (y/n, default=n): ").strip().lower()
    debug = debug == 'y'
    
    print("\n" + "="*70)
    print("MEMULAI SCRAPER PARALLEL (GPU-OPTIMIZED)...")
    if workers:
        print(f"WARNING: Akan membuka {workers} browser instances secara bersamaan!")
    else:
        print(f"WARNING: Akan membuka multiple browser instances (auto-detected)")
    print("="*70 + "\n")
    
    confirm = input("Lanjutkan? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Dibatalkan.")
        exit()
    
    try:
        scraper = SekolahScraper(
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