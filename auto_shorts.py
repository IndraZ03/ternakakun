import subprocess
import os
import time
import shutil
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import yt_dlp

# --- KONFIGURASI ---
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\tiktok_automation\user_data\1"
OUTPUT_FOLDER = r"c:\ternakakun\output"
LOGO_PATH = r"c:\ternakakun\logo.png"
CLOSING_PATH = r"c:\ternakakun\closing.mp4"
FFMPEG_CMD = "ffmpeg"  # Pastikan ffmpeg ada di PATH

# --- FUNGSI SELENIUM DARI @[flow.py] ---
def buka_chrome_debug():
    print("Mencoba membuka Chrome dalam mode debug...")
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={USER_DATA_DIR}"
    ]
    subprocess.Popen(cmd)
    time.sleep(3)

def jalankan_selenium():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Selenium berhasil terhubung ke Chrome!")
        return driver
    except Exception as e:
        print(f"Gagal menghubungkan Selenium: {e}")
        return None

# --- FUNGSI DOWNLOAD YT DARI @[yt.py] ---
def download_yt_short(url, output_filename):
    """
    Mengunduh YT Short ke file spesifik.
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': False,
        'no_warnings': True,
        'merge_output_format': 'mp4' # Memaksa output jadi mp4 jika perlu merge
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            # Pastikan file ada (kadang yt-dlp menambahkan ekstensi lain jika merge gagal atau format beda)
            # Kita asumsi output_filename yang kita minta adalah hasil akhirnya (misal .mp4)
            if os.path.exists(output_filename):
                print(f"Video berhasil diunduh: {output_filename}")
                return True
            else:
                # Cek jika ada file dengan nama sama tapi ekstensi beda (case jarang dengan format yang kita set)
                print(f"Warning: File output spesifik tidak ditemukan, mungkin ekstensi berbeda.")
                return False
        except Exception as e:
            print(f"Error saat mengunduh: {e}")
            return False

# --- FUNGSI WATERMARK DARI @[watermark.py] ---
def add_watermark(input_video, logo_path, output_video, scale_factor=0.2):
    if not os.path.exists(input_video):
        print(f"File video {input_video} tidak ditemukan untuk watermark!")
        return False
    
    # Filter complex untuk watermark di pojok kiri atas
    # scale=iw*0.2:-1 resize logo
    # overlay=10:10 posisi 10px dari kiri atas
    cmd = [
        FFMPEG_CMD, '-y',
        '-i', input_video,
        '-i', logo_path,
        '-filter_complex', f'[1:v]scale=iw*{scale_factor}:-1 [logo]; [0:v][logo]overlay=10:10',
        '-c:a', 'copy',
        output_video
    ]
    
    print(f"Sedang memproses watermark... (Ini mungkin memakan waktu)")
    try:
        # Hapus stdout=subprocess.DEVNULL agar progress ffmpeg terlihat
        subprocess.run(cmd, check=True) 
        print(f"Watermark berhasil ditambahkan: {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error watermark: {e}")
        return False

# --- FUNGSI CLOSING DARI @[closing.py] ---
def add_closing(input_video, closing_video, output_video):
    if not os.path.exists(input_video):
        print(f"File video {input_video} tidak ditemukan untuk closing!")
        return False
    
    # Asumsi video portrait 576x1024, disesuaikan agar robust
    
    cmd = [
        FFMPEG_CMD, '-y',
        '-i', input_video,
        '-i', closing_video,
        '-filter_complex',
        '[0:v]scale=576:1024:force_original_aspect_ratio=increase,crop=576:1024,setsar=1,fps=30[v0];' # Normalize video utama
        '[0:a]aresample=48000[a0];'
        '[1:v]scale=576:1024:force_original_aspect_ratio=increase,crop=576:1024,setsar=1,fps=30[v1];' # Normalize closing
        '[1:a]aresample=48000[a1];'
        '[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]',
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        output_video
    ]
    
    print(f"Sedang memproses closing... (Ini mungkin memakan waktu)")
    try:
        # Hapus stdout=subprocess.DEVNULL agar progress ffmpeg terlihat
        subprocess.run(cmd, check=True)
        print(f"Closing berhasil ditambahkan: {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error closing: {e}")
        return False

# --- LOGIKA UTAMA ---
def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # 1. Buka Chrome & Selenium
    buka_chrome_debug()
    driver = jalankan_selenium()
    
    if not driver:
        return
    
    wait = WebDriverWait(driver, 10)
    
    # 2. Akses URL Awal
    start_url = "https://www.youtube.com/shorts/9_Jlv9JxtVo"
    print(f"Mengakses {start_url} ...")
    driver.get(start_url)
    time.sleep(5) # Tunggu load awal
    
    try:
        while True:
            # 3. Ambil Link & ID Video
            # Tunggu URL stabil (opsional, tapi bagus di loop)
            current_url = driver.current_url
            print(f"\n--- Memproses Video: {current_url} ---")
            
            video_id = current_url.split('/')[-1].split('?')[0] # Bersihkan query params jika ada
            if not video_id:
                print("Gagal mengambil Video ID.")
                continue

            # Nama file sementara
            temp_download = os.path.abspath(f"temp_{video_id}.mp4")
            temp_watermark = os.path.abspath(f"temp_wm_{video_id}.mp4")
            final_output = os.path.join(OUTPUT_FOLDER, f"{video_id}_final.mp4")
            
            # Cek jika sudah pernah didownload
            if os.path.exists(final_output):
                print(f"Video {video_id} sudah ada, melewati...")
            else:
                # 4. Download
                if download_yt_short(current_url, temp_download):
                    # 5. Watermark
                    wm_success = add_watermark(temp_download, LOGO_PATH, temp_watermark)
                    
                    if wm_success:
                        # 6. Closing
                        if add_closing(temp_watermark, CLOSING_PATH, final_output):
                            print(f"SUKSES! Video tersimpan di: {final_output}")
                        else:
                            print("Gagal menambahkan closing.")
                    else:
                        print("Gagal menambahkan watermark.")
                    
                    # Bersihkan file temp
                    for f in [temp_download, temp_watermark]:
                        if os.path.exists(f):
                            os.remove(f)
                else:
                    print("Gagal download video.")

            # 7. Klik Next Video
            print("Mencari tombol Next Video...")
            prev_url = driver.current_url
            try:
                # Opsi 1: Cari tombol Next Video dengan selector yang lebih luas
                # User memberikan referensi: <yt-touch-feedback-shape ...> yang merupakan child dari tombol
                next_button = None
                try:
                    # Cari button nav-down (biasanya ada ID nya)
                    next_button = driver.find_element(By.ID, "navigation-button-down")
                except:
                    pass
                
                if not next_button:
                    try:
                        # Cari berdasarkan aria-label
                        next_button = driver.find_element(By.XPATH, "//button[@aria-label='Next video' or @aria-label='Video berikutnya']")
                    except:
                        pass

                if next_button:
                    print("Tombol Next ditemukan.")
                    # Gunakan JavaScript Click untuk mengatasi 'element not interactable'
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", next_button)
                    print("Klik JS pada tombol Next berhasil.")
                else:
                    print("Tombol Next tidak ditemukan secara spesifik.")
                    # Fallback ke Keyboard (sangat reliabel untuk Shorts)
                    print("Menggunakan tombol Panah Bawah (Keyboard)...")
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
                
                # Tunggu URL berubah maksimal 10 detik
                print("Menunggu video berikutnya dimuat...")
                try:
                    WebDriverWait(driver, 10).until(lambda d: d.current_url != prev_url)
                    print("URL Video berubah.")
                    time.sleep(3) # Tunggu buffer awal
                except Exception as e_wait:
                    print(f"URL tidak berubah setelah klik/tombol. Mencoba force keyboard arrow down...")
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
                    time.sleep(3)
                
            except Exception as e:
                print(f"Error saat navigasi ke video selanjutnya: {e}")
                print("Mencoba recovery dengan Arrow Down...")
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
                    time.sleep(3)
                except:
                    pass
                
    except KeyboardInterrupt:
        print("\nProses dihentikan oleh pengguna.")
    except Exception as e:
        print(f"Terjadi kesalahan fatal: {e}")

if __name__ == "__main__":
    main()
