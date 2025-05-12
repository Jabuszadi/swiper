# Oryginalne importy i kod z zaznaczenia
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions # Zmieniono nazwę, aby uniknąć konfliktu z lokalną zmienną 'options'
from selenium.webdriver.chrome.service import Service

# Użycie ChromeOptions zamiast Options, aby uniknąć potencjalnego konfliktu nazw, jeśli 'options' jest też zmienną
options = ChromeOptions()
# Usunięto opcje profilu użytkownika, aby uruchomić niezależną instancję Chrome
options.add_argument(r"user-data-dir=C:\Users\adria\AppData\Local\Google\Chrome\User Data") # Ścieżka do folderu User Data
options.add_argument(r"profile-directory=Profile 8") # Zmień XX na faktyczną nazwę nowego folderu profilu (np. Profile 8)
options.add_argument("--disable-gpu") # Wyłączenie akceleracji GPU
options.add_experimental_option("detach", True)  # <- to zapobiega zamknięciu Chrome po zakończeniu skryptu
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('--remote-debugging-pipe')
options.add_argument('--no-sandbox')
options.add_argument('--remote-debugging-port=9222')


# Zdefiniuj ścieżkę do chromedrivera (upewnij się, że jest POPRAWNA)
chromedriver_path = r'C:\WebDriver\chromedriver.exe'

# Utwórz obiekt Service z podaną ścieżką i włącz szczegółowe logowanie
service = Service(chromedriver_path, service_args=['--verbose'])

print("Navigating..")

driver = webdriver.Chrome(service = webdriver.ChromeService(executable_path=chromedriver_path), options=options)

print("...")

url="https://www.facebook.com"
driver.get(url)
