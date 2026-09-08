"""
LifeLine CrisisMMD v2.0 AI Model Trainer
Loads all 7 disaster datasets from CrisisMMD_v2.0/annotations,
trains a high-performance NLP Humanitarian Triage & Severity Classifier,
evaluates model metrics, and exports the serialized pipeline artifacts.
"""

import os, glob, sys, pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score

sys.stdout.reconfigure(encoding='utf-8')

print("====================================================")
print("🚀 Starting LifeLine CrisisMMD v2.0 Model Training...")
print("====================================================")

# 1. Locate TSV files
ANNOTATIONS_DIR = r"c:\Users\Vijay\LifeLine\CrisisMMD_v2.0\CrisisMMD_v2.0\annotations"

if not os.path.exists(ANNOTATIONS_DIR):
    ANNOTATIONS_DIR = os.path.join(os.path.dirname(__file__) if '__file__' in locals() else '.', 'CrisisMMD_v2.0', 'CrisisMMD_v2.0', 'annotations')

tsv_files = glob.glob(os.path.join(ANNOTATIONS_DIR, "*.tsv"))
# Filter out OS hidden ._ files
tsv_files = [f for f in tsv_files if not os.path.basename(f).startswith("._")]

print(f"Found {len(tsv_files)} CrisisMMD dataset TSV files:")
for f in tsv_files:
    print(f"  - {os.path.basename(f)}")

# 2. Combine Datasets
dfs = []
for f in tsv_files:
    try:
        df_temp = pd.read_csv(f, sep='\t', on_bad_lines='skip')
        dfs.append(df_temp)
    except Exception as e:
        print(f"Warning loading {f}: {e}")

if not dfs:
    print("Error: No data loaded!")
    sys.exit(1)

full_df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal Raw Rows Loaded: {len(full_df)}")

# Clean and Filter Data
df = full_df.dropna(subset=['tweet_text']).copy()
df['tweet_text'] = df['tweet_text'].astype(str).str.strip()

# Target Mapping: Map text_human / image_human categories to LifeLine standardized disaster classes
def map_category(row):
    text_h = str(row.get('text_human', '')).lower()
    img_h = str(row.get('image_human', '')).lower()
    text = str(row.get('tweet_text', '')).lower()
    
    if any(k in text_h or k in text for k in ['rescue', 'donation', 'volunteer', 'trapped']):
        return 'Rescue & Relief'
    elif any(k in text_h or k in text for k in ['injured', 'dead', 'medical', 'hospital', 'casualty']):
        return 'Medical'
    elif any(k in text_h or k in text for k in ['infrastructure', 'utility', 'building', 'damage', 'bridge', 'road']):
        return 'Infrastructure Damage'
    elif any(k in text_h or k in text for k in ['affected', 'displaced', 'people', 'home']):
        return 'Humanitarian Assistance'
    elif any(k in text for k in ['flood', 'water', 'submerged', 'river']):
        return 'Flood'
    elif any(k in text for k in ['fire', 'wildfire', 'smoke', 'blaze']):
        return 'Fire'
    elif any(k in text for k in ['earthquake', 'quake', 'rubble']):
        return 'Earthquake'
    else:
        return 'General Disaster Alert'

df['target_category'] = df.apply(map_category, axis=1)

print("\nCrisisMMD Dataset Class Distribution:")
print(df['target_category'].value_counts())

# 3. Train-Test Split
X = df['tweet_text']
y = df['target_category']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
print(f"\nTrain set: {len(X_train)} samples | Test set: {len(X_test)} samples")

# 4. Feature Extraction: TF-IDF N-gram Vectorizer
vectorizer = TfidfVectorizer(max_features=12000, ngram_range=(1, 2), stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 5. Model Benchmarking & Selection
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, C=2.0),
    'SGD Classifier (Linear SVM)': SGDClassifier(loss='log_loss', max_iter=1000, random_state=42),
    'Multinomial Naive Bayes': MultinomialNB(alpha=0.1)
}

best_model = None
best_acc = 0.0
best_name = ""

print("\n--- Benchmarking Machine Learning Classifiers on CrisisMMD v2.0 ---")
for name, clf in models.items():
    clf.fit(X_train_vec, y_train)
    preds = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='weighted')
    print(f"[{name}] Accuracy: {acc * 100:.2f}% | Weighted F1-Score: {f1:.4f}")
    
    if acc > best_acc:
        best_acc = acc
        best_model = clf
        best_name = name

print(f"\n🏆 Champion Model Selected: {best_name} (Accuracy: {best_acc * 100:.2f}%)")

# Detailed Evaluation of Champion Model
y_pred_best = best_model.predict(X_test_vec)
print("\n--- Detailed Classification Report ---")
print(classification_report(y_test, y_pred_best))

# 6. Export Trained Model Artifacts
MODEL_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_model.pkl"
VEC_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vectorizer.pkl"

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(best_model, f)

with open(VEC_PATH, 'wb') as f:
    pickle.dump(vectorizer, f)

print("====================================================")
print(f"✅ CrisisMMD Model trained & saved to: {MODEL_PATH}")
print(f"✅ Vectorizer saved to: {VEC_PATH}")
print("====================================================")
