import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # Import Keys
from selenium.webdriver.firefox.service import Service # Changed for Firefox
from selenium.webdriver.firefox.options import Options as FirefoxOptions # Changed for Firefox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager # Changed for Firefox

# 🔧 Konfiguracja
TINDER_URL = "https://tinder.com/app/recs"
SWIPES_LIMIT = 100
MIN_DELAY = 1.5
MAX_DELAY = 3.5

# Zmieniono selektor do oczekiwania na pasek narzędzi ze skrótami klawiszowymi
# BUTTON_NOPE_SELECTOR = "button[aria-label='Nie']" # Keep if needed for other actions or waits
# BUTTON_LIKE_SELECTOR = "button[aria-label='Lubię']" # Not needed for key press
# profile_element_selector = "[data-testid='profileCard__image']" # Nie używamy już tego selektora do początkowego oczekiwania
TOOLBAR_SELECTOR = "div.recsToolbar" # <<< NOWY SELEKTOR DLA PASKA NARZĘDZI
# Selectors for waiting for buttons to be available, even if we use keys
BUTTON_NOPE_SELECTOR_FOR_WAIT = "button[aria-label='Nope']"
BUTTON_LIKE_SELECTOR_FOR_WAIT = "button[aria-label='Like']"


# 🔧 Opcje przeglądarki Firefox
# Zdefiniuj ścieżkę do katalogu profilu Firefox (WSTAW SWOJĄ POPRAWNĄ ŚCIEŻKĘ!)
firefox_profile_path = r'C:\Users\adria\AppData\Roaming\Mozilla\Firefox\Profiles\et7jvk0s.Swiper' # <<< ZAMIEŃ NA ŚCIEŻKĘ Z about:profiles

options = FirefoxOptions()
options.add_argument("--window-size=1920x1080") # Można spróbować, ale Firefox może inaczej obsługiwać rozmiar okna

# Wskaż opcję użycia konkretnego profilu
options.add_argument(f"-profile")
options.add_argument(firefox_profile_path)

# Ustawienia preferencji dla lokalizacji
options.set_preference("geo.prompt.testing", True)
options.set_preference("geo.prompt.testing.allow", True)
# Poniższa opcja może być potrzebna, jeśli chcesz na stałe zezwolić na lokalizację dla danej strony
# options.set_preference("geo.provider.network.url", "data:application/json,{\"location\": {\"lat\": 52.2297, \"lng\": 21.0122}, \"accuracy\": 100.0}") # Przykładowe koordynaty (Warszawa)


# options.add_argument("--headless")  # Dla Firefoxa, jeśli chcesz tryb headless
options.page_load_strategy = 'normal'

# Użyj GeckoDriverManager do zarządzania sterownikiem GeckoDriver dla Firefoxa
service = Service(GeckoDriverManager().install())

# Uruchom przeglądarkę Firefox z zadanymi opcjami
driver = webdriver.Firefox(service=service, options=options)

# --- ZAŁADUJ SWÓJ MODEL TUTAJ ---
print("⏳ Ładowanie modelu predykcyjnego...")
try:
    # ZASTĄP PONIŻSZE LINIE KODEM DO ŁADOWANIA SWOJEGO MODELU
    # Przykład:
    # model_path = "sciezka/do/twojego/modelu.h5"
    # moj_model = nazwa_biblioteki_modelu.load_model(model_path)
    # LUB:
    # import pickle
    # with open('sciezka/do/twojego/modelu.pkl', 'rb') as f:
    #     moj_model = pickle.load(f)
    moj_model = "ZAŁADOWANY_OBIEKT_MODELU" # <-- Zastąp to faktycznym obiektem modelu po załadowaniu
    print("✅ Model załadowany pomyślnie.")
except Exception as e:
    print(f"❌ Błąd podczas ładowania modelu: {e}")
    # Rozważ zakończenie skryptu, jeśli model nie działa
    # driver.quit()
    # exit()
# ----------------------------------


# 🌐 Wejdź na Tinder
driver.get(TINDER_URL)

# Informacja o logowaniu, jeśli profil nie jest zalogowany
print("ℹ️ Skrypt używa zapisanego profilu Firefox.")
print("Jeśli Tinder wymaga logowania, zrób to ręcznie w oknie przeglądarki.")
print("Po zalogowaniu, wróć tutaj i naciśnij ENTER, aby kontynuować swipe'owanie.")
input("▶️ ENTER po sprawdzeniu/zalogowaniu...")

# --- DODANE LINIE DO DIAGNOSTYKI ---
print("🌐 Sprawdzanie aktualnego URL:")
print(driver.current_url)

print("📸 Robienie zrzutu ekranu (screenshot)...")
try:
    driver.save_screenshot("debug_screenshot.png")
    print("✅ Zrzut ekranu zapisany jako debug_screenshot.png")
except Exception as e:
    print(f"⚠️ Nie udało się zapisać zrzutu ekranu: {e}")

