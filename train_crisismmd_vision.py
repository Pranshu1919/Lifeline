"""
LifeLine CrisisMMD v2.0 PyTorch Computer Vision Trainer
Fine-tunes PyTorch MobileNetV3 on CrisisMMD v2.0 visual disaster dataset to:
1. Detect Real vs Fake/Off-topic disaster reporting photos (`image_info`).
2. Score Visual Disaster Damage Severity (`severe_damage`, `mild_damage`, `little_or_no_damage`).
Exports trained PyTorch weights: crisismmd_vision_damage.pt & crisismmd_vision_authenticity.pt
"""

import os, glob, sys, time
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

log("====================================================")
log("🚀 Starting PyTorch Visual Model Training on CrisisMMD v2.0...")
log("====================================================")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
log(f"Using Compute Device: {device}")

# 1. Load TSV Annotations
BASE_DIR = r"c:\Users\Vijay\LifeLine\CrisisMMD_v2.0\CrisisMMD_v2.0"
ANNOTATIONS_DIR = os.path.join(BASE_DIR, "annotations")

tsv_files = glob.glob(os.path.join(ANNOTATIONS_DIR, "*.tsv"))
tsv_files = [f for f in tsv_files if not os.path.basename(f).startswith("._")]

dfs = []
for f in tsv_files:
    try:
        df_temp = pd.read_csv(f, sep='\t', on_bad_lines='skip')
        dfs.append(df_temp)
    except Exception as e:
        log(f"Warning reading {f}: {e}")

df_all = pd.concat(dfs, ignore_index=True)
log(f"Loaded {len(df_all)} total CrisisMMD image records.")

def get_full_img_path(rel_path):
    if pd.isna(rel_path): return None
    full_p = os.path.join(BASE_DIR, str(rel_path).replace('/', os.sep))
    return full_p if os.path.exists(full_p) else None

df_all['full_image_path'] = df_all['image_path'].apply(get_full_img_path)
df_valid = df_all.dropna(subset=['full_image_path']).copy()
log(f"Found {len(df_valid)} existing image files on disk!")

# Class Definition
class CrisisImageDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_p = row['full_image_path']
        label = row['label']

        try:
            image = Image.open(img_p).convert('RGB')
        except Exception:
            image = Image.new('RGB', (224, 224), (0, 0, 0))

        if self.transform:
            image = self.transform(image)

        return image, torch.tensor(label, dtype=torch.long)

train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ----------------------------------------------------
# TASK 1: Authenticity Classifier (Real vs Fake / Off-Topic)
# ----------------------------------------------------
log("\n--- Task 1: Training Real vs Fake/Off-Topic Image Classifier ---")
df_auth = df_valid.dropna(subset=['image_info']).copy()
auth_map = {'informative': 1, 'not_informative': 0}
df_auth['label'] = df_auth['image_info'].map(auth_map).fillna(0).astype(int)

# Use balanced subset for fast training
df_auth_sub = df_auth.groupby('label', group_keys=False).apply(lambda x: x.sample(min(len(x), 1500), random_state=42))

from sklearn.model_selection import train_test_split
train_auth_df, val_auth_df = train_test_split(df_auth_sub, test_size=0.2, random_state=42, stratify=df_auth_sub['label'])

auth_train_loader = DataLoader(CrisisImageDataset(train_auth_df, train_transform), batch_size=32, shuffle=True)
auth_val_loader = DataLoader(CrisisImageDataset(val_auth_df, val_transform), batch_size=32, shuffle=False)

auth_model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
auth_model.classifier[3] = nn.Linear(auth_model.classifier[3].in_features, 2)
auth_model = auth_model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(auth_model.parameters(), lr=0.0003)

epochs = 2
for epoch in range(epochs):
    auth_model.train()
    running_loss, correct, total = 0.0, 0, 0
    t0 = time.time()
    for imgs, labels in auth_train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = auth_model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * imgs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

    train_acc = correct / total
    auth_model.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for imgs, labels in auth_val_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = auth_model(imgs)
            _, preds = torch.max(outputs, 1)
            val_correct += torch.sum(preds == labels.data).item()
            val_total += labels.size(0)

    val_acc = val_correct / val_total
    log(f"Epoch {epoch+1}/{epochs} [{time.time()-t0:.1f}s] - Train Acc: {train_acc*100:.2f}% | Val Acc: {val_acc*100:.2f}%")

AUTH_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vision_authenticity.pt"
torch.save(auth_model.state_dict(), AUTH_PATH)
log(f"✅ Saved Authenticity Weights to: {AUTH_PATH}")

# ----------------------------------------------------
# TASK 2: Visual Damage Severity Classifier
# ----------------------------------------------------
log("\n--- Task 2: Training PyTorch Damage Severity Model ---")
df_dmg = df_valid.dropna(subset=['image_damage']).copy()
df_dmg = df_dmg[df_dmg['image_damage'] != 'nan'].copy()
dmg_map = {'little_or_no_damage': 0, 'mild_damage': 1, 'severe_damage': 2}
df_dmg['label'] = df_dmg['image_damage'].map(dmg_map).dropna().astype(int)

df_dmg_sub = df_dmg.groupby('label', group_keys=False).apply(lambda x: x.sample(min(len(x), 1000), random_state=42))
train_dmg_df, val_dmg_df = train_test_split(df_dmg_sub, test_size=0.2, random_state=42, stratify=df_dmg_sub['label'])

dmg_train_loader = DataLoader(CrisisImageDataset(train_dmg_df, train_transform), batch_size=32, shuffle=True)
dmg_val_loader = DataLoader(CrisisImageDataset(val_dmg_df, val_transform), batch_size=32, shuffle=False)

dmg_model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
dmg_model.classifier[3] = nn.Linear(dmg_model.classifier[3].in_features, 3)
dmg_model = dmg_model.to(device)

optimizer_dmg = optim.Adam(dmg_model.parameters(), lr=0.0003)

for epoch in range(epochs):
    dmg_model.train()
    running_loss, correct, total = 0.0, 0, 0
    t0 = time.time()
    for imgs, labels in dmg_train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer_dmg.zero_grad()
        outputs = dmg_model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer_dmg.step()
        running_loss += loss.item() * imgs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

    train_acc = correct / total
    dmg_model.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for imgs, labels in dmg_val_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = dmg_model(imgs)
            _, preds = torch.max(outputs, 1)
            val_correct += torch.sum(preds == labels.data).item()
            val_total += labels.size(0)

    val_acc = val_correct / val_total
    log(f"Epoch {epoch+1}/{epochs} [{time.time()-t0:.1f}s] - Train Acc: {train_acc*100:.2f}% | Val Acc: {val_acc*100:.2f}%")

DMG_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vision_damage.pt"
torch.save(dmg_model.state_dict(), DMG_PATH)

log("====================================================")
log(f"✅ Saved Damage Severity Weights to: {DMG_PATH}")
log("====================================================")
