import requests
import pandas as pd
import time
import os
import json
from tqdm import tqdm
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Konfigurasi
BASE_URL = "https://sekolah.data.kemendikdasmen.go.id"
OUTPUT_FILE = "data_sekolah_kemendikbuddasmen.csv"
CHECKPOINT_FILE = "scraping_checkpoint.json"
TEMP_DATA_FILE = "temp_scraped_data.csv"

# Headers untuk request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': BASE_URL,
}

def save_checkpoint(kab_index, total_kab, data_count, current_kab=""):
    checkpoint = {
        'last_kab_index': kab_index,
        'current_kab': current_kab,
        'total_kab': total_kab,
        'data_count': data_count,
        'timestamp': datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def load_existing_data():
    if os.path.exists(TEMP_DATA_FILE):
        try:
            df = pd.read_csv(TEMP_DATA_FILE, encoding='utf-8-sig')
            return df.to_dict('records')
        except:
            return []
    return []

def save_temp_data(all_data):
    df = pd.DataFrame(all_data)
    df.to_csv(TEMP_DATA_FILE, index=False, encoding='utf-8-sig')

def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def get_kabupaten_list(session):
    try:
        response = session.get(f"{BASE_URL}/index.php", timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        select_kab = soup.find('select', {'id': 'kode_kabupaten'})
        
        if select_kab:
            kabupaten_list = []
            for option in select_kab.find_all('option'):
                value = option.get('value')
                text = option.get_text(strip=True)
                if value and value != "":
                    kabupaten_list.append({'kode': value, 'nama': text})
            print(f"✅ Ditemukan {len(kabupaten_list)} kabupaten/kota")
            return kabupaten_list
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def get_total_schools(html_content):
    """Extract total jumlah sekolah dari pagination info"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        pagination = soup.find('ul', {'class': 'pagination'})
        if pagination:
            active_li = pagination.find('li', {'class': 'active'})
            if active_li:
                text = active_li.get_text(strip=True)
                # Format: "580 Sekolah"
                match = re.search(r'(\d+)\s+Sekolah', text)
                if match:
                    return int(match.group(1))
        return 0
    except:
        return 0

def parse_school_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    schools = []
    boxes = soup.find_all('div', class_='box box-default')
    
    for box in boxes:
        try:
            school = {}
            list_items = box.find_all('li', class_='list-group-item')
            
            if list_items:
                first_item = list_items[0]
                link = first_item.find('a')
                
                if link:
                    text = link.get_text(strip=True)
                    npsn_match = re.search(r'\(([^\)]+)\)', text)
                    if npsn_match:
                        school['npsn'] = npsn_match.group(1).strip()
                    
                    nama_match = re.search(r'\)\s*(.+)', text)
                    if nama_match:
                        school['nama'] = nama_match.group(1).strip()
                    else:
                        school['nama'] = text
                    
                    detail_url = link.get('href', '')
                    if detail_url:
                        school['detail_url'] = detail_url
                        sekolah_id_match = re.search(r'/profil/([A-F0-9-]+)', detail_url)
                        if sekolah_id_match:
                            school['sekolah_id'] = sekolah_id_match.group(1)
                
                for i, item in enumerate(list_items[1:], 1):
                    text = item.get_text(strip=True)
                    if len(text) < 5:
                        continue
                    
                    if i == 1:
                        school['alamat_jalan'] = text
                    elif i == 2:
                        school['kelurahan_kecamatan'] = text
                        kec_match = re.search(r'Kec\.\s*(.+)', text)
                        if kec_match:
                            school['kecamatan'] = kec_match.group(1).strip()
                    elif i == 3:
                        school['kabupaten_provinsi'] = text
                        parts = text.split('Prov.')
                        if len(parts) == 2:
                            school['kabupaten_kota'] = parts[0].strip()
                            school['provinsi'] = 'Prov. ' + parts[1].strip()
                
                if school.get('nama') or school.get('npsn'):
                    schools.append(school)
        except:
            continue
    
    return schools

def scrape_kabupaten(session, kab_code, kab_name, bentuk_pendidikan="", status_sekolah="semua"):
    """Scraping dengan AJAX pagination yang benar"""
    all_schools = []
    page = 1
    
    # Halaman 1 - menggunakan POST biasa untuk mendapatkan total
    url_page1 = f"{BASE_URL}/index.php/Chome/pencarian/"
    data_page1 = {
        'page': 1,
        'kode_kabupaten': kab_code,
        'kode_kecamatan': '',
        'bentuk_pendidikan': bentuk_pendidikan,
        'status_sekolah': status_sekolah,
        'nama': ''
    }
    
    try:
        response = session.post(url_page1, data=data_page1, timeout=30)
        if response.status_code != 200:
            return []
        
        html_content = response.text
        schools_page1 = parse_school_data(html_content)
        
        # Get total schools dari pagination
        total_schools = get_total_schools(html_content)
        
        if not schools_page1:
            return []
        
        all_schools.extend(schools_page1)
        
        # Jika total schools > 4, lanjutkan ke halaman berikutnya
        if total_schools > 4:
            schools_per_page = len(schools_page1)  # Biasanya 4
            total_pages = (total_schools + schools_per_page - 1) // schools_per_page
            
            print(f"      📊 Total: {total_schools} sekolah, {total_pages} halaman")
            
            # Loop untuk halaman 2 dan seterusnya menggunakan AJAX
            url_ajax = f"{BASE_URL}/index.php/Chome/pagingpencarian"
            
            for page in range(2, total_pages + 1):
                try:
                    data_ajax = {
                        'page': page,
                        'nama': '',
                        'kode_kabupaten': kab_code,
                        'kode_kecamatan': '',
                        'bentuk_pendidikan': bentuk_pendidikan,
                        'status_sekolah': status_sekolah
                    }
                    
                    response_ajax = session.post(url_ajax, data=data_ajax, timeout=30)
                    
                    if response_ajax.status_code == 200:
                        schools_page = parse_school_data(response_ajax.text)
                        
                        if schools_page:
                            all_schools.extend(schools_page)
                            
                            # Progress setiap 20 halaman
                            if page % 20 == 0:
                                print(f"      📄 Progress: {page}/{total_pages} halaman, {len(all_schools)} sekolah")
                    
                    # Delay untuk menghindari rate limiting
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"      ⚠️ Error page {page}: {e}")
                    continue
        
        # Tambahkan info kabupaten ke semua sekolah
        for school in all_schools:
            school['kabupaten_kota'] = kab_name
            school['kode_kab'] = kab_code
        
        return all_schools
        
    except Exception as e:
        print(f"      ❌ Error scraping: {e}")
        return []

def scrape_all_sekolah(resume=True, filter_jenjang="", filter_status="semua"):
    print("🚀 Memulai scraping data sekolah Kemendikbuddasmen...")
    print(f"📌 Base URL: {BASE_URL}")
    
    session = get_session()
    
    print("\n📍 Mengambil daftar kabupaten/kota...")
    kabupaten_list = get_kabupaten_list(session)
    
    if not kabupaten_list:
        print("❌ Tidak dapat mengambil daftar kabupaten")
        return
    
    checkpoint = load_checkpoint() if resume else None
    start_index = 0
    all_data = []
    
    if checkpoint and resume:
        print(f"\n📂 Checkpoint ditemukan!")
        print(f"   Last: {checkpoint.get('current_kab', 'N/A')}")
        print(f"   Progress: {checkpoint['last_kab_index']}/{checkpoint['total_kab']}")
        print(f"   Data: {checkpoint['data_count']:,}")
        
        response = input("\n🔄 Resume? (y/n): ").lower()
        if response == 'y':
            start_index = checkpoint['last_kab_index'] + 1
            all_data = load_existing_data()
            print(f"✅ Resume dari index {start_index}")
        else:
            if os.path.exists(TEMP_DATA_FILE):
                os.remove(TEMP_DATA_FILE)
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
    
    total_kab = len(kabupaten_list)
    print(f"\n📊 Total kabupaten/kota: {total_kab}")
    print(f"▶️  Mulai dari index: {start_index}\n")
    
    with tqdm(total=total_kab - start_index, desc="Progress") as pbar:
        for i in range(start_index, total_kab):
            kab = kabupaten_list[i]
            kab_code = kab['kode']
            kab_name = kab['nama']
            
            schools = scrape_kabupaten(
                session, kab_code, kab_name,
                bentuk_pendidikan=filter_jenjang,
                status_sekolah=filter_status
            )
            
            if schools:
                all_data.extend(schools)
                pbar.set_postfix({
                    'Kab': kab_name[:25],
                    'Sekolah': len(schools),
                    'Total': f"{len(all_data):,}"
                })
            else:
                pbar.set_postfix({
                    'Kab': kab_name[:25],
                    'Status': 'No data'
                })
            
            pbar.update(1)
            
            # Save checkpoint setiap 5 kabupaten
            if (i + 1) % 5 == 0:
                save_checkpoint(i, total_kab, len(all_data), kab_name)
                save_temp_data(all_data)
            
            # Backup setiap 50 kabupaten
            if (i + 1) % 50 == 0:
                backup_file = f"backup_kab_{i+1}.csv"
                df_backup = pd.DataFrame(all_data)
                df_backup.to_csv(backup_file, index=False, encoding='utf-8-sig')
                print(f"\n💾 Backup: {backup_file} ({len(all_data):,} sekolah)")
            
            time.sleep(1)
    
    print(f"\n✅ Scraping selesai! Total: {len(all_data):,}")
    
    if not all_data:
        print("❌ Tidak ada data")
        return
    
    df = pd.DataFrame(all_data)
    
    if 'npsn' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['npsn'], keep='first')
        if initial_count > len(df):
            print(f"🗑️  Duplikat dihapus: {initial_count - len(df):,}")
    
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"💾 Disimpan: {OUTPUT_FILE}")
    
    if os.path.exists(TEMP_DATA_FILE):
        os.remove(TEMP_DATA_FILE)
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
    
    print("\n" + "="*70)
    print("📊 STATISTIK")
    print("="*70)
    print(f"Total Sekolah: {len(df):,}")
    print(f"Total Kolom: {len(df.columns)}")
    
    if 'kabupaten_kota' in df.columns:
        print(f"\n🗺️  Top 10 Kabupaten:")
        for i, (kab, count) in enumerate(df['kabupaten_kota'].value_counts().head(10).items(), 1):
            print(f"   {i:2}. {kab:40} : {count:6,}")

def test_scraping(session):
    print("🧪 Test scraping Kab. Aceh Barat...")
    
    schools = scrape_kabupaten(session, '060600', 'Prov. Aceh - Kab. Aceh Barat')
    
    if schools:
        print(f"\n✅ Berhasil: {len(schools)} sekolah")
        print("\n📋 Sample 5 sekolah pertama:")
        for i, school in enumerate(schools[:5], 1):
            print(f"\n{i}. {school.get('nama', 'N/A')}")
            print(f"   NPSN: {school.get('npsn', 'N/A')}")
        
        df = pd.DataFrame(schools)
        df.to_csv('test_aceh_barat.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 Disimpan: test_aceh_barat.csv")
        print(f"📊 Total: {len(schools)} sekolah")
    else:
        print("\n❌ Gagal scraping")

def main():
    print("="*70)
    print("  SCRAPER DATA SEKOLAH KEMENDIKBUDDASMEN")
    print("  https://sekolah.data.kemendikdasmen.go.id")
    print("="*70)
    
    session = get_session()
    
    print("\n📋 Menu:")
    print("1. Test scraping Kab. Aceh Barat (580 sekolah)")
    print("2. Scrape semua data")
    print("3. Scrape dengan filter jenjang")
    print("4. Scrape dengan filter status")
    
    choice = input("\nPilih (1-4): ").strip()
    
    try:
        if choice == '1':
            test_scraping(session)
        elif choice == '2':
            scrape_all_sekolah(resume=True)
        elif choice == '3':
            print("\n📚 Jenjang: SD, SMP, SMA, SMK, TK, dll")
            jenjang = input("Masukkan jenjang: ").strip().upper()
            scrape_all_sekolah(resume=True, filter_jenjang=jenjang)
        elif choice == '4':
            print("\n🏛️  1. Negeri  2. Swasta")
            status_choice = input("Pilih (1/2): ").strip()
            status = "NEGERI" if status_choice == '1' else "SWASTA"
            scrape_all_sekolah(resume=True, filter_status=status)
        else:
            print("❌ Pilihan tidak valid")
    except KeyboardInterrupt:
        print("\n\n⚠️  Dihentikan oleh user")
        print("💾 Checkpoint tersimpan")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()