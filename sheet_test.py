import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import gspread
from google.oauth2.service_account import Credentials

def append_with_retry(sheet, rows, max_retries=3):
    for retry in range(max_retries):
        try:
            if len(rows) == 1:
                sheet.append_row(rows[0])
            else:
                sheet.append_rows(rows)
            print(f"✅ {len(rows)} ilan başarıyla eklendi!")
            return True
        except Exception as e:
            print(f"❌ Ekleme başarısız (deneme {retry+1}/{max_retries}): {e}")
            if retry < max_retries - 1:
                human_delay(5, 7)
    return False

def human_delay(min_sec=2, max_sec=6):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("LinkedIn Jobs").sheet1

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options)

try:
    driver.get("https://www.linkedin.com/login")
    human_delay(3, 5)

    import pickle
    try:
        cookies = pickle.load(open("linkedin_cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Giriş tamamlandı.")
    except:
        print("Cookie bulunamadı, manuel giriş gerekli.")
        input("Manuel giriş yapıp Enter'a basın...")

    search_url = "https://www.linkedin.com/jobs/search/?keywords=fullstack%20remote&location=Worldwide&geoId=92000000"
    driver.get(search_url)

    wait = WebDriverWait(driver, 30)

    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]")))
    except:
        print("İş ilanları yüklenemedi, sayfa yenileniyor...")
        driver.refresh()
        human_delay(3, 5)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]")))

    def load_more_jobs(target_count=100):
        scroll_pause_time = 3
        job_ids = set()
        last_count = 0
        no_change_count = 0

        print(f"Hedef: {target_count} ilan yüklenmesi...")

        while len(job_ids) < target_count:
            job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
            new_ids = {card.get_attribute("data-occludable-job-id") for card in job_cards if card.get_attribute("data-occludable-job-id")}
            job_ids.update(new_ids)

            current_count = len(job_ids)
            print(f"Şu anki ilan sayısı: {current_count}")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            human_delay(scroll_pause_time, scroll_pause_time + 2)

            try:
                wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")) > len(job_cards))
            except:
                pass

            if current_count == last_count:
                no_change_count += 1
                print(f"Yeni ilan yok (deneme {no_change_count}/3)")
                if no_change_count >= 3:
                    print("Daha fazla ilan bulunamadı, scroll durduruluyor.")
                    break
            else:
                no_change_count = 0

            last_count = current_count

        return driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

    existing_values = sheet.get_all_values()
    existing_ids = set()
    for row in existing_values[2:]:  # Header ve boş satırı atla
        if len(row) >= 6:
            job_id = row[5].strip() if len(row) > 5 and row[5] else ""
            if job_id:
                existing_ids.add(job_id)

    print(f"Mevcut benzersiz ilan ID sayısı: {len(existing_ids)}")

    job_cards = load_more_jobs(target_count=75)
    processed_jobs = []
    processed_count = 0

    for i, job_card in enumerate(job_cards):
        try:
            job_id = job_card.get_attribute("data-occludable-job-id")
            if not job_id or job_id in existing_ids:
                print(f"Bu ilan zaten mevcut (ID): {job_id}")
                continue

            processed_count += 1
            print(f"\nİşleniyor ({processed_count}/{len(job_cards)}): {job_id}")

            driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
            human_delay(1, 2)
            driver.execute_script("arguments[0].click();", job_card)
            human_delay(2, 4)

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__job-details--container")))
            human_delay(1, 2)

            title = ""
            company = ""
            location = ""
            description = ""
            link = ""

            try:
                title = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title").text.strip()
                company = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name").text.strip()
                location = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__tertiary-description-container").text.strip().split('\n')[0].split('·')[0].strip()
            except:
                continue

            # İlan linkini alıyoruz:
            try:
                link = job_card.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                link = ""

            try:
                show_more = driver.find_element(By.CSS_SELECTOR, ".jobs-description__footer-button")
                if show_more.is_displayed():
                    driver.execute_script("arguments[0].click();", show_more)
                    human_delay(1, 2)
            except:
                pass

            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, ".jobs-box__html-content")
                description = desc_elem.text.strip()
                if "Şirket hakkında" in description:
                    description = description.split("Şirket hakkında")[0].strip()
            except:
                continue

            if (not title.strip() or not company.strip() or not description.strip() or not link.strip()):
                print(f"Eksik bilgi - Başlık: {bool(title.strip())}, Şirket: {bool(company.strip())}, Açıklama: {bool(description.strip())}, Link: {bool(link.strip())}")
                continue

            # Son bir kez daha job_id ve link ile kontrol et
            if job_id in existing_ids:
                print(f"Bu ilan zaten mevcut (ID): {job_id}")
                continue

            processed_jobs.append([job_id, title, company, location, description, link])
            existing_ids.add(job_id)
            print(f"✅ İlan işlendi: {title} (ID: {job_id})")

        except Exception as e:
            print(f"Genel hata {job_id}: {str(e)}")
            continue

    if processed_jobs:
        print(f"\nToplam {len(processed_jobs)} yeni ilan ekleniyor...")
        if not append_with_retry(sheet, processed_jobs):
            print("\nToplu ekleme başarısız, tek tek denenecek...")
            for job in processed_jobs:
                if append_with_retry(sheet, [job]):
                    print(f"✅ Eklendi: {job[0]}")
                else:
                    print(f"❌ Eklenemedi: {job[0]}")

finally:
    try:
        print("Tarayıcı kapatılıyor...")
        driver.quit()
        print("İşlem tamamlandı!")
    except Exception as e:
        print(f"Driver kapatılırken hata: {e}")
