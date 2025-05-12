from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions # Używamy FirefoxOptions
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager # Dla Firefoxa używamy GeckoDriver i GeckoDriverManager

# Zdefiniuj ścieżkę do katalogu profilu Firefox (WSTAW SWOJĄ POPRAWNĄ ŚCIEŻKĘ!)
firefox_profile_path = r'C:\Users\adria\AppData\Roaming\Mozilla\Firefox\Profiles\et7jvk0s.Swiper' # <<< ZAMIEŃ NA ŚCIEŻKĘ Z about:profiles

# Utwórz obiekt FirefoxOptions
options = FirefoxOptions()

# Wskaż opcję użycia konkretnego profilu
# W Selenium dla Firefoxa używa się argumentu "profile" i podaje ścieżkę do katalogu profilu
options.add_argument(f"-profile")
options.add_argument(firefox_profile_path)


# Użyj GeckoDriverManager do zarządzania sterownikiem GeckoDriver dla Firefoxa
service = Service(GeckoDriverManager().install())

# Uruchom przeglądarkę Firefox z zadanymi opcjami
driver = webdriver.Firefox(service=service, options=options)

# Teraz możesz nawigować i logować się, a sesja zostanie zapamiętana w tym profilu
url = "https://www.tinder.com" # lub inna strona wymagająca logowania
driver.get(url)

# Po zalogowaniu, sesja zostanie zapisana w profilu, a kolejne uruchomienia skryptu
# używające tego samego profilu będą już zalogowane.