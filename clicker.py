import time
import random
import os
import io
import requests

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image # Zachowujemy import Image, bo jest potrzebny do wczytywania obrazu z requestsa

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager

# === Ścieżka do modelu i konfiguracja modelu ===
# Upewnij się, że model_wlosy_best.pt znajduje się w tym samym katalogu co skrypt, lub podaj pełną ścieżkę
MODEL_PATH = "model_wlosy_best.pt"
CLASS_NAMES = ["black", "blonde", "brunette", "redhead"] # Nazwy klas z modelu
# Średnie i odchylenia standardowe użyte do normalizacji (z predict_image.py)
NORM_MEAN = [0.5, 0.5, 0.5]
NORM_STD = [0.5, 0.5, 0.5]

# Transformacje obrazu (musi być takie samo jak przy trenowaniu)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD)
])

# === SPRAWDZENIE DOSTĘPNOŚCI GPU ===
# Workaround dla OMP: Error #15 (z predict_image.py)
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

if not torch.cuda.is_available():
    print("BŁĄD: CUDA nie jest dostępne. Ten skrypt wymaga akceleracji GPU do działania modelu predykcyjnego.")
    print("Upewnij się, że masz poprawnie zainstalowane PyTorch z obsługą CUDA i kompatybilny sterownik GPU.")
    exit()

device = torch.device("cuda")
print(f"Pomyślnie skonfigurowano użycie urządzenia: {device}")


# 🔧 Konfiguracja Selenium
TINDER_URL = "https://am1.badoo.com/encounters" # Adres URL Badoo
SWIPES_LIMIT = 100
MIN_DELAY = 1.5
MAX_DELAY = 3.5

# Selektory (na podstawie wcześniejszych ustaleń i dostarczonego HTML Badoo)
# Selektor obszaru przycisków Like/Nope (używany do czekania na gotowość strony)
TOOLBAR_SELECTOR = "div.profile-card-full__actions"



# Selektor dla elementu, na którym będziemy emulować swipe (TWÓJ POPRAWNY SELEKTOR!)
SWIPE_ELEMENT_SELECTOR = "div.user-section-photo" # <<< TUTAJ JEST TWÓJ SELEKTOR!
SWIPE_OFFSET_PIXELS = 300 # <<< Określ, o ile pikseli w prawo przeciągnąć (doświadczalnie)
SWIPE_LEFT_OFFSET_PIXELS = -300 # <<< Określ, o ile pikseli w lewo przeciągnąć (doświadczalnie)


# Selektor dla elementu(ów) ZDJĘCIA PROFILOWEGO na Badoo
# MUSISZ ZIDENTYFIKOWAĆ I WSTAWIC POPRAWNY SELEKTOR DLA ELEMENTU IMG LUB INNEGO ZAWIERAJĄCEGO ZDJĘCIE
IMAGE_ELEMENT_SELECTOR = "img[data-qa='multimedia-image']" # <<< Używamy selektora opartego na data-qa


# 🔧 Opcje przeglądarki Firefox
# Zdefiniuj ścieżkę do katalogu profilu Firefox (WSTAW SWOJĄ POPRAWNĄ ŚCIEŻKĘ!)
firefox_profile_path = r'C:\Users\adria\AppData\Roaming\Mozilla\Firefox\Profiles\et7jvk0s.Swiper'

options = FirefoxOptions()
options.add_argument("--window-size=1920x1080")

# Wskaż opcję użycia konkretnego profilu
options.add_argument(f"-profile")
options.add_argument(firefox_profile_path)

# Ustawienia preferencji dla lokalizacji
options.set_preference("geo.prompt.testing", True)
options.set_preference("geo.prompt.testing.allow", True)

# options.add_argument("--headless") # Możesz odkomentować po debugowaniu, jeśli nie potrzebujesz widzieć okna
options.page_load_strategy = 'normal'

# Użyj GeckoDriverManager do zarządzania sterownikiem GeckoDriver dla Firefoxa
service = Service(GeckoDriverManager().install())

# Uruchom przeglądarkę Firefox
driver = webdriver.Firefox(service=service, options=options)

