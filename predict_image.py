import os
# The following line is a workaround for the OMP: Error #15.
# It allows the program to continue execution even if multiple OpenMP runtimes are found.
# This is an unsafe, unsupported, and undocumented workaround.
# Use with caution, as it may cause crashes or silently produce incorrect results.
# The best solution is to ensure only a single OpenMP runtime is linked.
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# === Ścieżka do modelu i klasyfikowanego zdjęcia ===
MODEL_PATH = "model_wlosy_best.pt"
IMAGE_PATH = "example.png"  # <- zmień na własny plik

# CLASS_NAMES is set to 4 classes as per user instruction.
# The original error indicated that the checkpoint 'model_wlosy.pt' might be for 3 classes.
# If 'model_wlosy.pt' is indeed for 3 classes, loading it into a 4-class model structure
# will result in a RuntimeError.
CLASS_NAMES = ["black", "blonde", "brunette", "redhead"]  # User confirms 4 classes.

# === Transformacje (musi być takie samo jak przy trenowaniu) ===
# Średnie i odchylenia standardowe użyte do normalizacji
NORM_MEAN = [0.5, 0.5, 0.5]
NORM_STD = [0.5, 0.5, 0.5]

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD)
])

# === Wczytaj model ===
# Sprawdź dostępność CUDA i skonfiguruj urządzenie
if not torch.cuda.is_available():
    print("BŁĄD: CUDA nie jest dostępne. Ten skrypt wymaga akceleracji GPU.")
    # Rzucenie wyjątku zatrzyma wykonanie skryptu, jeśli GPU jest absolutnie konieczne.
    raise RuntimeError("CUDA is not available. GPU acceleration is required for this script.")

device = torch.device("cuda")
print(f"Pomyślnie skonfigurowano użycie urządzenia: {device}")

model = models.resnet18(pretrained=False) # Using pretrained=False as we load a full state_dict

# Define the model's final layer for the number of classes specified in CLASS_NAMES.
# Since len(CLASS_NAMES) is 4, this will configure the model for 4 output classes.
model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))

# Attempt to load the state dictionary from MODEL_PATH.
# IMPORTANT: For this to succeed without error, the checkpoint file specified by MODEL_PATH
# (i.e., 'model_wlosy.pt') must contain weights for a model that was also configured
# with len(CLASS_NAMES) (i.e., 4) output classes.
# If 'model_wlosy.pt' was trained for a different number of classes (e.g., 3),
# a RuntimeError will occur here due to size mismatches in the 'fc' layer weights and biases.
# Example error for such a mismatch:
# "size mismatch for fc.weight: copying a param with shape torch.Size([3, 512]) from checkpoint,
#  the shape in current model is torch.Size([4, 512])."
# To resolve such an error, ensure MODEL_PATH points to a model checkpoint that
# was trained with the correct number of classes (4 in this case).
# map_location=device ensures tensors are loaded onto the configured device (GPU in this case)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.to(device) # Przenieś model na wybrane urządzenie (GPU)
model.eval()

# === Wczytaj obraz ===
image = Image.open(IMAGE_PATH).convert("RGB")
# Przenieś tensor wejściowy na wybrane urządzenie (GPU)
input_tensor = transform(image).unsqueeze(0).to(device)

# === Wizualizacja tego, co "widzi" model (obraz po transformacjach) ===
def imshow_transformed(tensor, title=None):
    """Wyświetla tensor obrazu po transformacjach."""
    # Przeniesienie tensora na CPU i usunięcie wymiaru batcha
    # Operacje numpy i matplotlib wymagają danych na CPU
    image_tensor = tensor.squeeze(0).cpu().clone()
    
    # Denormalizacja (operacje na tensorach CPU)
    mean = torch.tensor(NORM_MEAN).view(3, 1, 1) # Domyślnie na CPU
    std = torch.tensor(NORM_STD).view(3, 1, 1)   # Domyślnie na CPU
    image_tensor = image_tensor * std + mean
    
    # Konwersja do numpy i zmiana kolejności wymiarów (C, H, W) -> (H, W, C)
    image_numpy = image_tensor.permute(1, 2, 0).numpy()
    
    # Przycięcie wartości do zakresu [0, 1] na wypadek błędów numerycznych
    image_numpy = np.clip(image_numpy, 0, 1)
    
    plt.figure(figsize=(6, 6))
    plt.imshow(image_numpy)
    if title:
        plt.title(title)
    plt.axis('off')
    plt.show()

# Wyświetl przetworzony obraz
# input_tensor jest na GPU, ale imshow_transformed przeniesie go na CPU do wizualizacji
imshow_transformed(input_tensor, title=f"Obraz '{os.path.basename(IMAGE_PATH)}' po transformacjach (wejście modelu)")


# === Predykcja ===
# Obliczenia na GPU, ponieważ model i input_tensor są na GPU
with torch.no_grad():
    outputs = model(input_tensor)
    _, predicted = torch.max(outputs, 1)
    predicted_class_idx = predicted.item() # .item() przenosi skalar z GPU na CPU

    # Check if the predicted index is valid for the CLASS_NAMES list.
    # This should hold true if the model loaded correctly and is consistent with CLASS_NAMES.
    if 0 <= predicted_class_idx < len(CLASS_NAMES):
        predicted_class = CLASS_NAMES[predicted_class_idx]
    else:
        # This case would be unexpected if the model is correctly loaded for 4 classes.
        # It might indicate an issue if the model's output range doesn't align with expectations.
        print(f"Warning: Predicted class index ({predicted_class_idx}) is out of bounds "
              f"for CLASS_NAMES list (size {len(CLASS_NAMES)}).")
        predicted_class = "Error: Unknown Class"

print(f"\n📸 Klasyfikacja zdjęcia '{os.path.basename(IMAGE_PATH)}': {predicted_class.upper()}")
