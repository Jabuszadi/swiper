import os
# The following line is a workaround for the OMP: Error #15.
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
# import matplotlib.pyplot as plt # Nie potrzebujemy tego w wersji modułowej
import numpy as np

# === Konfiguracja ===
MODEL_PATH = "model_wlosy_best.pt"
CLASS_NAMES = ["black", "blonde", "brunette", "redhead"]
NORM_MEAN = [0.5, 0.5, 0.5]
NORM_STD = [0.5, 0.5, 0.5]

# Dostępne klasyfikatory - ta lista jest używana przez aplikację Streamlit
AVAILABLE_CLASSIFIERS = [
    "Klasyfikator Koloru Włosów",
    # Dodaj tutaj inne nazwy klasyfikatorów, jeśli Twój skrypt je obsługuje
    # np. "Klasyfikator Etniczny"
]

# === Transformacje ===
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD)
])

# Zmienne globalne na potrzeby wczytanego modelu i urządzenia
_model = None
_device = None

# === Funkcja do wczytania modelu (wywoływana raz przez Streamlit) ===
def load_classifier_model():
    """Wczytuje model klasyfikatora. Wywoływana raz."""
    global _model, _device

    if _model is not None:
        print("Model już wczytany.")
        return _model # Zwraca istniejący model

    print("Wczytywanie modelu klasyfikatora...")

    if not torch.cuda.is_available():
        print("CUDA nie jest dostępne. Używam CPU.")
        _device = torch.device("cpu")
    else:
        _device = torch.device("cuda")
        print(f"Pomyślnie skonfigurowano użycie urządzenia: {_device}")

    try:
        model = models.resnet18(pretrained=False)
        model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))

        # map_location=device zapewnia wczytanie na właściwe urządzenie (CPU lub GPU)
        state_dict = torch.load(MODEL_PATH, map_location=_device)

        # Jeśli klucze w state_dict mają prefiks 'module.' (np. z DataParallel), usuń go
        # state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}

        model.load_state_dict(state_dict)
        model.to(_device)
        model.eval()
        _model = model # Przypisz wczytany model do globalnej zmiennej
        print("Model wczytany pomyślnie.")
        return _model

    except FileNotFoundError:
        print(f"❌ Błąd: Plik modelu nie znaleziono: {MODEL_PATH}")
        _model = None # Upewnij się, że model jest None w przypadku błędu
        raise # Przekaż błąd dalej
    except RuntimeError as e:
        print(f"❌ Błąd Runtime podczas wczytywania modelu: {e}")
        print("Może być niezgodność liczby klas lub inny problem z plikiem modelu.")
        _model = None
        raise
    except Exception as e:
        print(f"❌ Wystąpił nieoczekiwany błąd podczas wczytywania modelu: {e}")
        _model = None
        raise

# === Funkcja do klasyfikacji obrazu (wywoływana przez Streamlit) ===
def classify_image_with_models(pil_image: Image.Image, selected_classifiers: list):
    """
    Klasyfikuje obraz za pomocą wybranych klasyfikatorów.

    Args:
        pil_image: Obiekt obrazu PIL.Image.Image.
        selected_classifiers: Lista nazw wybranych klasyfikatorów (z AVAILABLE_CLASSIFIERS).

    Returns:
        Słownik z wynikami klasyfikacji dla każdego wybranego klasyfikatora.
    """
    # Ta funkcja zakłada, że load_classifier_model() została już wywołana i _model jest wczytany
    if _model is None or _device is None:
        # Możesz tu próbować wczytać model ponownie, albo zwrócić błąd
        try:
            load_classifier_model() # Próbuj wczytać model, jeśli jeszcze tego nie zrobiono
        except Exception:
            # Jeśli wczytywanie nadal się nie udało
             return {"Error": "Model klasyfikatora nie został wczytany poprawnie lub wystąpił błąd podczas ponownej próby wczytania."}


    # Upewnij się, że obraz jest w formacie RGB
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    try:
        # Przetwórz obraz i przenieś tensor na to samo urządzenie co model
        input_tensor = transform(pil_image).unsqueeze(0).to(_device)

        results = {}

        # PRZYKŁAD: Logika używająca Twojego modelu dla "Klasyfikator Koloru Włosów"
        # Musisz dostosować tę logikę do swoich faktycznych klasyfikatorów
        if "Klasyfikator Koloru Włosów" in selected_classifiers and _model:
             with torch.no_grad():
                 outputs = _model(input_tensor)
                 probabilities = torch.softmax(outputs, dim=1)[0].cpu().numpy() # Prawdopodobieństwa na CPU

             # Stwórz słownik {nazwa_klasy: prawdopodobieństwo}
             hair_color_results = {CLASS_NAMES[i]: float(probabilities[i]) for i in range(len(CLASS_NAMES))} # Konwersja na float dla JSON
             results["Klasyfikator Koloru Włosów"] = hair_color_results
        elif "Klasyfikator Koloru Włosów" in selected_classifiers and _model is None:
             results["Klasyfikator Koloru Włosów"] = {"Error": "Model Koloru Włosów nie jest dostępny (błąd ładowania)."}


        # DODAJ TUTAJ LOGIKĘ DLA INNYCH KLASYFIKATORÓW, JEŚLI MASZ INNE MODELE LUB METODY

        if not results:
             return {"Info": "Nie wybrano żadnych rozpoznanych klasyfikatorów do uruchomienia."}

        return results

    except Exception as e:
        print(f"❌ Wystąpił błąd podczas klasyfikacji: {e}")
        return {"Error": f"Błąd podczas klasyfikacji: {e}"}

# === Opcjonalny blok testowy (wykonywany tylko przy uruchomieniu predict_image.py bezpośrednio) ===
if __name__ == "__main__":
    # Ten kod wykona się tylko, gdy uruchomisz 'python predict_image.py'
    # Nie wykona się przy imporcie przez Streamlit.
    print("Uruchomiono skrypt predict_image.py bezpośrednio (tryb testowy).")

    IMAGE_PATH_TEST = "example.png" # Ścieżka do testowego obrazu

    try:
        # Wczytaj model
        loaded_model = load_classifier_model()

        # Wczytaj testowy obraz
        if not os.path.exists(IMAGE_PATH_TEST):
            print(f"❌ Błąd: Testowy plik obrazu nie znaleziono: {IMAGE_PATH_TEST}")
        else:
            test_image = Image.open(IMAGE_PATH_TEST)

            # Uruchom klasyfikację
            print(f"\nKlasyfikowanie testowego obrazu: {IMAGE_PATH_TEST}")
            # Wywołaj funkcję klasyfikującą z listą klasyfikatorów do użycia
            test_results = classify_image_with_models(test_image, AVAILABLE_CLASSIFIERS)

            # Wyświetl wyniki testowe
            print("\n--- Wyniki Testowe ---")
            for classifier_name, results in test_results.items():
                print(f"**{classifier_name}:**")
                if isinstance(results, dict):
                    for key, value in results.items():
                         print(f"- {key}: {value:.4f}")
                else:
                    print(results)
            print("--------------------")

    except Exception as e:
         print(f"Wystąpił błąd w trybie testowym: {e}")
