import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import numpy as np
import random
import os
from collections import Counter

# ---------- Konfiguracja ----------
data_dir = "hair_color_split"
sample_size = 1000
batch_size = 64
epochs = 20
early_stop_patience = 4
random.seed(42)

NORM_MEAN = [0.5, 0.5, 0.5]
NORM_STD = [0.5, 0.5, 0.5]

# ---------- Transformacje ----------
# Normalization should be for 3 channels (RGB)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD)
])



# ---------- Dataset ----------
full_dataset = datasets.ImageFolder(data_dir, transform=transform)
class_names = full_dataset.classes
print("🧾 Klasy:", class_names)
# Ensure that len(class_names) is 4 if the goal is a 4-class model.
# This depends on the structure of the `data_dir`.
# If `data_dir` has 4 subdirectories, len(class_names) will be 4.

# ⚖️ Sprawdzenie balansu klas
labels = [label for _, label in full_dataset]
label_counts = Counter(labels)
for idx, count in label_counts.items():
    print(f"⚖️ {class_names[idx]}: {count} obrazów")

# ---------- Losowa próbka ----------
sample_indices = random.sample(range(len(full_dataset)), sample_size)
train_size = int(0.8 * sample_size)
train_indices = sample_indices[:train_size]
val_indices = sample_indices[train_size:]

train_set = Subset(full_dataset, train_indices)
val_set = Subset(full_dataset, val_indices)

train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_set, batch_size=batch_size)

# ---------- Model ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = models.resnet18(pretrained=True)
# The number of output features of model.fc is set to len(class_names).
# If data_dir provides 4 classes, len(class_names) will be 4,
# and the model will be trained for 4 classes.
model.fc = nn.Linear(model.fc.in_features, len(class_names))
model = model.to(device)

# ---------- Loss i optymalizator ----------
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0003)

# ---------- Trenowanie ----------
train_losses, val_losses = [], []
train_accuracies, val_accuracies = [], []
best_val_acc = 0.0
patience_counter = 0

for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    correct_train = 0
    total_train = 0

    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, preds = torch.max(outputs, 1)
        correct_train += (preds == labels).sum().item()
        total_train += labels.size(0)

    train_loss = running_loss / len(train_loader)
    train_acc = correct_train / total_train
    train_losses.append(train_loss)
    train_accuracies.append(train_acc)

    # ---------- Walidacja ----------
    model.eval()
    val_loss = 0.0
    correct_val = 0
    total_val = 0

    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct_val += (preds == labels).sum().item()
            total_val += labels.size(0)

    val_loss /= len(val_loader)
    val_acc = correct_val / total_val
    val_losses.append(val_loss)
    val_accuracies.append(val_acc)

    print(f"[Epoka {epoch+1:02d}] Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.3f} | Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.3f}")

    # ---------- Early Stopping ----------
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        patience_counter = 0
        torch.save(model.state_dict(), "model_wlosy_best.pt")
        print("💾 Zapisano nowy najlepszy model.")
    else:
        patience_counter += 1
        if patience_counter >= early_stop_patience:
            print("🛑 Early stopping – brak poprawy.")
            break

# ---------- Ewaluacja ----------
model.load_state_dict(torch.load("model_wlosy_best.pt"))
model.eval()
all_preds, all_labels = [], []

with torch.no_grad():
    for inputs, labels in val_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

# ---------- Metryki ----------
print("\n✅ Dokładność końcowa: {:.2f}%".format((np.array(all_preds) == np.array(all_labels)).mean() * 100))
print("\n📋 Raport klasyfikacji:")
print(classification_report(all_labels, all_preds, target_names=class_names))
print("\n📉 Macierz pomyłek:")
print(confusion_matrix(all_labels, all_preds))

# ---------- Wykres ----------
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses, label="train loss")
plt.plot(val_losses, label="val loss")
plt.title("Loss")
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(train_accuracies, label="train acc")
plt.plot(val_accuracies, label="val acc")
plt.title("Accuracy")
plt.legend()

plt.tight_layout()
plt.savefig("training_plot.png")
plt.show()
