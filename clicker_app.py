import gradio as gr
import subprocess
import sys
import os
from PIL import Image
import json # DODANO: Import modułu json
# import predict_image as classifier_module # Import przeniesiony do bloku try

# 🔧 Konfiguracja ścieżek do skryptów clicker (jeśli nadal ich używasz)
CLICKER_TINDER_SCRIPT = "clicker_tinder1.py"
CLICKER_SCRIPT = "clicker.py"
DOWNLOAD_SCRIPT = "download_images_old.py" # Ścieżka do skryptu pobierającego
PASSIONS_FILE = "passions_tinder.json" # DODANO: Ścieżka do pliku z pasjami
LANGUAGES_FILE = "languages_tinder.json" # DODANO: Ścieżka do pliku z językami

# --- Inicjalizacja zmiennych przed blokiem try ---
# Zapewnienie, że zmienne są zdefiniowane nawet w przypadku błędu importu lub ładowania
AVAILABLE_CLASSIFIERS = []
AVAILABLE_HAIR_COLORS = [] # Dodana zmienna na dostępne kolory włosów
available_passions = [] # DODANO: Zmienna na dostępne pasje
available_languages = [] # DODANO: Zmienna na dostępne języki
# DODANO: Listy opcji dla sekcji "Basics" (wyciągnięte z dostarczonego HTML)
ZODIAC_SIGNS = ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"]
EDUCATION_LEVELS = ["Bachelors", "In College", "High School", "PhD", "In Grad School", "Masters", "Trade School"]
CHILDREN_OPTIONS = ["I want children", "I don't want children", "I have children and want more", "I have children and don't want more", "Not sure yet"]
VACCINATION_STATUSES = ["Vaccinated", "Unvaccinated", "Prefer not to say"]
PERSONALITY_TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
COMMUNICATION_STYLES = ["Big time texter", "Phone caller", "Video chatter", "Bad texter", "Better in person"]
LOVE_LANGUAGES = ["Thoughtful gestures", "Presents", "Touch", "Compliments", "Time together"]

# DODANO: Listy opcji dla sekcji "Lifestyle" (wyciągnięte z dostarczonego HTML)
PETS_OPTIONS = ["Dog", "Cat", "Reptile", "Amphibian", "Bird", "Fish", "Don't have but love", "Other", "Turtle", "Hamster", "Rabbit", "Pet-free", "All the pets", "Want a pet", "Allergic to pets"]
DRINKING_HABITS = ["Not for me", "Sober", "Sober curious", "On special occasions", "Socially on weekends", "Most Nights"]
SMOKING_HABITS = ["Social smoker", "Smoker when drinking", "Non-smoker", "Smoker", "Trying to quit"]
WORKOUT_HABITS = ["Everyday", "Often", "Sometimes", "Never"]
DIETARY_PREFERENCES = ["Vegan", "Vegetarian", "Pescatarian", "Kosher", "Halal", "Carnivore", "Omnivore", "Other"]
SOCIAL_MEDIA_ACTIVITY = ["Influencer status", "Socially active", "Off the grid", "Passive scroller"]
SLEEPING_HABITS = ["Early bird", "Night owl", "In a spectrum"]

# DODANO: Lista opcji dla sekcji "Sexual Orientation" (wyciągnięte z dostarczonego HTML)
SEXUAL_ORIENTATIONS = ["Straight", "Gay", "Lesbian", "Bisexual", "Asexual", "Demisexual", "Pansexual", "Queer", "Questioning"]

CAN_CLASSIFY = False
model_load_status = "Model klasyfikatora nie został jeszcze wczytany." # Domyślny status
classifier_module = None # Będzie None, jeśli import się nie powiecie