# --- ZAŁADUJ SWÓJ MODEL TUTAJ ---
print("⏳ Ładowanie modelu predykcyjnego...")
try:
    # <<< KOD DO ŁADOWANIA MODELU Z predict_image.py >>>
    model = models.resnet18(pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    # map_location=device zapewnia wczytanie na skonfigurowane urządzenie (GPU)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device) # Przenieś model na GPU
    model.eval() # Ustaw model w tryb ewaluacji (ważne dla predykcji)
    # --------------------------------------------------
    print("✅ Model załadowany pomyślnie na GPU.")
except FileNotFoundError:
    print(f"❌ Błąd: Plik modelu '{MODEL_PATH}' nie został znaleziony.")
    print("Upewnij się, że plik modelu znajduje się w tym samym katalogu co skrypt lub podaj pełną ścieżkę.")
    driver.quit()
    exit()
except Exception as e:
    print(f"❌ Błąd podczas ładowania modelu: {e}")
    driver.quit()
    exit()
# ----------------------------------


# 🌐 Wejdź na Badoo
driver.get(TINDER_URL)

# Informacja o logowaniu...
print("ℹ️ Skrypt używa zapisanego profilu Firefox.")
print("Jeśli Badoo wymaga logowania, zrób to ręcznie w oknie przeglądarki.")
print("Po zalogowaniu, wróć tutaj i naciśnij ENTER, aby kontynuować.")
input("▶️ ENTER po sprawdzeniu/zalogowaniu...")


# ✅ Czekaj na pasek narzędzi (co sugeruje załadowanie profilu)
try:
    # Czekaj na widoczność obszaru przycisków Like/Nope (jako sygnał gotowości strony)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, TOOLBAR_SELECTOR))
    )
    print("✅ Pasek narzędzi z przyciskami Like/Nope widoczny. Rozpoczynanie symulacji swipe'owania...")

    swiped_count = 0

    while swiped_count < SWIPES_LIMIT:
        try:
            print(f"🔬 Analizowanie profilu {swiped_count + 1}/{SWIPES_LIMIT}...")

            # --- Czekanie na pojawienie się ELEMENTU DO SWIPE'A (profilu) ---
            # Czekaj na widoczność elementu, na którym będziemy wykonywać gest swipe
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, SWIPE_ELEMENT_SELECTOR))
            )
            print("✅ Element do swipe'a widoczny i gotowy.")
             # --- Czekanie na pojawienie się ZDJĘCIA PROFILOWEGO ---
             # Czekaj na obecność elementu zdjęcia profilowego, aby mieć pewność, że zdjęcie jest w DOM
            WebDriverWait(driver, 10).until(
                  EC.presence_of_element_located((By.CSS_SELECTOR, IMAGE_ELEMENT_SELECTOR)) # <<< Używamy nowego selektora
            )
            print("✅ Zdjęcie profilowe obecne i gotowe.")
            # --------------------------------------------------------

            # --- MIEJSCE NA OBSŁUGĘ POTENCJALNYCH POPUPÓW / NAKŁADEK ---
            # Jeśli na zrzucie ekranu (debug_screenshot.png, który możesz wygenerować ręcznie) widać popupy lub elementy
            # zasłaniające przyciski Like/Nope/obszar swipe'owalny, tutaj należy dodać logikę do ich zamknięcia.
            # Przykłady w komentarzach poniżej:
            # try:
            #    close_button = driver.find_element(By.CSS_SELECTOR, "selektor_przycisku_zamkniecia_popupu")
            #    if close_button.is_displayed():
            #        close_button.click()
            #        print("ℹ️ Zamknięto popup.")
            #        time.sleep(1) # Krótka pauza po zamknięciu
            # except NoSuchElementException:
            #    pass # Nie ma popupu lub nie znaleziono przycisku zamknięcia
            # except Exception as popup_e:
            #    print(f"⚠️ Błąd podczas zamykania popupu: {popup_e}")


            # Inny przykład: naciśnięcie klawisza ESC, co często zamyka popupy
            # try:
            #    body = driver.find_element(By.TAG_NAME, 'body') # Możesz potrzebować znaleźć element body jeśli go nie masz
            #    body.send_keys(Keys.ESCAPE)
            #    print("ℹ️ Naciśnięto ESC (próba zamknięcia popupu).")
            #    time.sleep(1)
            # except NoSuchElementException:
            #    pass
            # except Exception as esc_e:
            #     print(f"⚠️ Błąd podczas wysyłania ESC: {esc_e}")
            # ------------------------------------------------------------


            # --- POBIERZ ZDJĘCIA PROFILU I URUCHOM PREDYKCJĘ ---
            print("🖼️ Pobieram URL-e zdjęć profilu...")
            image_urls = []
            try:
                # Znajdź WSZYSTKIE elementy zdjęć profilu na stronie (często jest ich kilka)
                # Używamy POPRAWNEGO SELEKTORA ZDJĘCIA - UZUPEŁNIJ GO NA GÓRZE SKRYPTU!
                image_elements = driver.find_elements(By.CSS_SELECTOR, IMAGE_ELEMENT_SELECTOR)

                for img_element in image_elements:
                    # Upewnij się, że element ma atrybut 'src' i że URL nie jest pusty
                    src = img_element.get_attribute("src")
                    # Badoo może używać leniwego ładowania (lazy loading) i URL może być w innym atrybucie, np. data-src
                    if not src or not src.startswith("http"):
                         src = img_element.get_attribute("data-src")
                         # Sprawdź też inne atrybuty, np. style='background-image: url(...)'
                         if not src or not src.startswith("http"):
                             style = img_element.get_attribute("style")
                             if style and "background-image" in style:
                                 # Wydobądź URL z atrybutu style="background-image: url(...)"
                                 import re
                                 match = re.search(r'url\("?(.*?)"?\)', style)
                                 if match:
                                     src = match.group(1)


                    if src and src.startswith("http"): # Sprawdź, czy to prawidłowy URL obrazu
                         image_urls.append(src)

                if not image_urls:
                     print("⚠️ Nie znaleziono URL-i zdjęć profilu dla selektora:", IMAGE_ELEMENT_SELECTOR, ". Pomiń profil.")
                     continue # Pomiń ten profil i przejdź do następnego

                print(f"✅ Znaleziono {len(image_urls)} URL-i zdjęć: {image_urls}")

                # --- URUCHOMIENIE PREDYKCJI DLA KAŻDEGO ZDJĘCIA ---
                predicted_classes = []
                with torch.no_grad(): # Wyłącz gradienty na czas predykcji (oszczędność pamięci/czasu)
                    for url in image_urls:
                        try:
                            # Pobierz obraz z URL-a
                            response = requests.get(url, stream=True)
                            response.raise_for_status() # Rzuć wyjątek dla złych kodów statusu (4xx lub 5xx)
                            response.raw.decode_content = True # Dekompresuj gzip/deflate

                            # Otwórz obraz za pomocą Pillow z danych w pamięci
                            # Użyj io.BytesIO do czytania z bajtów w pamięci
                            image = Image.open(io.BytesIO(response.content)).convert("RGB")

                            # Przetwórz obraz
                            input_tensor = transform(image).unsqueeze(0).to(device) # Dodaj wymiar batcha i przenieś na GPU

                            # Wywołaj predykcję modelu
                            outputs = model(input_tensor)
                            _, predicted_tensor = torch.max(outputs, 1)
                            predicted_class_idx = predicted_tensor.item() # Przenieś wynik na CPU i pobierz wartość skalara

                            # Mapowanie indeksu na nazwę klasy
                            if 0 <= predicted_class_idx < len(CLASS_NAMES):
                                predicted_class = CLASS_NAMES[predicted_class_idx]
                                print(f"   -> Predykcja dla {url[:50]}...: {predicted_class.upper()}") # Wypisz fragment URL
                                predicted_classes.append(predicted_class)
                            else:
                                print(f"   -> Warning: Predicted class index ({predicted_class_idx}) out of bounds for {url[:50]}...")
                                predicted_classes.append("unknown") # Dodaj "unknown" jeśli indeks poza zakresem

                        except Exception as pred_e:
                             print(f"   -> ⚠️ Błąd podczas przetwarzania zdjęcia lub predykcji dla {url[:50]}...: {pred_e}")
                             predicted_classes.append("error") # Zapisz błąd jako wynik

                # --- LOGIKA DECYZYJNA ---
                # Decyzja: swipe w prawo jeśli CO NAJMNIEJ JEDNO zdjęcie zostało sklasyfikowane jako "brunette"
                final_prediction_is_brunette = "brunette" in predicted_classes
                print(f"➡️ Finalna predykcja dla profilu: Brunette: {final_prediction_is_brunette}")

            except NoSuchElementException: # Obsłuż błąd jeśli selektor zdjęć nie działa
                 print(f"⚠️ NoSuchElementException: Nie znaleziono elementu(ów) zdjęcia profilowego dla selektora ({IMAGE_ELEMENT_SELECTOR}). Pomiń profil.")
                 continue # Pomiń ten profil i przejdź do następnego
            except Exception as photo_e: # Obsłuż inne błędy podczas pobierania URL-i zdjęć lub predykcji
                 print(f"⚠️ Błąd podczas pobierania URL-i zdjęć lub predykcji: {photo_e}. Pomiń profil.")
                 continue # Pomiń ten profil i przejdź do następnego


            # --- AKCJA: Symulujemy swipe w oparciu o predykcję ---
            # Znajdź element, na którym będziemy wykonywać swipe (czekaliśmy na niego wcześniej)
            try:
                swipe_element = driver.find_element(By.CSS_SELECTOR, SWIPE_ELEMENT_SELECTOR)
                actions = ActionChains(driver) # Utwórz obiekt ActionChains

                if final_prediction_is_brunette:
                    print(f"❤️ Predykcja: Brunetka. Symuluję swipe w prawo o {SWIPE_OFFSET_PIXELS} pikseli.")
                    # Wykonaj gest drag_and_drop_by_offset na znalezionym elemencie w prawo
                    actions.drag_and_drop_by_offset(swipe_element, SWIPE_OFFSET_PIXELS, 0).perform() # 0 dla osi Y
                else:
                    print(f"👎 Predykcja: Nie-Brunetka. Symuluję swipe w lewo o {abs(SWIPE_LEFT_OFFSET_PIXELS)} pikseli.")
                    # Wykonaj gest drag_and_drop_by_offset na znalezionym elemencie w lewo
                    actions.drag_and_drop_by_offset(swipe_element, SWIPE_LEFT_OFFSET_PIXELS, 0).perform() # Ujemna wartość dla lewej
                # -------------------------------------------------

            except NoSuchElementException:
                print(f"⚠️ NoSuchElementException: Element do swipe'a ({SWIPE_ELEMENT_SELECTOR}) nie został znaleziony tuż przed akcją. Pomiń profil.")
                # To nie powinno się zdarzyć, jeśli czekaliśmy na niego wcześniej, ale jako fallback.
                continue
            except Exception as action_e:
                 print(f"⚠️ Błąd podczas wykonywania gestu swipe: {action_e}. Pomiń profil.")
                 continue # Pomiń ten profil w razie błędu swipe

            
            swiped_count += 1
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"⏳ Czekanie {delay:.2f} sekundy przed kolejnym swipe'em...")
            time.sleep(delay)

        except NoSuchElementException as e: # Obsługa błędu NoSuchElement w pętli (powinien być przechwycony wcześniej, ale jako fallback)
             print(f"⚠️ NoSuchElementException (w pętli głównej): Element nie znaleziono podczas przetwarzania ({e}). Możliwa zmiana strony lub problem z ładowaniem.")
             print("⌛ Chwila przerwy, próba kontynuacji...")
             time.sleep(5)
             continue
        except TimeoutException: # Obsługa błędu Timeout podczas czekania na elementy w pętli
             print(f"⚠️ TimeoutException: Oczekiwanie na element minęło w pętli. Możliwy problem z ładowaniem kolejnego profilu lub popupy blokujące.")
             print("💡 Spróbuj dodać logikę zamykania popupów/nakładek w sekcji 'MIEJSCE NA OBSŁUGĘ POTENCJALNYCH POPUPÓW'.")
             print("⌛ Chwila przerwy, próba kontynuacji...")
             time.sleep(5)
             continue
        except Exception as e:
            print(f"⚠️ Wystąpił inny błąd podczas przetwarzania profilu lub symulacji swipe'a w pętli głównej: {e}")
            if "badoo.com" not in driver.current_url:
                 print("🛑 Opuściliśmy Badoo. Kończę.")
                 break
            print("⌛ Chwila przerwy, możliwe okno/popup lub inny problem...")
            time.sleep(5)
            continue

except TimeoutException:
    print("❌ Nie załadowano profilu – możliwe że nie jesteś zalogowany w profilu Firefox, lub problem z połączeniem.")
    print("Sprawdź stan przeglądarki.")

finally:
    print(f"\n✅ Zakończono: wykonano {swiped_count if 'swiped_count' in locals() else 0}/{SWIPES_LIMIT} swipe'ów.")
    # driver.quit()  # Odkomentuj, jeśli chcesz zamknąć przeglądarkę po zakończeniu
