import asyncio
import json
import os
import shutil
# from aiohttp import ClientSession, ClientTimeout # Te importy nie są już potrzebne w skrypcie Selenium
# from urllib.parse import urlparse, urlencode # Ten import jest potrzebny, ale był już w oryginalnym kodzie
# from playwright.async_api import async_playwright # Te importy nie są już potrzebne w skrypcie Selenium
# from playwright.sync_api import sync_playwright # Ten import nie jest już potrzebny w skrypcie Selenium

from selenium import webdriver
# Potrzebujemy importu dla FirefoxProfile
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
# Potrzebujemy importu dla FirefoxOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
import os
import json
from urllib.request import *
import sys
import time
from selenium.webdriver.common.by import By # Potrzebne do WebDriverWait
from selenium.webdriver.support.ui import WebDriverWait # Potrzebne do czekania
from selenium.webdriver.support import expected_conditions as EC # Potrzebne do warunków czekania
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException # Obsługa wyjątków

# adding path to geckodriver to the OS environment variable
# os.environ["PATH"] += os.pathsep + os.getcwd() # Ta linia może być zbędna, jeśli używasz webdriver_manager
download_path = "dataset/"

# Define the queries and max images per query - USERS' QUERIES
QUERIES = {
    "blonde": "woman with blonde hair",
    "brunette": "woman with brown hair",
    "black": "woman with black hair",
    "redhead": "woman with red hair",
    "asian_people": "asian people",
    "black_people": "black people",
    "white_people": "white people"
}
MAX_IMAGES_PER_QUERY = 100 # Ustaw maksymalną liczbę obrazów do pobrania na zapytanie

# Ścieżka do profilu Firefoxa podana przez użytkownika
firefox_profile_path = r'C:\Users\adria\AppData\Roaming\Mozilla\Firefox\Profiles\et7jvk0s.Swiper'

# *** ZMIENIONY SELEKTOR DLA MINIATUR ***
# Selektor dla miniatury, którą klikamy, aby otworzyć podgląd
THUMBNAIL_SELECTOR = "h3.ob5Hkd" # Używamy selektora podanego przez użytkownika

# *** ZMIENIONY SELEKTOR DLA OBRAZU W PODGLĄDZIE ***
# Selektor dla obrazu w pełnym rozmiarze w panelu podglądu
# Używamy selektora opartego na jsname z fragmentu HTML
FULL_IMAGE_SELECTOR = "img[jsname='kn3ccd']" # Selektor dla tagu img z atrybutem jsname='kn3ccd'

# Selektor przycisku zamknięcia podglądu (opcjonalnie, można też użyć klawisza ESCAPE)
# CLOSE_BUTTON_SELECTOR = "button[aria-label='Zamknij']" # Przykład, może być inny