# --- Sekcja do zaimportowania Twojej logiki klasyfikacji i wczytania modelu ---
# W Gradio model wczytujemy raz przy starcie serwera, poza funkcjami handlerów UI
try:
    import predict_image as classifier_module

    # Spróbuj wczytać model od razu przy starcie aplikacji Gradio
    if classifier_module:
        try:
            # Wywołaj funkcję wczytującą model z Twojego modułu
            # Upewnij się, że predict_image.py ma funkcję load_classifier_model
            classifier_module.load_classifier_model()
            model_load_status = "Model wczytany pomyślnie."
        except Exception as e:
            # Zwróć komunikat o błędzie w przypadku niepowodzenia ładowania modelu
            model_load_status = f"Błąd podczas wczytywania modelu: {e}"
            print(f"ERROR: {model_load_status}")


    # Sprawdź czy moduł klasyfikujący jest dostępny i ma potrzebną funkcję/zmienną
    # Te sprawdzenia wykonają się tylko jeśli classifier_module nie jest None
        if hasattr(classifier_module, 'AVAILABLE_CLASSIFIERS'):
             AVAILABLE_CLASSIFIERS = classifier_module.AVAILABLE_CLASSIFIERS
             if not AVAILABLE_CLASSIFIERS: # Sprawdź czy lista nie jest pusta
                 print("Warning: Lista AVAILABLE_CLASSIFIERS w predict_image.py jest pusta.")
                 # Możesz dodać ten warning do statusu modelu, jeśli chcesz wyświetlić go w UI
                 model_load_status += "\n\n**Ostrzeżenie:** Lista AVAILABLE_CLASSIFIERS w predict_image.py jest pusta."
        else:
             # Zapasowa lista, jeśli zmienna nie jest dostępna w module
             AVAILABLE_CLASSIFIERS = [
                 "Klasyfikator Koloru Włosów (Fallback)",
                 "Klasyfikator Etniczny (Fallback)"
             ]
             print("Warning: Brak zmiennej AVAILABLE_CLASSIFIERS w predict_image.py. Używam listy zastępczej.")
             model_load_status += "\n\n**Ostrzeżenie:** Brak zmiennej AVAILABLE_CLASSIFIERS. Używam listy zastępczej."

        # === DODANE: Pobierz listę dostępnych kolorów włosów ===
        if hasattr(classifier_module, 'AVAILABLE_HAIR_COLORS'):
            AVAILABLE_HAIR_COLORS = classifier_module.AVAILABLE_HAIR_COLORS
            if not AVAILABLE_HAIR_COLORS:
                 print("Warning: Lista AVAILABLE_HAIR_COLORS w predict_image.py jest pusta.")
                 # Możesz dodać ten warning do statusu modelu, jeśli chcesz wyświetlić go w UI
                 # model_load_status += "\n\n**Ostrzeżenie:** Lista AVAILABLE_HAIR_COLORS w predict_image.py jest pusta."
        else:
            # Zapasowa lista kolorów, jeśli zmienna nie jest dostępna
            AVAILABLE_HAIR_COLORS = ["Blonde", "Brunette", "Black", "Red", "Other"] # Przykładowa lista
            print("Warning: Brak zmiennej AVAILABLE_HAIR_COLORS w predict_image.py. Używam listy zastępczej.")
            # model_load_status += "\n\n**Ostrzeżenie:** Brak zmiennej AVAILABLE_HAIR_COLORS. Używam listy zastępczej."
        # =====================================================


        if hasattr(classifier_module, 'classify_image_with_models'):
             CAN_CLASSIFY = True
        else:
             print("""
                 ERROR: Nie znaleziono funkcji `classify_image_with_models(pil_image, selected_classifiers)`
                 w module `predict_image.py`.
             """)
             model_load_status = "Błąd: Funkcja classify_image_with_models brakująca w predict_image.py."
             CAN_CLASSIFY = False
    else:
         # Ten else dotyczy przypadku, gdy import classifier_module się nie powiódł
         model_load_status = "Błąd: Moduł predict_image.py nie został zaimportowany."


except ImportError:
    model_load_status = f"""
        **Błąd Importu:** Nie można zaimportować skryptu `predict_image.py`.
        Upewnij się, że plik `predict_image.py` znajduje się w tym samym katalogu
        co `{os.path.basename(__file__)}` i że został poprawnie przeorganizowany (bez kodu na najwyższym poziomie
        wykonującego operacje takie jak ładowanie modeli/obrazów, wyświetlanie wykresów).
    """
    print(model_load_status)
    # Tutaj zmienne AVAILABLE_CLASSIFIERS, CAN_CLASSIFY i model_load_status zachowają swoje wartości domyślne
except Exception as e:
    model_load_status = f"Wystąpił nieoczekiwany błąd podczas ładowania logiki klasyfikacji: {e}"
    print(f"ERROR: {model_load_status}")
    # Tutaj zmienne AVAILABLE_CLASSIFIERS, CAN_CLASSIFY i model_load_status zachowają swoje wartości domyślne

# --- Koniec sekcji importu i ładowania modelu ---

# --- DODANE: Wczytaj pasje z pliku JSON przy starcie aplikacji ---
try:
    if os.path.exists(PASSIONS_FILE):
        with open(PASSIONS_FILE, 'r', encoding='utf-8') as f:
            available_passions = json.load(f)
            print(f"Wczytano {len(available_passions)} pasji z pliku {PASSIONS_FILE}")
    else:
        print(f"Warning: Plik {PASSIONS_FILE} nie znaleziony. Pasje nie będą dostępne.")
        available_passions = [] # Ustaw pustą listę, jeśli plik nie istnieje
except Exception as e:
    print(f"ERROR: Wystąpił błąd podczas wczytywania pasji z {PASSIONS_FILE}: {e}")
    available_passions = [] # Ustaw pustą listę w przypadku błędu

# --- Koniec sekcji wczytywania pasji ---

# --- DODANE: Wczytaj języki z pliku JSON przy starcie aplikacji ---
try:
    if os.path.exists(LANGUAGES_FILE):
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            available_languages = json.load(f)
            print(f"Wczytano {len(available_languages)} języków z pliku {LANGUAGES_FILE}")
    else:
        print(f"Warning: Plik {LANGUAGES_FILE} nie znaleziony. Języki nie będą dostępne.")
        available_languages = [] # Ustaw pustą listę, jeśli plik nie istnieje
except Exception as e:
    print(f"ERROR: Wystąpił błąd podczas wczytywania języków z {LANGUAGES_FILE}: {e}")
    available_languages = [] # Ustaw pustą listę w przypadku błędu

# --- Koniec sekcji wczytywania języków ---