print("📄 Pobieranie kodu źródłowego strony (page source)...")
try:
    page_source = driver.page_source
    with open("debug_page_source.html", "w", encoding="utf-8") as f:
        f.write(page_source)
    print("✅ Kod źródłowy strony zapisany jako debug_page_source.html")
except Exception as e:
    print(f"⚠️ Nie udało się pobrać kodu źródłowego: {e}")
# --- KONIEC DODANYCH LINII ---


# ✅ Czekaj na pasek narzędzi (co sugeruje załadowanie profilu)
try:
    # Zmieniono oczekiwanie z obecności na WIDOCZNOŚĆ paska narzędzi
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, TOOLBAR_SELECTOR))
    )
    print("✅ Pasek narzędzi widoczny. Rozpoczynanie swipe'owania...")

    swiped_count = 0
    body_element = driver.find_element(By.TAG_NAME, 'body') # Get body element once

    while swiped_count < SWIPES_LIMIT:
        try:
            print(f"🔬 Analizowanie profilu {swiped_count + 1}/{SWIPES_LIMIT}...")

            # --- POBIERZ ZDJĘCIA PROFILU I URUCHOM PREDYKCJĘ ---
            # ZASTĄP PONIŻSZY KOD LOGIKĄ POBIERANIA ZDJĘĆ I WYWOŁANIA SWOJEGO MODELU
            
            # Przykład: Znajdź pierwszy element obrazu profilu (może być potrzebny inny selektor)
            # profile_image_element = WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "selector_do_zdjecia_profilowego")) # <-- ZMIEŃ NA POPRAWNY SELEKTOR!
            # )
            # image_url = profile_image_element.get_attribute("src")

            # # Przykład: Uruchom predykcję na podstawie URL lub pobranego obrazu
            # # prediction_result = moj_model.predict(image_url) # Jeśli model akceptuje URL
            # # LUB:
            # # image_data = pobierz_zdjecie_z_url(image_url) # Funkcja do zaimplementowania
            # # prediction_result = moj_model.predict(image_data) # Jeśli model akceptuje dane obrazu

            # # Symulowany wynik predykcji dla przykładu
            # is_brunette = random.choice([True, False]) # <-- ZASTĄP TO FAKTYCZNYM WYNIKIEM Z MODELU
            
            # PRZYKŁAD: JAK WYGLĄDA WYNIK Z TWOJEGO MODELU?
            # Czy to string np. "Brunette"? Czy to boolean True/False?

            # Przyjmijmy, że Twój model zwraca True jeśli to Brunette, False w przeciwnym razie
            prediction_result = "WYNIK Z TWOJEGO MODELU" # <-- ZASTĄP TO FAKTYCZNYM WYWOŁANIEM MODELU
            
            is_brunette = (prediction_result == "Brunette") # <-- PRZYKŁAD: DOSTOSUJ PORÓWNANIE DO WYNIKU SWOJEGO MODELU


            if is_brunette:
                print("❤️ Predykcja: Brunetka. Swipe w prawo (klawisz ARROW_RIGHT)")
                body_element.send_keys(Keys.ARROW_RIGHT)
            else:
                print("👎 Predykcja: Nie-Brunetka. Swipe w lewo (klawisz ARROW_LEFT)")
                body_element.send_keys(Keys.ARROW_LEFT)
            # -------------------------------------------------


            swiped_count += 1
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"⏳ Czekanie {delay:.2f} sekundy przed kolejnym swipe'em...")
            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Błąd podczas swipe'owania lub predykcji: {e}")
            if "tinder.com" not in driver.current_url:
                print("🛑 Opuściliśmy Tinder. Kończę.")
                break
            print("⌛ Chwila przerwy, możliwe okno/popup lub inny problem...")
            # Dodatkowe sprawdzenie, czy nie ma jakiegoś overlay'a
            # Można tu dodać logikę zamykania popupów, jeśli są częste
            time.sleep(5) # Dłuższa przerwa na wypadek problemów
            # Spróbuj odświeżyć stronę, jeśli błędy się powtarzają
            # driver.refresh()
            # print("🔄 Próba odświeżenia strony...")
            # WebDriverWait(driver, 30).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, profile_element_selector))
            # )
            # Spróbuj ponownie znaleźć body element, jeśli strona została przeładowana lub zmieniła się struktura
            try:
                body_element = driver.find_element(By.TAG_NAME, 'body')
            except:
                print("⚠️ Nie można znaleźć elementu body po błędzie. Próbuję kontynuować...")
            continue

except TimeoutException:
    print("❌ Nie załadowano profilu – możliwe że nie jesteś zalogowany w profilu Firefox, lub problem z połączeniem.")
    print("Sprawdź stan przeglądarki.")

finally:
    print(f"\n✅ Zakończono: wykonano {swiped_count if 'swiped_count' in locals() else 0}/{SWIPES_LIMIT} swipe'ów.")
    # driver.quit()  # Odkomentuj, jeśli chcesz zamknąć przeglądarkę po zakończeniu
