import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import datetime
from datetime import timedelta, date
import random

# 🔧 Konfiguracja
QUERIES = {
    "blonde": "woman with blonde hair",
    "brunette": "woman with brown hair",
    "black": "woman with black hair",
    "redhead": "woman with red hair",
    "asian_woman": "asian woman",
    "black_woman": "black woman",
    "white_woman": "european woman",
    "indian_woman": "indian woman"
}
IMAGES_PER_ENGINE = 7000  # na każdą kategorię per silnik (używane do obliczenia łącznego limitu)
TOTAL_IMAGES_PER_CATEGORY = 4 * IMAGES_PER_ENGINE # Łączna docelowa liczba zdjęć na kategorię

# 🔧 Opcje Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def download_images(image_urls, category, offset=0):
    SAVE_DIR = f"images_{category}"
    os.makedirs(SAVE_DIR, exist_ok=True)
    existing_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".jpg")]
    current_offset = len(existing_files) if offset == 0 else offset
    print(f"Current offset for '{category}': {current_offset}")

    print(f"📥 Pobieranie {len(image_urls)} zdjęć dla '{category}' z offsetem {current_offset}...")
    count = 0
    for idx, url in enumerate(image_urls):
        try:
            filename = f"{category}_{current_offset + idx + 1:04d}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            if os.path.exists(filepath):
                continue

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                count += 1
        except Exception as e:
            print(f"❌ Błąd przy pobieraniu {url}: {e}")
            continue
    print(f"✅ Zakończono pobieranie dla '{category}'. Pobrano: {count}.")
    return count

def collect_bing_images(query, limit, date=None, max_scroll_attempts=5):
    print(f"\n🔍 BING: Szukanie '{query}' (limit: {limit}, data: {date or 'brak'}, max_scroll_attempts: {max_scroll_attempts})")
    
    base_url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}&form=HDRSC2"
    if date:
        search_url = f"{base_url}&freshness={date}"
    else:
        search_url = base_url

    driver.get(search_url)
    time.sleep(2)
    image_urls = set()
    scroll_attempts = 0
    last_count = 0

    while len(image_urls) < limit and scroll_attempts < max_scroll_attempts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        try:
            show_more = driver.find_element(By.CLASS_NAME, "btn_seemore")
            if show_more.is_displayed() and show_more.is_enabled():
                driver.execute_script("arguments[0].click();", show_more)
                print("Clicked Bing 'Show More'")
                time.sleep(3)
        except:
            pass

        containers = driver.find_elements(By.CLASS_NAME, "iusc")
        for c in containers:
            try:
                meta = c.get_attribute("m")
                meta_json = json.loads(meta)
                murl = meta_json["murl"]
                if murl not in image_urls:
                    image_urls.add(murl)
            except:
                continue

        print(f"Collected {len(image_urls)} URLs from Bing so far for date {date or 'Any time'}.")

        if len(image_urls) == last_count:
            scroll_attempts += 1
            print(f"No new Bing images found since last scroll for date {date or 'Any time'}. Attempt {scroll_attempts}/{max_scroll_attempts}")
            if scroll_attempts >= max_scroll_attempts:
                 print(f"Reached max scroll attempts for date {date or 'Any time'}. No new images found.")
                 break
        else:
            last_count = len(image_urls)
            scroll_attempts = 0
            print(f"Found new Bing images for date {date or 'Any time'}. Resetting scroll_attempts.")

    print(f"Finished collecting from Bing for date {date or 'Any time'}. Total URLs found: {len(image_urls)}")
    return list(image_urls)[:limit]

# Pomocnicza funkcja do uzyskania ostatniego dnia miesiąca
def last_day_of_month(year, month):
    if month == 12:
        return date(year, month, 31)
    return date(year, month + 1, 1) - timedelta(days=1)

# 🔁 Główna pętla - Teraz dla Binga z filtrowaniem losowego dnia z miesiąca (ostatnie 12 miesięcy)
for category, query in QUERIES.items():
    print(f"\nProcessing category: '{category}' with query: '{query}' (Target: {TOTAL_IMAGES_PER_CATEGORY} in total from last 12 months)")

    # Określ początkowy offset na podstawie istniejących plików
    SAVE_DIR = f"images_{category}"
    os.makedirs(SAVE_DIR, exist_ok=True)
    existing_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".jpg")]
    total_saved_for_category = len(existing_files)
    print(f"Starting with {total_saved_for_category} existing images for '{category}'.")

    # Ustal 12 losowych dat, po jednej z każdego z ostatnich 12 miesięcy
    dates_to_process = []
    today = date.today()
    current_year = today.year
    current_month = today.month

    for i in range(12):
        # Get the first day of the current month being considered
        first_day = date(current_year, current_month, 1)
        # Get the last day of the current month being considered
        last_day = last_day_of_month(current_year, current_month)

        # Pick a random day between first_day and last_day
        days_in_month = (last_day - first_day).days + 1
        random_day_offset = random.randrange(days_in_month)
        random_date_in_month = first_day + timedelta(days=random_day_offset)

        dates_to_process.append(random_date_in_month.strftime('%Y-%m-%d'))

        # Move to the previous month
        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1
    
    # Możesz opcjonalnie posortować daty, jeśli chcesz przetwarzać od najstarszych do najnowszych
    # dates_to_process.sort()

    for single_date_str in dates_to_process:
        print(f"\n--- Przetwarzanie daty: {single_date_str} (losowy dzień z miesiąca) dla kategorii '{category}' ---")

        # Sprawdź, czy osiągnięto docelową liczbę obrazów dla tej kategorii
        if total_saved_for_category >= TOTAL_IMAGES_PER_CATEGORY:
            print(f"Reached target of {TOTAL_IMAGES_PER_CATEGORY} images for category '{category}'. Skipping remaining dates.")
            break

        # Oblicz ile jeszcze obrazów potrzebujemy do osiągnięcia TOTAL_IMAGES_PER_CATEGORY
        remaining_limit = TOTAL_IMAGES_PER_CATEGORY - total_saved_for_category
        print(f"Need {remaining_limit} more images for category '{category}'.")

        # 1. Collect images from Bing for the specific date
        # Przekazujemy pozostały limit jako ograniczenie dla bieżącej daty/miesiąca
        bing_links = collect_bing_images(query, remaining_limit, date=single_date_str)
        print(f"Collected {len(bing_links)} links from Bing for date {single_date_str}.")

        if bing_links:
            # 2. Download the collected Bing images
            # Używamy aktualnej całkowitej liczby zapisanych obrazów jako offsetu
            bing_saved_count = download_images(bing_links, category, offset=total_saved_for_category)
            total_saved_for_category += bing_saved_count # Zaktualizuj całkowitą liczbę zapisanych obrazów
            print(f"Successfully downloaded {bing_saved_count} images from Bing for category '{category}' and date {single_date_str}. Total saved so far: {total_saved_for_category}")
        else:
            print(f"No new images collected for category '{category}' on date {single_date_str}.")

    print(f"\n✅ Zakończono przetwarzanie kategorii '{category}'. Całkowita liczba zapisanych obrazów (z Binga w losowych dniach z ostatnich 12 miesięcy): {total_saved_for_category}/{TOTAL_IMAGES_PER_CATEGORY}")

# Sterownik Selenium jest używany tylko przez funkcję Bing,
# więc driver.quit() nadal musi być na końcu.
driver.quit()
print("\n✅ Gotowe! Przetwarzanie zakończone (tylko Bing z filtrowaniem losowego dnia z miesiąca).")