# --- Funkcja klasyfikująca dla Gradio ---
# Ta funkcja będzie wywoływana, gdy użytkownik kliknie przycisk
def classify_image(
    pil_image: Image.Image | None,
    selected_classifiers: list[str]
) -> str: # Zwraca wyniki klasyfikacji (str)
    """
    Handles image classification using the loaded module and formats results for Gradio.
    Takes a PIL Image and selected classifiers.
    Returns a formatted string (Markdown) of the classification results.
    """
    # Sprawdź, czy klasyfikacja jest w ogóle możliwa na podstawie statusu ładowania modelu
    if not CAN_CLASSIFY or "Błąd" in model_load_status:
         # Zwróć informację o błędzie ładowania modelu jako wynik klasyfikacji
         return f"Klasyfikacja niemożliwa: {model_load_status}"

    if pil_image is None:
        return "Proszę najpierw przesłać obraz."
    if not selected_classifiers:
        return "Proszę wybrać co najmniej jeden klasyfikator."

    classification_results = {}
    try:
        # === WYWOŁAJ FUNKCJĘ KLASYFIKUJĄCĄ Z TWOJEGO predict_image.py ===
        # Sprawdź, czy classifier_module i funkcja są dostępne przed wywołaniem (dodatkowa ostrożność)
        if classifier_module and hasattr(classifier_module, 'classify_image_with_models'):
             classification_results = classifier_module.classify_image_with_models(pil_image, selected_classifiers)
        else:
             # Ten przypadek nie powinien wystąpić, jeśli CAN_CLASSIFY jest False, ale dodane dla pewności
             return "Error: Logika klasyfikacji niedostępna (moduł niezaimportowany lub funkcja brakująca)."

    except Exception as e:
        # Zwróć błąd klasyfikacji
        return f"Wystąpił błąd podczas klasyfikacji: {e}"


    # --- Przetwarzanie wyników ---
    formatted_results = "### Szczegółowe Wyniki Klasyfikacji:\n"

    if classification_results: # Upewnij się, że są jakieś wyniki do wyświetlenia
        for classifier_name, results in classification_results.items():
            formatted_results += f"**{classifier_name}:**\n"
            if isinstance(results, dict):
                # Sortowanie wyników słownikowych dla czytelności (np. wg prawdopodobieństwa malejąco)
                sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)
                for key, value in sorted_results:
                     # Upewnij się, że wartość jest liczbą przed formatowaniem
                     if isinstance(value, (int, float)):
                         formatted_results += f"- {key}: {value:.4f}\n"
                     else:
                         formatted_results += f"- {key}: {value}\n" # Wyświetl jako tekst jeśli nie liczba
            else:
                formatted_results += f"{results}\n" # Wyświetl jako tekst/string jeśli nie słownik
                formatted_results += "\n" # Dodaj pustą linię po wynikach klasyfikacji

    else:
         formatted_results += "Klasyfikacja nie zwróciła żadnych wyników."

    # Zwróć sformatowane wyniki
    return formatted_results


# --- Funkcja pomocnicza do wyświetlania informacji o obrazie ---
def display_image_info(pil_image: Image.Image | None) -> str:
    """Takes a PIL Image or None and returns a string with image dimensions or empty string."""
    if pil_image is None:
        return "" # Zwróć pusty string, gdy nie ma obrazu
    try:
        return f"Rozmiar obrazu: {pil_image.size[0]}x{pil_image.size[1]}"
    except Exception:
        return "Nie można odczytać rozmiaru obrazu."


