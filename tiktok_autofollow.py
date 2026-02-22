import subprocess
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Konfigurasi Global ---
MAX_FOLLOWS_PER_SESSION = 10
SESSION_FOLLOW_COUNT = 0
SLEEP_TIME_MINUTES = 5

def buka_chrome_debug():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\tiktok_automation\user_data\3"
    
    print("Mencoba membuka Chrome dalam mode debug...")
    
    # Kill process chrome jika ada biar bersih saat restart
    os.system("taskkill /f /im chrome.exe >nul 2>&1")
    time.sleep(2)

    cmd = [
        chrome_path,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}"
    ]
    
    subprocess.Popen(cmd)
    time.sleep(5) # Waktu lebih lama agar window muncul

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

def random_sleep():
    delay = random.choice([7, 5, 6])
    print(f"  [Sleep] Menunggu {delay} detik...")
    time.sleep(delay)

def restart_session(driver, resume_url):
    global SESSION_FOLLOW_COUNT
    print(f"\n[LIMIT] Mencapai {MAX_FOLLOWS_PER_SESSION} target (9 follow + 1 pending).")
    print(f"[LIMIT] Target terakhir yang dicopy: {resume_url}")
    print("[LIMIT] Menutup browser dan istirahat...")
    
    try:
        driver.quit()
    except:
        pass
    
    # FORCE KILL CHROME
    try:
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
    except:
        pass
    
    # Istirahat
    print(f"[ISTIRAHAT] Tidur selama {SLEEP_TIME_MINUTES} menit...")
    time.sleep(SLEEP_TIME_MINUTES * 60)
    
    # Buka lagi
    print("[RESTART] Membuka kembali browser...")
    buka_chrome_debug()
    new_driver = jalankan_selenium()
    
    if new_driver:
        print(f"[RESTART] Membuka URL target: {resume_url}")
        new_driver.get(resume_url)
        time.sleep(5)
        SESSION_FOLLOW_COUNT = 0 # Reset counter
        return new_driver
    else:
        raise Exception("Gagal restart driver selenium.")

def check_and_handle_limit(driver, element, is_suggestion=False):
    global SESSION_FOLLOW_COUNT
    
    if SESSION_FOLLOW_COUNT >= MAX_FOLLOWS_PER_SESSION - 1:
        # Ini adalah target ke-10
        print("  [LIMIT CHECK] Ini adalah target ke-10. Tidak akan difollow sekarang.")
        
        target_url = driver.current_url
        if is_suggestion:
            try:
                # Cari link dari kartu suggestion
                # Struktur: Card -> a (link) ... button
                # Selector: ancestors div CardContainer/DivFadeScrollContainer
                target_url = driver.execute_script("""
                    var el = arguments[0];
                    var card = el.closest('.DivCardContainer') || el.closest('[class*="DivCardContainer"]');
                    if(card) {
                        var link = card.querySelector('a');
                        return link ? link.href : window.location.href;
                    }
                    return window.location.href;
                """, element)
                
                print(f"  [URL] Link akun suggestion didapatkan: {target_url}")
            except Exception as e:
                print(f"  [URL] Gagal ambil link suggestion, menggunakan URL saat ini: {target_url} ({e})")
        
        # Lakukan Restart
        new_driver = restart_session(driver, target_url)
        return False, new_driver # False artinya tidak diklik (skip), return driver baru
    
    return True, driver

def click_element_with_limit(driver, element, name="Element", is_suggestion=False):
    global SESSION_FOLLOW_COUNT
    
    # Cek Limit Sebelum Klik
    should_click, driver_or_new = check_and_handle_limit(driver, element, is_suggestion)
    
    if not should_click:
        return True, driver_or_new
    else:
        driver = driver_or_new
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            element.click()
            print(f"  [Klik] {name} berhasil diklik.")
            SESSION_FOLLOW_COUNT += 1
            print(f"  [Count] Total Follow sesi ini: {SESSION_FOLLOW_COUNT}")
            return True, driver
        except Exception as e:
            try:
                driver.execute_script("arguments[0].click();", element)
                print(f"  [Klik JS] {name} berhasil diklik via JS.")
                SESSION_FOLLOW_COUNT += 1
                print(f"  [Count] Total Follow sesi ini: {SESSION_FOLLOW_COUNT}")
                return True, driver
            except Exception as e2:
                print(f"  [Gagal] Tidak bisa klik {name}: {e2}")
                return False, driver

