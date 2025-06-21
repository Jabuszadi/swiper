import time
import random
import os
import io
import requests
import argparse
import re

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

# === DODANO: Parsowanie argumentów wiersza poleceń ===
parser = argparse.ArgumentParser(description="Skrypt do automatycznego swipe'owania na Badoo/Tinder z klasyfikacją koloru włosów.")
parser.add_argument(
    '--preferred-hair-colors',
    nargs='*', # Pozwala na zero lub więcej argumentów po --preferred-hair-colors
    default=[], # Domyślnie pusta lista
    help='Lista nazw kolorów włosów (np. Blond Black Red) które mają powodować Swipe Right.'
)
args = parser.parse_args()

# Pobierz listę preferowanych kolorów z argumentów
PREFERRED_HAIR_COLORS = [color.lower() for color in args.preferred_hair_colors] # Konwertuj na małe litery dla spójności
print(f"✨ Skonfigurowane preferowane kolory włosów do Swipe Right: {PREFERRED_HAIR_COLORS}")
# =======================================================


# === Ścieżka do modelu i konfiguracja modelu ===
# Upewnij się, że model_wlosy_best.pt znajduje się w tym samym katalogu co skrypt, lub podaj pełną ścieżkę
MODEL_PATH = "model_wlosy_best.pt"
CLASS_NAMES = ["black", "blonde", "brunette", "redhead"] # Nazwy klas z modelu (pamiętaj o spójności z modelem i preferencjami)
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
TINDER_URL = "https://tinder.com/app/recs" # Adres URL Tindera
SWIPES_LIMIT = 100
MIN_DELAY = 1.5
MAX_DELAY = 3.5

# Selektory (na podstawie wcześniejszych ustaleń i dostarczonego HTML Badoo)
# Selektor obszaru przycisków Like/Nope (używany do czekania na gotowość strony)
TOOLBAR_SELECTOR = "div.recsToolbar"



# Selektor dla elementu, na którym będziemy emulować swipe (TWÓJ POPRAWNY SELEKTOR!)
SWIPE_ELEMENT_SELECTOR = "div.StretchedBox" # <<< TUTAJ JEST TWÓJ SELEKTOR!
SWIPE_OFFSET_PIXELS = 300 # <<< Określ, o ile pikseli w prawo przeciągnąć (doświadczalnie)
SWIPE_LEFT_OFFSET_PIXELS = -300 # <<< Określ, o ile pikseli w lewo przeciągnąć (doświadczalnie)


# Selektor dla elementu(ów) ZDJĘCIA PROFILOWEGO na Badoo
# MUSISZ ZIDENTYFIKOWAĆ I WSTAWIC POPRAWNY SELEKTOR DLA ELEMENTU IMG LUB INNEGO ZAWIERAJACEGO ZDJECIE
IMAGE_ELEMENT_SELECTOR = "div.StretchedBox" # <<< Używamy selektora opartego na data-qa


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

actions = ActionChains(driver)

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
input("▶️ ENTER po sprawdzeniu/zalogowaniu...")