# --- ZMODYFIKOWANA Funkcja pomocnicza do uruchamiania skryptów clicker ---
# Funkcja teraz przyjmuje wszystkie wybrane preferencje
def run_script_ui(
    script_name: str,
    preferred_hair_colors: list[str],
    preferred_passions: list[str],
    height_range: tuple[float, float] | None,
    relationship_goal: list[str] | None,
    preferred_languages: list[str] | None,
    preferred_zodiacs: list[str] | None,
    preferred_education: list[str] | None,
    preferred_children: list[str] | None,
    preferred_vaccination: list[str] | None,
    preferred_personality: list[str] | None,
    preferred_communication: list[str] | None,
    preferred_love_languages: list[str] | None,
    preferred_pets: list[str] | None,
    preferred_drinking: list[str] | None,
    preferred_smoking: list[str] | None,
    preferred_workout: list[str] | None,
    preferred_diet: list[str] | None,
    preferred_social_media: list[str] | None,
    preferred_sleeping: list[str] | None,
    preferred_orientations: list[str] | None
) -> str:
    """Uruchamia dany skrypt z argumentami w osobnym procesie."""
    script_path = ""
    if script_name == "Clicker Tinder":
        script_path = CLICKER_TINDER_SCRIPT
    elif script_name == "Zwykły Clicker":
        script_path = CLICKER_SCRIPT
    else:
        return f"Nieznany skrypt: {script_name}"

    # Ścieżka do interpretera Pythona
    command = [sys.executable, script_path]
    output_message = "" # DODANO: Zmienna do zbierania komunikatów

    # === DODAJEMY PREFEROWANE KOLORY JAKO ARGUMENTY ===
    if preferred_hair_colors:
         command.append("--preferred-hair-colors")
         command.extend(preferred_hair_colors) # Dodaj każdy kolor jako osobny argument
    # =================================================

       # === DODAJEMY ZAKRES WZROSTU JAKO ARGUMENTY ===
    # Sprawdź, czy zakres wzrostu został podany (Slider zwraca tuple, jeśli interactive=True)
    if height_range is not None and len(height_range) == 2:
        min_h, max_h = height_range
        # Gradio Slider z interactive=True zawsze zwróci tuple,
        # ale domyślny zakres może być (min_value, max_value).
        # Możesz dodać logikę, aby nie przekazywać argumentu, jeśli wybrano pełny zakres,
        # ale prostsze jest zawsze przekazywanie wybranej wartości.
        command.extend(["--height-range", str(int(min_h)), str(int(max_h))]) # Dodaj min i max jako osobne argumenty
    # ============================================


    # === DODAJEMY PREFEROWANE PASJE JAKO ARGUMENTY ===
    if preferred_passions:
        command.append("--preferred-passions")
        command.extend(preferred_passions) # Dodaj każdą pasję jako osobny argument
    # ===============================================

    # === DODAJEMY CEL ZWIĄZKU JAKO ARGUMENT ===
    # Dodaj argument tylko jeśli cele związku są wybrane
    if relationship_goal: # ZMIENIONO: Sprawdź, czy lista nie jest pusta
        command.append("--relationship-goal")
        command.extend(relationship_goal) # DODANO: Dodaj każdy wybrany cel jako osobny argument
    # ========================================

    # === DODAJEMY PREFEROWANE JĘZYKI JAKO ARGUMENTY ===
    # Dodaj argument tylko jeśli języki są wybrane
    if preferred_languages: # DODANO: Sprawdź, czy lista nie jest pusta
        command.append("--preferred-languages")
        command.extend(preferred_languages) # DODANO: Dodaj każdy wybrany język jako osobny argument
    # ==============================================

    # === DODAJEMY PREFEROWANE ZNAKI ZODIAKU JAKO ARGUMENTY === # DODANO
    if preferred_zodiacs:
        command.append("--preferred-zodiacs")
        command.extend(preferred_zodiacs)
    # ====================================================== # DODANO

    # === DODAJEMY PREFEROWANE POZIOMY EDUKACJI JAKO ARGUMENTY === # DODANO
    if preferred_education:
        command.append("--preferred-education")
        command.extend(preferred_education)
    # ======================================================== # DODANO

    # === DODAJEMY PREFERENCJE DOTYCZĄCE DZIECI JAKO ARGUMENTY === # DODANO
    if preferred_children:
        command.append("--preferred-children")
        command.extend(preferred_children)
    # ======================================================== # DODANO

    # === DODAJEMY PREFEROWANY STATUS SZCZEPIENIA JAKO ARGUMENTY === # DODANO
    if preferred_vaccination:
        command.append("--preferred-vaccination")
        command.extend(preferred_vaccination)
    # ========================================================== # DODANO

    # === DODAJEMY PREFEROWANE TYPY OSOBOWOŚCI JAKO ARGUMENTY === # DODANO
    if preferred_personality:
        command.append("--preferred-personality")
        command.extend(preferred_personality)
    # ======================================================= # DODANO

    # === DODAJEMY PREFEROWANE STYLE KOMUNIKACJI JAKO ARGUMENTY === # DODANO
    if preferred_communication:
        command.append("--preferred-communication")
        command.extend(preferred_communication)
    # ========================================================= # DODANO

    # === DODAJEMY PREFEROWANE JĘZYKI MIŁOŚCI JAKO ARGUMENTY === # DODANO
    if preferred_love_languages:
        command.append("--preferred-love-languages")
        command.extend(preferred_love_languages)
    # ======================================================= # DODANO

    # === DODAJEMY PREFERENCJE DOTYCZĄCE ZWIERZĄT JAKO ARGUMENTY === # DODANO
    if preferred_pets:
        command.append("--preferred-pets")
        command.extend(preferred_pets)
    # ========================================================== # DODANO

    # === DODAJEMY PREFEROWANE NAWYKI PICIA JAKO ARGUMENTY === # DODANO
    if preferred_drinking:
        command.append("--preferred-drinking")
        command.extend(preferred_drinking)
    # ====================================================== # DODANO

    # === DODAJEMY PREFEROWANE NAWYKI PALENIA JAKO ARGUMENTY === # DODANO
    if preferred_smoking:
        command.append("--preferred-smoking")
        command.extend(preferred_smoking)
    # ====================================================== # DODANO

    # === DODAJEMY PREFEROWANE NAWYKI ĆWICZEŃ JAKO ARGUMENTY === # DODANO
    if preferred_workout:
        command.append("--preferred-workout")
        command.extend(preferred_workout)
    # ====================================================== # DODANO

    # === DODAJEMY PREFEROWANE PREFERENCJE DIETETYCZNE JAKO ARGUMENTY === # DODANO
    if preferred_diet:
        command.append("--preferred-diet")
        command.extend(preferred_diet)
    # =============================================================== # DODANO

    # === DODAJEMY PREFEROWANĄ AKTYWNOŚĆ W MEDIACH SPOŁECZNOŚCIOWYCH JAKO ARGUMENTY === # DODANO
    if preferred_social_media:
        command.append("--preferred-social-media")
        command.extend(preferred_social_media)
    # =========================================================================== # DODANO

    # === DODAJEMY PREFEROWANE NAWYKI SPANIA JAKO ARGUMENTY === # DODANO
    if preferred_sleeping:
        command.append("--preferred-sleeping")
        command.extend(preferred_sleeping)
    # ====================================================== # DODANO

    # === DODAJEMY PREFEROWANE ORIENTACJE SEKSUALNE JAKO ARGUMENTY === # ZMODYFIKOWANO
    # Sprawdź i ogranicz liczbę wybranych orientacji do 3, jeśli wybrano więcej
    limited_orientations = preferred_orientations
    if preferred_orientations and len(preferred_orientations) > 3:
        limited_orientations = preferred_orientations[:3]
        output_message += "Uwaga: Wybrano więcej niż 3 orientacje seksualne. Zastosowano tylko pierwsze 3.\n" # DODANO komunikat
        print("Warning: Selected more than 3 sexual orientations. Using only the first 3.") # DODANO print w konsoli

    if limited_orientations:
        command.append("--preferred-orientations")
        command.extend(limited_orientations) # Użyj ograniczonej listy
    # =========================================================== # ZMODYFIKOWANO


    st_info_msg = f"Próbuję uruchomić polecenie: {' '.join(command)}..."
    print(st_info_msg) # Wyświetl w konsoli serwera Gradio


    try:
        # Używamy subprocess.Popen do uruchomienia w tle
        # Wyjście skryptu (print, błędy) pojawi się w konsoli terminala, z której uruchomiono Gradio
        process = subprocess.Popen(command, cwd='.')
        # Zwróć status uruchomienia skryptu i ewentualne komunikaty
        return f"{output_message}Skrypt **{os.path.basename(script_path)}** uruchomiony w tle (PID: {process.pid}). Wyjście w konsoli serwera Gradio." # DODANO output_message
    except FileNotFoundError:
        return f"{output_message}Błąd: Nie znaleziono pliku skryptu: **{script_path}**. Upewnij się, że ścieżka jest poprawna." # DODANO output_message
    except Exception as e:
        return f"{output_message}Wystąpił błąd podczas uruchamiania skryptu **{script_path}**: {e}" # DODANO output_message