def process_profile(driver, wait):
    # 1. Klik tombol 'Ikuti' Utama
    print("\n--- Memproses Profil Utama ---")
    try:
        # Update selector utam: button[data-e2e='follow-button']
        # Pastikan tombol follow besar yang bukan di dalam list suggestion
        # Filter element yang tidak punya ancestor 'DivCardContainer'
        
        main_follow_script = """
        var buttons = document.querySelectorAll("button[data-e2e='follow-button']");
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            // Cek apakah tombol ini ada di dalam suggestion card list
            if (!btn.closest("[class*='DivCardContainer']") && !btn.closest(".DivCardContainer")) {
                if (btn.offsetParent !== null && btn.innerText.toLowerCase().includes('follow')) {
                     return btn;
                }
            }
        }
        return null;
        """
        
        main_follow_btn = driver.execute_script(main_follow_script)
        
        if main_follow_btn:
             txt = main_follow_btn.text.lower()
             if "following" in txt or "friends" in txt or "message" in txt:
                 print("  Status: Already following this account.")
             else:
                print(f"  Menemukan tombol 'Follow' utama: {main_follow_btn.text}")
                success, driver = click_element_with_limit(driver, main_follow_btn, "Tombol Follow Utama", is_suggestion=False)
                if success:
                    random_sleep()
        else:
             print("  Tombol 'Follow' utama tidak ditemukan/sudah follow.")
            
    except Exception as e:
        print(f"  Info: Skip tombol follow utama ({e})")

    # 2. Klik Panah 'Saran akun' -> English 'Suggested accounts' arrow
    print("\n--- Mencari Saran Akun ---")
    try:
        # Selector arrow berdasarkan HTML user: DivArrowIconContainer e6jlosd11
        # Atau path svg flip-rtl
        script_arrow = """
            var arrows = document.querySelectorAll("[class*='DivArrowIconContainer']");
            for (var i=0; i<arrows.length; i++) {
                 if(arrows[i].offsetParent !== null) return arrows[i];
            }
            return null;
        """
        arrow = driver.execute_script(script_arrow)

        if arrow:
            try:
                arrow.click()
            except:
                driver.execute_script("arguments[0].click();", arrow)
            time.sleep(2)
    except Exception as e:
        print(f"  Gagal klik panah saran: {e}")

    # 3. Loop Follow Suggestion
    print("\n--- Memproses List Saran Akun ---")
    
    # Ambil tombol follow HANYA di dalam suggestion container
    # Container Class: css-1yq9lsk... DivFadeScrollContainer
    # Card Class: DivCardContainer
    
    suggestion_xpath = "//div[contains(@class, 'DivCardContainer')]//button[@data-e2e='follow-button']"
    
    # Loop manual dengan re-fetch
    start_index = 0
    while True:
        try:
            # Cari ulang tombol setiap iterasi
            all_suggestion_btns = driver.find_elements(By.XPATH, suggestion_xpath)
            
            # Filter visible & text 'Follow'
            valid_btns = []
            for btn in all_suggestion_btns:
                if btn.is_displayed():
                    t = btn.text.lower()
                    if "follow" in t and "following" not in t:
                        valid_btns.append(btn)
            
            print(f"  Tombol suggestion valid saat ini: {len(valid_btns)}")
            
            if start_index >= len(valid_btns):
                break
                
            btn_to_click = valid_btns[start_index]
            
            # Action
            old_driver_id = driver.session_id
            success, driver = click_element_with_limit(driver, btn_to_click, f"Follow Suggestion #{start_index+1}", is_suggestion=True)
            
            if driver.session_id != old_driver_id:
                print("  [INFO] Sesi direstart. Kembali ke main loop.")
                return True, driver
                
            if success:
                start_index += 1
                random_sleep()
            else:
                start_index += 1
                
        except Exception as e:
            print(f"  Error loop suggestion: {e}")
            break

    # 4. Pindah ke Akun Lain
    print("\n--- Pindah ke Akun Selanjutnya ---")
    try:
        # Cari avatar link user lain
        # a href /@... img inside
        avatar_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/@')]//img/parent::div/parent::a")
        visible_avatars = [lnk for lnk in avatar_links if lnk.is_displayed()]
        
        if visible_avatars:
            random_avatar = random.choice(visible_avatars)
            next_url = random_avatar.get_attribute("href")
            
            print(f"  Memilih akun acak: {next_url}")
            try:
                random_avatar.click()
            except:
                driver.get(next_url)
            
            return True, driver
        else:
            print("  Tidak ditemukan avatar user lain.")
            return False, driver
            
    except Exception as e:
        print(f"  Gagal pindah akun: {e}")
        return False, driver

def main():
    buka_chrome_debug()
    driver = jalankan_selenium()
    
    if not driver:
        return

    wait = WebDriverWait(driver, 10)
    
    start_url = input("Masukkan Link Profil Awal: ").strip()
    if not start_url:
        print("URL kosong, keluar.")
        return

    print(f"Membuka {start_url}...")
    driver.get(start_url)
    time.sleep(3)

    while True:
        try:
            pindah_sukses, driver = process_profile(driver, wait)
            wait = WebDriverWait(driver, 10)

            if pindah_sukses:
                print("\nMenunggu halaman profil dimuat....")
                time.sleep(5)
            else:
                print("\nBuntu. Scroll...")
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\nDihentikan user.")
            break
        except Exception as e:
            print(f"\nError loop utama: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