# ✅ Czekaj na pasek narzędzi (co sugeruje załadowanie profilu)
# Główny blok try dla całej interakcji z Badoo
try:
    # Czekaj na widoczność obszaru przycisków Like/Nope (jako sygnał gotowości strony)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, TOOLBAR_SELECTOR))
    )
    print("✅ Pasek narzędzi z przyciskami Like/Nope widoczny. Rozpoczynanie symulacji swipe'owania...")

    swiped_count = 0 # Zmienna inicjalizowana w głównym bloku try

    # Główna pętla do swipe'owania profili
    while swiped_count < SWIPES_LIMIT:
        
            print(f"\n--- Analizowanie profilu {swiped_count + 1}/{SWIPES_LIMIT} ---") # DODANO: Wyraźne oddzielenie profili

            #  --- Czekanie na pojawienie się ELEMENTU DO SWIPE'A (profilu) i ZDJĘCIA PROFILOWEGO ---
            # Zagnieżdżony blok try/except dla czekania na kluczowe elementy
            try:
                # Czekaj na widoczność elementu, na którym będziemy wykonywać gest swipe
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, SWIPE_ELEMENT_SELECTOR))
                )
                print("✅ Element do swipe'a widoczny i gotowy.")
                 # Czekaj na obecność elementu zdjęcia profilowego
                WebDriverWait(driver, 10).until(
                      EC.presence_of_element_located((By.CSS_SELECTOR, IMAGE_ELEMENT_SELECTOR)) # <<< Używamy nowego selektora
                )
                print("✅ Zdjęcie profilowe obecne i gotowe.")
            except TimeoutException:
                print(f"⚠️ TimeoutException: Nie załadowano elementu do swipe'a lub zdjęcia. Pomiń profil.")
                swiped_count += 1 # Zwiększ licznik nawet jeśli wystąpi błąd przy ładowaniu elementów
                continue # Pomiń ten profil i przejdź do następnego
            except NoSuchElementException:
                 print(f"⚠️ NoSuchElementException: Nie znaleziono elementu do swipe'a lub zdjęcia. Pomiń profil.")
                 swiped_count += 1 # Zwiększ licznik nawet jeśli wystąpi błąd przy ładowaniu elementów
                 continue # Pomiń ten profil i przejdź do następnego
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


            # --- POBIERZ ZDJĘCIA PROFILU I URUCHOM PREDYKCJE ---
            print("🖼️ Pobieram URL-e zdjęć profilu...")
            image_urls = []
            try:
                # Znajdź WSZYSTKIE elementy zdjęć profilu na stronie (często jest ich kilka)
                # Używamy POPRAWNEGO SELEKTORA ZDJĘCIA - UZUPEŁNIJ GO NA GÓRZE SKRYPTU!
                image_elements = driver.find_elements(By.CSS_SELECTOR, IMAGE_ELEMENT_SELECTOR)

                for img_element in image_elements:
                    # Upewnij się, że element ma atrybut 'src' i że URL nie jest pusty
                    src = img_element.get_attribute("style")
                    # Badoo może używać leniwego ładowania (lazy loading) i URL może być w innym atrybucie, np. data-src
                    if not src or not src.startswith("http"):
                         src = img_element.get_attribute("style")
                         # Sprawdź też inne atrybuty, np. style='background-image: url(...)'
                         if not src or not src.startswith("http"):
                             style = img_element.get_attribute("style")
                             if style and "background-image" in style:
                                 # Wydobądź URL z atrybutu style="background-image: url(...)"
                                 match = re.search(r'url\("?(.*?)"?\)', style)
                                 if match:
                                     src = match.group(1)


                    if src and src.startswith("http"): # Sprawdź, czy to prawidłowy URL obrazu
                         image_urls.append(src)

                if not image_urls:
                     print("⚠️ Nie znaleziono URL-i zdjęć profilu dla selektora:", IMAGE_ELEMENT_SELECTOR, ". Pomiń profil.")
                     swiped_count += 1 # Zwiększ licznik, jeśli nie ma zdjęć
                     continue # Pomiń ten profil i przejdź do następnego

                print(f"✅ Znaleziono {len(image_urls)} URL-i zdjęć: {image_urls}")

                # --- URUCHOMIENIE PREDYKCJI DLA KAŻDEGO ZDJĘCIA ---
                # Zbieramy top predykcje (lowercase) dla każdego zdjęcia
                top_predicted_classes_for_profile = []
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
                                top_predicted_classes_for_profile.append(predicted_class.lower()) # DODANO: Zapisz top predykcję (lowercase)
                            else:
                                print(f"   -> Warning: Predicted class index ({predicted_class_idx}) out of bounds for {url[:50]}...")
                                # top_predicted_classes_for_profile.append("unknown") # Opcjonalnie dodaj "unknown"
                                pass # Nie dodajemy "unknown" do listy

                        except Exception as pred_e:
                             print(f"   -> ⚠️ Błąd podczas przetwarzania zdjęcia lub predykcji dla {url[:50]}...: {pred_e}")
                             # top_predicted_classes_for_profile.append("error") # Opcjonalnie dodaj "error"
                             pass # Nie dodajemy "error" do listy


                # --- ZMODYFIKOWANA LOGIKA DECYZYJNA (Majority Rule) ---
                # Decyzja: swipe w prawo jeżeli WIĘKSZOŚĆ (powyżej 50%) predykcji dla zdjęć profilu
                # znajduje się na liście preferowanych kolorów włosów

                total_predictions = len(top_predicted_classes_for_profile)
                preferred_color_count = 0

                if total_predictions > 0:
                    # Count how many predictions are in the preferred list
                    for predicted_color in top_predicted_classes_for_profile:
                        if predicted_color in PREFERRED_HAIR_COLORS:
                            preferred_color_count += 1

                    # Determine if preferred colors are the majority
                    should_swipe_right = preferred_color_count > total_predictions / 2
                    print(f"🔬 Analiza predykcji: Całkowita liczba predykcji zdjęć: {total_predictions}, Predykcji pasujących do preferowanych kolorów: {preferred_color_count}")
                else:
                    # No predictions were made
                    should_swipe_right = False
                    print("🔬 Analiza predykcji: Brak udanych predykcji koloru włosów dla tego profilu.")


                # DODANO: Logowanie informacji o predykcji i preferencjach dla bieżącego profilu
                print(f"➡️ Logika decyzji Swipe: Preferowane kolory do Swipe Right: {PREFERRED_HAIR_COLORS}, Decyzja: {'Swipe Right' if should_swipe_right else 'Swipe Left'}")


                if should_swipe_right:
                    # Find which preferred colors were detected (for logging)
                    detected_preferred = [c for c in top_predicted_classes_for_profile if c in PREFERRED_HAIR_COLORS]
                    # Usun duplikaty dla czytelności w logu
                    unique_detected_preferred = []
                    [unique_detected_preferred.append(item) for item in detected_preferred if item not in unique_detected_preferred]

                    print(f"❤️ Wykonuję Swipe Right. Wykryto preferowany kolor włosów w większości ({preferred_color_count}/{total_predictions}) zdjęć ({', '.join(unique_detected_preferred) if unique_detected_preferred else 'N/A'}).")
                else:
                    # Find which preferred colors *could* have been detected but weren't majority (for logging)
                    detected_non_preferred = [c for c in top_predicted_classes_for_profile if c not in PREFERRED_HAIR_COLORS]
                    # Usun duplikaty
                    unique_detected_non_preferred = []
                    [unique_detected_non_preferred.append(item) for item in detected_non_preferred if item not in unique_detected_non_preferred]
                    detected_preferred_minority = [c for c in top_predicted_classes_for_profile if c in PREFERRED_HAIR_COLORS]
                     # Usun duplikaty
                    unique_detected_preferred_minority = []
                    [unique_detected_preferred_minority.append(item) for item in detected_preferred_minority if item not in unique_detected_preferred_minority]


                    print(f"👎 Wykonuję Swipe Left. Wykryty preferowany kolor włosów ({', '.join(unique_detected_preferred_minority)}) nie stanowi większości predykcji ({preferred_color_count}/{total_predictions}). Dominujące kolory (niepreferowane): {', '.join(unique_detected_non_preferred) if unique_detected_non_preferred else 'N/A'}.")
                # ---------------------------------------

                # --- WYKONAJ AKCJĘ SWIPE NA PODSTAWIE DECYZJI ---
                # Upewnij się, że element do wysyłania klawiszy jest aktywny i widoczny
                try:
                    # Ponownie znajdujemy element, aby upewnić się, że jest aktualny po ewentualnym załadowaniu nowego profilu
                    target_element = WebDriverWait(driver, 5).until(
                         EC.visibility_of_element_located((By.CSS_SELECTOR, SWIPE_ELEMENT_SELECTOR))
                    )
                    # Alternatywnie można spróbować wysłać klawisze do elementu body, jeśli wysyłanie do swipe_element nie działa
                    # target_element = driver.find_element(By.TAG_NAME, 'body')

                except TimeoutException:
                    print(f"⚠️ TimeoutException: Element docelowy dla klawiszy ({SWIPE_ELEMENT_SELECTOR}) nie był widoczny. Pomiń profil.")
                    swiped_count += 1 # Zwiększ licznik w przypadku błędu
                    continue
                except NoSuchElementException:
                     print(f"⚠️ NoSuchElementException: Element docelowy dla klawiszy ({SWIPE_ELEMENT_SELECTOR}) nie znaleziono. Pomiń profil.")
                     swiped_count += 1 # Zwiększ licznik w przypadku błędu
                     continue


                if should_swipe_right:
                    print("➡️ Wykonuję Swipe Right (klawisz strzałki w prawo)...")
                    # Wyślij klawisz strzałki w prawo do elementu
                    actions.send_keys(Keys.ARROW_RIGHT).perform()
                    print("✅ Swipe Right wykonany.") # Dodano log potwierdzający
                else:
                    print("⬅️ Wykonuję Swipe Left (klawisz strzałki w lewo)...")
                    # Wyślij klawisz strzałki w lewo do elementu
                    actions.send_keys(Keys.ARROW_LEFT).perform()
                    print("✅ Swipe Left wykonany.") # Dodano log potwierdzający

                # ------------------------------------------------

                # ZWIĘKSZ LICZNIK SWIPE'ÓW I ZACZEKAJ (po udanym swipe)
                swiped_count += 1 # Zwiększ licznik tylko po udanym wykonaniu swipe'a
                print(f"✅ Wykonano swipe: {swiped_count}/{SWIPES_LIMIT}")
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"⏳ Czekam {delay:.2f} sekundy przed następnym profilem...")
                time.sleep(delay)

            # Obsługa wyjątków wewnątrz pętli while (poza zagnieżdżonym try/except dla czekania)
            except NoSuchElementException as e: # Jeśli element zniknie *po* wstępnym czekaniu, ale przed swipe'em
                 print(f"⚠️ NoSuchElementException (w pętli głównej): Element nie znaleziono podczas przetwarzania ({e}). Możliwa zmiana strony lub problem z ładowaniem.")
                 print("⌛ Chwila przerwy, próba kontynuacji...")
                 time.sleep(5)
                 swiped_count += 1 # Zwiększ licznik, nawet jeśli wystąpi błąd
                 continue # Spróbuj następny profil
            except TimeoutException as e: # Jeśli coś trwa za długo *po* wstępnym czekaniu
                 print(f"⚠️ TimeoutException: Oczekiwanie na element minęło w pętli. Możliwy problem z ładowaniem kolejnego profilu lub popupy blokujące.")
                 print("💡 Spróbuj dodać logikę zamykania popupów/nakładek w sekcji 'MIEJSCE NA OBSŁUGĘ POTENCJALNYCH POPUPOW'.")
                 print("⌛ Chwila przerwy, próba kontynuacji...")
                 time.sleep(5)
                 swiped_count += 1 # Zwiększ licznik, nawet jeśli wystąpi timeout
                 continue # Spróbuj następny profil
            except Exception as e: # Inne błędy wewnątrz pętli
                print(f"⚠️ Wystąpił inny błąd podczas przetwarzania profilu lub symulacji swipe'a w pętli głównej: {e}")
                if "badoo.com" not in driver.current_url:
                     print("🛑 Opuściliśmy Badoo. Kończę.")
                     break # Wyjście z pętli while, jeśli opuściliśmy Badoo
                print("⌛ Chwila przerwy, możliwe okno/popup lub inny problem...")
                time.sleep(5)
                swiped_count += 1 # Zwiększ licznik, nawet jeśli wystąpi błąd ogólny
                continue # Spróbuj następny profil

# Ten blok except obsługuje TimeoutException z PRED PĘTLĄ WHILE (przy pierwszym ładowaniu strony)
except TimeoutException:
    print("❌ Nie załadowano profilu – możliwe że nie jesteś zalogowany w profilu Firefox, lub problem z połączeniem.")
    print("Sprawdź stan przeglądarki.")

# Ten blok finally wykonuje się zawsze po zakończeniu głównego bloku try (lub obsłudze wyjątku)
finally:
    # swiped_count może nie być zainicjalizowane, jeśli główny try blok zawiódł od razu
    print(f"\n✅ Zakończono: wykonano {swiped_count if 'swiped_count' in locals() else 0}/{SWIPES_LIMIT} swipe'ów.")
    # driver.quit()  # Odkomentuj, jeśli chcesz zamknąć przeglądarkę po zakończeniu