# --- Definicja Interfejsu Gradio (przy użyciu Blocks dla większej elastyczności) ---
with gr.Blocks(title="Aplikacja do Klasyfikacji Obrazów") as demo:
    gr.Markdown("# Aplikacja do Klasyfikacji Obrazów")

    # Wyświetl status wczytania modelu
    model_status_md = gr.Markdown(f"Status wczytania modelu: {model_load_status}")


    gr.Markdown("---") # Dodaj separator przed tabami
    gr.Markdown("### Konfiguracja i Uruchomienie Skryptów Clicker")


    # --- Przeniesiono Taby dla skryptów clicker na górę ---
    with gr.Tabs() as clicker_tabs:
        with gr.TabItem("Clicker Tinder"):
             gr.Markdown("### Preferencje dla Clicker Tinder")
             gr.Markdown("Wybierz kryteria, które mają spowodować akcję **Swipe Right** dla skryptu **Clicker Tinder**.")

             # Komponent do wyboru preferowanych kolorów dla Clicker Tinder
             if AVAILABLE_HAIR_COLORS:
                  preferred_hair_colors_tinder = gr.CheckboxGroup(
                       choices=AVAILABLE_HAIR_COLORS, # Lista opcji z predict_image.py
                       label="Preferowane kolory włosów:",
                       value=[] # Domyślnie nic nie jest wybrane
                  )
             else:
                  gr.Warning("Brak dostępnych kolorów włosów do konfiguracji akcji swipe dla Clicker Tinder.")
                  preferred_hair_colors_tinder = gr.CheckboxGroup(
                       choices=[],
                       label="Brak dostępnych kolorów do konfiguracji akcji swipe:",
                       value=[],
                       interactive=False
                  )

             gr.Markdown("---") # Dodaj separator
             # === Komponent do wyboru preferowanych pasji dla Clicker Tinder (Dropdown z domyślnymi wartościami) ===
             # Lista pasji jest teraz wczytywana z pliku passions.json
             # Użyjemy available_passions w choices
             preferred_passions_tinder = gr.Dropdown(
                  choices=available_passions, # ZMIENIONO: Użyj listy wczytanej z JSON
                  label="Preferowane pasje:",
                  multiselect=True, # Włącz wielokrotny wybór z funkcją wyszukiwania/filtrowania
                  value=["Coffee", "Museums", "Gamer", "Spirituality"] # Domyślne wybrane pasje
             )
             # ================================================================

             gr.Markdown("---") # Dodaj separator
             # === DODANE: Komponent do wyboru zakresu wzrostu dla Clicker Tinder (Slider) ===
             preferred_height_range_tinder = gr.Slider(
                 minimum=140, # Minimalny wzrost (cm)
                 maximum=220, # Maksymalny wzrost (cm)
                 value=(150, 200), # Domyślny zakres (cm)
                 step=1, # Krok suwaka (cm)
                 label="Preferowany zakres wzrostu (cm):",
                 interactive=True # Umożliwia wybór zakresu
             )
             # ==========================================================================

             gr.Markdown("---") # Dodaj separator
             # === ZMIENIONO: Komponent do wyboru celu związku dla Clicker Tinder (CheckboxGroup) ===
             # Opcje wyciągnięte z dostarczonego HTML
             relationship_goals_tinder = gr.CheckboxGroup( # ZMIENIONO: gr.Radio na gr.CheckboxGroup
                 choices=[
                     "Long-term partner",
                     "Long-term, open to short",
                     "Short-term, open to long",
                     "Short-term fun",
                     "New friends",
                     "Still figuring it out"
                 ],
                 label="Preferowane cele związku:", # ZMIENIONO: Etykieta na "Preferowane cele związku:"
                 value=[], # ZMIENIONO: Domyślnie pusta lista (nic nie jest wybrane)
                 interactive=True
             )
             # ========================================================================

             gr.Markdown("---") # Dodaj separator
             # === DODANE: Komponent do wyboru preferowanych języków dla Clicker Tinder (Dropdown z wyszukiwaniem) ===
             # Lista języków jest teraz wczytywana z pliku languages.json
             # Użyjemy available_languages w choices
             preferred_languages_tinder = gr.Dropdown(
                  choices=available_languages, # Użyj listy wczytanej z JSON
                  label="Preferowane języki:",
                  multiselect=True, # Włącz wielokrotny wybór z funkcją wyszukiwania/filtrowania
                  value=["English"] # ZMIENIONO: Domyślnie zaznacz "English"
             )
             # ================================================================================

             gr.Markdown("---") # Dodaj separator
             gr.Markdown("### Podstawowe Informacje (Basics)") # DODANO: Tytuł sekcji Basics

             # === DODANE: Komponenty dla sekcji Basics (CheckboxGroup dla każdego) ===
             preferred_zodiac_tinder = gr.CheckboxGroup(
                 choices=ZODIAC_SIGNS,
                 label="Preferowane znaki zodiaku:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_education_tinder = gr.CheckboxGroup(
                 choices=EDUCATION_LEVELS,
                 label="Preferowany poziom edukacji:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_children_tinder = gr.CheckboxGroup(
                 choices=CHILDREN_OPTIONS,
                 label="Preferencje dotyczące dzieci:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_vaccination_tinder = gr.CheckboxGroup(
                 choices=VACCINATION_STATUSES,
                 label="Preferowany status szczepienia:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_personality_tinder = gr.CheckboxGroup(
                 choices=PERSONALITY_TYPES,
                 label="Preferowany typ osobowości:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_communication_tinder = gr.CheckboxGroup(
                 choices=COMMUNICATION_STYLES,
                 label="Preferowany styl komunikacji:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_love_languages_tinder = gr.CheckboxGroup(
                 choices=LOVE_LANGUAGES,
                 label="Preferowane języki miłości:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             # ========================================================================

             gr.Markdown("---") # Dodaj separator
             gr.Markdown("### Styl Życia (Lifestyle)") # DODANO: Tytuł sekcji Lifestyle

             # === DODANE: Komponenty dla sekcji Lifestyle (CheckboxGroup dla każdego) ===
             preferred_pets_tinder = gr.CheckboxGroup(
                 choices=PETS_OPTIONS,
                 label="Preferencje dotyczące zwierząt:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_drinking_tinder = gr.CheckboxGroup(
                 choices=DRINKING_HABITS,
                 label="Preferowane nawyki picia:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_smoking_tinder = gr.CheckboxGroup(
                 choices=SMOKING_HABITS,
                 label="Preferowane nawyki palenia:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_workout_tinder = gr.CheckboxGroup(
                 choices=WORKOUT_HABITS,
                 label="Preferowane nawyki ćwiczeń:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_diet_tinder = gr.CheckboxGroup(
                 choices=DIETARY_PREFERENCES,
                 label="Preferowane preferencje dietetyczne:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_social_media_tinder = gr.CheckboxGroup(
                 choices=SOCIAL_MEDIA_ACTIVITY,
                 label="Preferowana aktywność w mediach społecznościowych:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             preferred_sleeping_tinder = gr.CheckboxGroup(
                 choices=SLEEPING_HABITS,
                 label="Preferowane nawyki spania:",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True
             )
             # ==========================================================================

             gr.Markdown("---") # Dodaj separator
             # === DODANE: Komponent do wyboru preferowanych orientacji seksualnych dla Clicker Tinder (CheckboxGroup) === # ZMODYFIKOWANO
             preferred_orientations_tinder = gr.CheckboxGroup(
                 choices=SEXUAL_ORIENTATIONS,
                 label="Preferowane orientacje seksualne (wybierz do 3):",
                 value=[], # Domyślnie nic nie jest wybrane
                 interactive=True,
                 # max_selected=3 # USUNIĘTO: Ten parametr powodował błąd w Twojej wersji Gradio
             )
             # ======================================================================================================= # ZMODYFIKOWANO

             gr.Markdown("---") # Dodaj separator


             # Przycisk Uruchom dla Clicker Tinder (Interaktywność zależy od model_load_status, nie od wybranych preferencji)
             btn_tinder = gr.Button(
                 "Uruchom Clicker Tinder",
                 interactive=CAN_CLASSIFY and "Błąd" not in model_load_status # Aktywny tylko gdy można klasyfikować
             )


        with gr.TabItem("Zwykły Clicker"):
             gr.Markdown("### Preferencje dla Zwykłego Clickera")
             gr.Markdown("Wybierz kolory włosów, które mają spowodować akcję **Swipe Right** dla skryptu **Zwykły Clicker**.")

             # Komponent do wyboru preferowanych kolorów dla Zwykłego Clickera
             if AVAILABLE_HAIR_COLORS:
                  preferred_hair_colors_regular = gr.CheckboxGroup(
                       choices=AVAILABLE_HAIR_COLORS, # Lista opcji z predict_image.py
                       label="Wybierz preferowane kolory włosów (Swipe Right):",
                       value=[] # Domyślnie nic nie jest wybrane
                  )
             else:
                  gr.Warning("Brak dostępnych kolorów włosów do konfiguracji akcji swipe dla Zwykłego Clickera.")
                  preferred_hair_colors_regular = gr.CheckboxGroup(
                       choices=[],
                       label="Brak dostępnych kolorów do konfiguracji akcji swipe:",
                       value=[],
                       interactive=False
                  )


             # Przycisk Uruchom dla Zwykłego Clickera (Interaktywność zależy od model_load_status, nie od wybranych preferencji)
             btn_regular = gr.Button(
                 "Uruchom Zwykły Clicker",
                 interactive=CAN_CLASSIFY and "Błąd" not in model_load_status # Aktywny tylko gdy można klasyfikować
             )

    # Komponent do wyświetlania statusu uruchomienia skryptu (Wspólny dla obu przycisków)
    script_output_md = gr.Markdown("") # Placeholder for script launch status


    gr.Markdown("---") # Dodaj separator po tabach
    gr.Markdown("### Sekcja Klasyfikacji Obrazu (Opcjonalnie)")
    gr.Markdown("Prześlij obraz i wybierz klasyfikatory, aby zobaczyć szczegółowe wyniki klasyfikacji.")

    # Sekcja Przesyłania Obrazu i Informacji o Obrazie
    with gr.Column():
        # Input component for image upload (type="pil" returns a PIL Image object)
        image_input = gr.Image(
            type="pil", # Return as PIL Image object
            label="Wybierz obraz do klasyfikacji...",
            sources=["upload", "webcam"], # Allow upload or webcam
            interactive=True # User can interact
        )
        # Markdown component to display image size/info
        image_info_md = gr.Markdown("") # Placeholder for image info

    # Sekcja Wyboru Klasyfikatorów
    # Użyjemy CheckboxGroup, jeśli lista klasyfikatorów jest dostępna, w przeciwnym razie poinformujemy o problemie
    if AVAILABLE_CLASSIFIERS:
         classifier_choices = gr.CheckboxGroup(
             choices=AVAILABLE_CLASSIFIERS, # Lista opcji z predict_image.py
             label="Wybierz jeden lub więcej klasyfikatorów:",
             value=[] # Domyślnie nic nie jest wybrane
         )
    else:
         # Jeśli AVAILABLE_CLASSIFIERS jest pusta lub niedostępna, wyświetl komunikat
         gr.Warning("Lista dostępnych klasyfikatorów jest pusta lub niedostępna.")
         classifier_choices = gr.CheckboxGroup(
              choices=["Brak dostępnych klasyfikatorów"],
              label="Wybierz jeden lub więcej klasyfikatorów:",
              value=[],
              interactive=False # Deaktywuj, jeśli brak opcji
         )

    # Sekcja Klasyfikacji i Wyświetlania Wyników
    # Przycisk będzie aktywny tylko jeśli model został wczytany pomyślnie i logika klasyfikacji jest dostępna
    classify_button = gr.Button(
        "Sklasyfikuj Przesłany Obraz",
        interactive=CAN_CLASSIFY and "Błąd" not in model_load_status # Aktywny tylko gdy można klasyfikować
    )

    # Markdown component to display classification results
    results_md = gr.Markdown("### Wyniki Klasyfikacji Obrazu")


    # --- Definicja Zdarzeń ---

    # Zdarzenie: zmiana w wyborze preferowanych kolorów LUB pasji dla Clicker Tinder
    # Funkcja sprawdzająca, czy wybrano jakiekolwiek kolory LUB jakiekolwiek pasje
    # def update_tinder_button_interactivity(hair_colors, passions):
    #     return gr.update(interactive=len(hair_colors) > 0 or len(passions) > 0)

    # Zdarzenie dla zmiany w wyborze kolorów w Tinder tabie
    # preferred_hair_colors_tinder.change(
    #      fn=update_tinder_button_interactivity,
    #      inputs=[preferred_hair_colors_tinder, preferred_passions_tinder], # Weź wartości z obu komponentów
    #      outputs=btn_tinder
    # )

    # Zdarzenie dla zmiany w wyborze pasji w Tinder tabie
    # preferred_passions_tinder.change(
    #     fn=update_tinder_button_interactivity,
    #     inputs=[preferred_hair_colors_tinder, preferred_passions_tinder], # Weź wartości z obu komponentów
    #     outputs=btn_tinder
    # )
    # ================================================================


    # Zdarzenie: kliknięcie przycisku Clicker Tinder
    # Uruchom skrypt Clicker Tinder z wybranymi preferencjami
    btn_tinder.click(
        fn=lambda preferred_colors, preferred_p, height_value, relationship_value, languages_value, zodiac_value, education_value, children_value, vaccination_value, personality_value, communication_value, love_languages_value, pets_value, drinking_value, smoking_value, workout_value, diet_value, social_media_value, sleeping_value, orientations_value:
           run_script_ui("Clicker Tinder", preferred_colors, preferred_p, height_value, relationship_value, languages_value, zodiac_value, education_value, children_value, vaccination_value, personality_value, communication_value, love_languages_value, pets_value, drinking_value, smoking_value, workout_value, diet_value, social_media_value, sleeping_value, orientations_value),
        inputs=[
            preferred_hair_colors_tinder,
            preferred_passions_tinder,
            preferred_height_range_tinder,
            relationship_goals_tinder,
            preferred_languages_tinder,
            preferred_zodiac_tinder,
            preferred_education_tinder,
            preferred_children_tinder,
            preferred_vaccination_tinder,
            preferred_personality_tinder,
            preferred_communication_tinder,
            preferred_love_languages_tinder,
            preferred_pets_tinder,
            preferred_drinking_tinder,
            preferred_smoking_tinder,
            preferred_workout_tinder,
            preferred_diet_tinder,
            preferred_social_media_tinder,
            preferred_sleeping_tinder,
            preferred_orientations_tinder
        ],
        outputs=script_output_md
    )

    # ZMODYFIKOWANO: Zdarzenie: zmiana w wyborze preferowanych kolorów dla Zwykłego Clickera
    # Aktywuj/dezaktywuj przycisk Zwykłego Clickera (teraz zależy od model_load_status)
    # preferred_hair_colors_regular.change(
    #      fn=lambda colors: gr.update(interactive=len(colors) > 0),
    #      inputs=preferred_hair_colors_regular,
    #      outputs=btn_regular
    # )
    # ================================================================

    # ZMODYFIKOWANO: Zdarzenie: kliknięcie przycisku Zwykłego Clickera
    # Uruchom skrypt Zwykłego Clickera z wybranymi preferencjami KOLORÓW (pozostałe parametry puste/None)
    btn_regular.click(
        fn=lambda preferred_colors: run_script_ui("Zwykły Clicker", preferred_colors, [], None, [], None, [], [], [], [], [], [], [], [], [], [], [], [], [], [], []), # Przekaż puste lists/None for all params except hair colors
        inputs=[preferred_hair_colors_regular], # Weź preferowane kolory z komponentu w tej zakładce
        outputs=script_output_md
    )

    # Zdarzenie: zmiana w komponencie image_input (dla sekcji klasyfikacji)
    image_input.change(
        fn=display_image_info,
        inputs=image_input,
        outputs=image_info_md
    )

    # Zdarzenie: kliknięcie przycisku classify_button (dla sekcji klasyfikacji)
    classify_button.click(
        fn=classify_image,
        inputs=[image_input, classifier_choices],
        outputs=[results_md]
    )
    # ==============================================================


    gr.Markdown("\n---\n")
    gr.Markdown(f"""
    **Instrukcje Uruchomienia Aplikacji Gradio:**
    1.  Upewnij się, że w skrypcie `predict_image.py` masz **globalną zmienną `AVAILABLE_HAIR_COLORS`** (lista stringów, np. `["Blond", "Brunette", "Black", "Red"]`)
        zawierającą nazwy kolorów włosów rozpoznawanych przez klasyfikator.
    2.  Upewnij się, że **przeorganizowałeś** skrypt `predict_image.py` zgodnie z moimi wcześniejszymi instrukcjami,
        przenosząc logikę do funkcji (`load_classifier_model`, `classify_image_with_models`)
        i dodając globalne zmienne `AVAILABLE_CLASSIFIERS` i `AVAILABLE_HAIR_COLORS` na najwyższym poziomie modułu.
    3.  Stwórz plik `passions_tinder.json` w tym samym katalogu co ten skrypt, zawierający listę pasji w formacie JSON (jak podano wcześniej).
    4.  **ZMODYFIKUJ PLIKI `clicker_tinder.py` i `clicker.py`**, aby akceptowały argumenty w wierszu poleceń (np. za pomocą modułu `argparse`)
        w formacie `--preferred-hair-colors kolor1 kolor2 ...` **oraz `clicker_tinder.py` powinien akceptować `--preferred-passions pasja1 pasja2 ...`, `--height-range min_cm max_cm`, `--relationship-goal cel1 cel2 ...`**, **`--preferred-languages jezyk1 jezyk2 ...`**, **`--preferred-zodiacs znak1 znak2 ...`**, **`--preferred-education poziom1 poziom2 ...`**, **`--preferred-children opcja1 opcja2 ...`**, **`--preferred-vaccination status1 status2 ...`**, **`--preferred-personality typ1 typ2 ...`**, **`--preferred-communication styl1 styl2 ...`**, **`--preferred-love-languages jezyk_milosc1 jezyk_milosc2 ...`**, **`--preferred-pets zwierzak1 zwierzak2 ...`**, **`--preferred-drinking nawyk1 nawyk2 ...`**, **`--preferred-smoking nawyk_palenia1 nawyk_palenia2 ...`**, **`--preferred-workout nawyk_cwiczen1 nawyk_cwiczen2 ...`**, **`--preferred-diet dieta1 dieta2 ...`**, **`--preferred-social-media aktywnosc1 aktywnosc2 ...`**, **`--preferred-sleeping nawyk_spania1 nawyk_spania2 ...`**, **i **`--preferred-orientations orientacja1 orientacja2 ...`**** (wszystkie mogą przyjąć wiele wartości, jeśli wybrano wiele opcji).
        Skrypty powinny używać tych list/zakresu do decydowania o akcji swipe.
        Dla `clicker_tinder.py`, jeśli profil spełnia kryteria koloru włosów LUB pasji LUB znajduje się w preferowanym zakresie wzrostu, powinien wykonać akcję "Swipe Right".
        Dla `clicker.py` logika pozostaje bez zmian (tylko kolory włosów).
    5.  Upewnij się, że umieściłeś zmodyfikowany `predict_image.py` i ten skrypt (`{os.path.basename(__file__)}`)
        w tym samym katalogu, a także zaktualizowane skrypty clicker.
    6.  Upewnij się, że plik modelu (`model_wlosy_best.pt`) jest dostępny pod ścieżką `MODEL_PATH` zdefiniowaną w `predict_image.py`.
    7.  Upewnij się, że zainstalowałeś niezbędne biblioteki: `pip install gradio Pillow torch torchvision numpy`.
    8.  Otwórz terminal, **aktywuj wirtualne środowisko**, przejdź do katalogu zawierającego wszystkie pliki i uruchom komendę:
        `python {os.path.basename(__file__)}`
    9.  Aplikacja otworzy się automatycznie w przeglądarce.
    """)


# --- Uruchomienie Aplikacji Gradio ---
if __name__ == "__main__":
    # demo.launch(inbrowser=True) # Uruchom i otwórz automatycznie w przeglądarce
    # Możesz użyć portu, jeśli chcesz, np. demo.launch(inbrowser=True, server_port=7860)
    demo.launch() # Uruchom, a Gradio poda adres w konsoli