def main():
    # Usunięcie parsowania argumentów z linii poleceń
    # searchtext = sys.argv[1]
    # num_requested = int(sys.argv[2])

    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    extensions = {"jpg", "jpeg", "png", "gif"}

    # Sprawdź, czy podany profil Firefox istnieje
    if not os.path.exists(firefox_profile_path):
        print(f"Błąd: Podana ścieżka profilu Firefoxa nie istnieje: {firefox_profile_path}")
        print("Upewnij się, że ścieżka jest prawidłowa i profil istnieje.")
        return # Zakończ działanie skryptu, jeśli profil nie istnieje


    # Iteracja przez zapytania ze słownika QUERIES
    for class_name, query_text in QUERIES.items():
        num_requested = MAX_IMAGES_PER_QUERY # Używamy stałej dla każdego zapytania
        fixed_number_of_scrolls = 10 # Stała liczba przewinięć - Zwiększamy do 10, aby mieć pewność, że co najmniej 10 obrazów się załaduje


        # Utworzenie katalogu dla bieżącej klasy/zapytania
        class_download_path = os.path.join(download_path, class_name.replace(" ", "_"))
        if not os.path.exists(class_download_path):
            os.makedirs(class_download_path)
        print(f"\n--- Rozpoczynam pobieranie dla klasy '{class_name}' z zapytaniem: '{query_text}' ---")
        print(f"Utworzono katalog klasy: {class_download_path}")


        url = "https://www.google.co.in/search?q="+query_text+"&source=lnms&tbm=isch"

        # ### Użycie podanego profilu Firefoxa poprzez FirefoxOptions ###
        driver = None # Inicjalizacja driver na None
        try:
            # Tworzenie obiektu FirefoxProfile z podanej ścieżki
            profile = FirefoxProfile(firefox_profile_path)
            # Tworzenie obiektu FirefoxOptions
            options = FirefoxOptions()
            # Ustawienie profilu w opcjach
            options.profile = profile

            # Inicjalizacja sterownika Firefox z opcjami
            driver = webdriver.Firefox(options=options) # Używamy argumentu 'options'
            print(f"Uruchomiono przeglądarkę Firefox z profilem: {firefox_profile_path}")
        except Exception as e:
            print(f"Błąd podczas uruchamiania przeglądarki z profilem {firefox_profile_path}: {e}")
            print("Przechodzę do kolejnego zapytania...")
            continue # Przejdź do kolejnego zapytania, jeśli nie udało się uruchomić przeglądarki


        try: # Dodajemy blok try...except wokół operacji na przeglądarce
            driver.get(url)

            # Potrzebujemy poczekać, aż strona się załaduje i pojawi się siatka miniatur
            print(f"Czekam na pojawienie się elementu miniatury: {THUMBNAIL_SELECTOR}")
            try:
                # Czekaj na obecność, a nie widoczność, bo sam h3 może nie być widoczny, ale jego potomek tak
                WebDriverWait(driver, 15).until(
                     EC.presence_of_element_located((By.CSS_SELECTOR, THUMBNAIL_SELECTOR))
                 )
                print("Siatka miniatur załadowana (znaleziono pierwszy element).")
            except TimeoutException:
                 print(f"Błąd: Nie znaleziono elementu miniatury {THUMBNAIL_SELECTOR} w ciągu 15 sekund. Sprawdź selektor lub połączenie internetowe.")
                 driver.quit()
                 continue # Przejdź do kolejnego zapytania

            # Logika przewijania strony - ładujemy więcej miniatur
            print(f"Przewijam stronę {fixed_number_of_scrolls} razy, aby załadować więcej miniatur.")
            for _ in range(fixed_number_of_scrolls):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight)") # Przewiń do dołu
                time.sleep(2) # Czekaj dłużej po przewinięciu, żeby elementy miały czas się załadować

            # Zbieranie miniatur po przewinięciu
            # Czekamy ponownie na obecność wszystkich elementów po przewinięciu
            try:
                WebDriverWait(driver, 10).until(
                     EC.presence_of_all_elements_located((By.CSS_SELECTOR, THUMBNAIL_SELECTOR))
                )
                thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, THUMBNAIL_SELECTOR)
                print(f"Znaleziono {len(thumbnail_elements)} potencjalnych elementów miniatur do kliknięcia po przewinięciu.")
            except TimeoutException:
                 print(f"Błąd: Nie udało się zebrać elementów miniatur po przewinięciu w ciągu 10 sekund.")
                 thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, THUMBNAIL_SELECTOR) # Spróbuj pobrać co się da
                 print(f"Zebrano {len(thumbnail_elements)} elementów, mimo błędu czekania.")


            image_urls_to_download = []
            downloaded_img_count = 0

            print(f"Rozpoczynam klikanie miniatur i pobieranie obrazów (limit: {num_requested}).")

            # Pętla przez znalezione miniatury
            for i, thumbnail in enumerate(thumbnail_elements):
                if downloaded_img_count >= num_requested:
                    print(f"Osiągnięto limit {num_requested} pobranych obrazów dla tego zapytania.")
                    break # Przerywamy, jeśli osiągnięto limit

                # Przed kliknięciem, upewnij się, że element jest przewinięty do widoku i gotowy do interakcji
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", thumbnail)
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(thumbnail))
                    print(f"Miniatura {i+1} przewinięta do widoku i klikalna.")
                except Exception as e:
                    print(f"Miniatura {i+1}: Nie udało się przewinąć lub element nieklikalny: {e}. Pomijam.")
                    continue # Przejdź do następnej miniatury


                print(f"Klikam miniaturę {i+1}/{len(thumbnail_elements)}...")
                try:
                    # Kliknij miniaturę
                    # Używamy JavaScript do kliknięcia
                    driver.execute_script("arguments[0].click();", thumbnail)
                    print(f"Kliknięto miniaturę {i+1}.")


                    # Poczekaj na pojawienie się podglądu obrazu w pełnym rozmiarze
                    print(f"Czekam na pojawienie się podglądu: {FULL_IMAGE_SELECTOR}")
                    # Czekamy na widoczność, bo podgląd powinien być widoczny
                    full_image_element = WebDriverWait(driver, 10).until(
                         EC.visibility_of_element_located((By.CSS_SELECTOR, FULL_IMAGE_SELECTOR))
                    )
                    print("Podgląd obrazu w pełnym rozmiarze załadowany.")

                    # Wyodrębnij URL obrazu w pełnym rozmiarze (najczęściej z atrybutu 'src')
                    img_url = full_image_element.get_attribute('src')

                    if img_url and img_url.startswith('http'):
                        # Mamy URL obrazu, teraz go pobieramy
                        if img_url not in image_urls_to_download: # Sprawdź duplikaty przed pobraniem
                            print(f"Wyodrębniono URL: {img_url[:50]}...") # Skrócony URL do logu

                            img_type = "jpg" # Domyślny
                            try:
                                # Spróbuj wywnioskować typ obrazu z URL
                                parsed_url = urlparse(img_url)
                                path = parsed_url.path
                                ext = os.path.splitext(path)[1][1:] # Pobierz rozszerzenie bez kropki
                                if ext and ext.lower() in extensions:
                                    img_type = ext.lower()
                                elif '.png' in img_url.lower():
                                    img_type = 'png'
                                elif '.gif' in img_url.lower():
                                    img_type = 'gif'
                                elif '.jpeg' in img_url.lower():
                                     img_type = 'jpeg'
                                else:
                                    img_type = "jpg"

                                req = Request(img_url, headers=headers)
                                raw_img = urlopen(req).read()

                                file_name = f"{class_name.replace(' ', '_')}_{downloaded_img_count+1}.{img_type}"
                                file_path = os.path.join(class_download_path, file_name)

                                with open(file_path, "wb") as f:
                                    f.write(raw_img)

                                print(f"Pobrano: {file_path}")
                                image_urls_to_download.append(img_url) # Dodaj URL do listy pobranych, żeby unikać duplikatów
                                downloaded_img_count += 1 # Zliczamy tylko udane pobrania

                            except Exception as e:
                                print (f"Pobieranie nieudane dla {img_url}: {e}")

                        # else:
                            # print(f"URL obrazu już pobrany (duplikat): {img_url[:50]}...")


                    else:
                        print("Wyodrębniony URL nie jest prawidłowym URL HTTP.")


                    # Zamknij podgląd obrazu
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE) # Naciśnij ESCAPE na ciele strony
                    print("Naciśnięto ESCAPE, aby zamknąć podgląd.")

                    # Krótka pauza po zamknięciu podglądu
                    time.sleep(1) # Zwiększono pauzę, żeby strona miała czas wrócić do stanu sprzed podglądu


                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                    print (f"Błąd podczas przetwarzania miniatury {i+1} (kliknięcie/ładowanie podglądu): {e}")
                    print("Próbuję nacisnąć ESCAPE i przejść do następnej miniatury.")
                    # Jeśli wystąpi błąd podczas klikania lub czekania na podgląd/znajdowania elementu
                    try:
                         driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                         time.sleep(1) # Zwiększono pauzę
                    except Exception:
                         pass # Ignoruj błędy podczas próby naciśnięcia ESCAPE
                    continue # Przejdź do następnej miniatury
                except Exception as e:
                     print(f"Wystąpił nieoczekiwany błąd podczas przetwarzania miniatury {i+1}: {e}")
                     # Podobnie jak wyżej, spróbuj zamknąć ewentualne nakładki
                     try:
                         driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                         time.sleep(1) # Zwiększono pauzę
                     except Exception:
                         pass
                     continue


            print(f"--- Zakończono proces zbierania obrazów dla klasy '{class_name}'. Zebrano {downloaded_img_count} obrazów. ---")

        except Exception as e:
            print(f"Wystąpił błąd podczas scrape'owania dla zapytania '{query_text}': {e}")
        finally:
             # Zamykamy przeglądarkę po zakończeniu pobierania dla bieżącego zapytania, niezależnie od błędów
            if driver:
                driver.quit()
                print(f"Przeglądarka zamknięta dla zapytania '{query_text}'.")


    print("\n--- Zakończono proces pobierania dla wszystkich zapytań ---")


if __name__ == "__main__":
	main()