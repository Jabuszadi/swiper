import streamlit as st
import subprocess
import sys
import os

# 🔧 Konfiguracja ścieżek do skryptów (zakładamy, że są w tym samym katalogu)
CLICKER_TINDER_SCRIPT = "clicker_tinder.py"
CLICKER_SCRIPT = "clicker.py"

st.title("Aplikacja do Uruchamiania Clickerów")

st.write("Kliknij przyciski poniżej, aby uruchomić wybrane skrypty.")

def run_script(script_name):
    """Uruchamia dany skrypt w osobnym procesie."""
    st.info(f"Próbuję uruchomić skrypt: {script_name}...")
    try:
        # Użyj sys.executable, aby uruchomić skrypt w tym samym środowisku Pythona co Streamlit
        # cwd='.' oznacza uruchomienie w bieżącym katalogu roboczym
        # Popen uruchamia proces i nie czeka na jego zakończenie
        process = subprocess.Popen(
            [sys.executable, script_name],
            cwd='.' # Uruchom w bieżącym katalogu
            # Możesz dodać stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            # aby próbować przechwycić wyjście, ale wyświetlanie go w czasie rzeczywistym w Streamlit
            # jest bardziej zaawansowane i wyjście może pojawić się w konsoli terminala.
        )
        st.success(f"Skrypt **{script_name}** został uruchomiony w tle (PID: {process.pid}).")
        st.warning("Wyjście (print, błędy) skryptu pojawi się w konsoli terminala, z której uruchomiono Streamlit.")
        return process
    except FileNotFoundError:
        st.error(f"Błąd: Nie znaleziono pliku skryptu: **{script_name}**. Upewnij się, że znajduje się w tym samym katalogu.")
        return None
    except Exception as e:
        st.error(f"Wystąpił błąd podczas uruchamiania skryptu **{script_name}**: {e}")
        return None

# Przycisk do uruchomienia clicker_tinder.py
if st.button("Uruchom Swiper dla Tinder"):
    run_script(CLICKER_TINDER_SCRIPT)

# Przycisk do uruchomienia clicker.py
if st.button("Uruchom Swiper dla Badoo"):
    run_script(CLICKER_SCRIPT)

st.write("\n---\n")
st.info(f"""
**Jak to działa:**
Kliknięcie przycisku uruchamia odpowiedni plik (`{CLICKER_TINDER_SCRIPT}` lub `{CLICKER_SCRIPT}`)
jako osobny proces systemowy. Aplikacja Streamlit działa dalej niezależnie.

**Ważne:**
*   Upewnij się, że pliki `{CLICKER_TINDER_SCRIPT}` i `{CLICKER_SCRIPT}` znajdują się w tym samym katalogu, co `{os.path.basename(__file__)}`.
*   Jeśli skrypty wymagają interakcji użytkownika przez konsolę lub tworzą własne okna, będą one działać poza interfejsem Streamlit.
*   Wyjście `print()` ze skryptów pojawi się w konsoli, z której uruchomiłeś aplikację Streamlit, a nie w interfejsie webowym.
""")
