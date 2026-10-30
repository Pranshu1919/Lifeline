"""
LifeLine CrisisMMD v2.0 AI Model Trainer (Upgraded High-Performance Edition)
Loads all 7 disaster datasets from CrisisMMD_v2.0/annotations,
implements advanced dual-granularity feature extraction (Word + Character N-grams),
trains and benchmarks optimized classifiers, builds a soft-voting ensemble,
evaluates precision, recall, and F1 metrics, and exports serialized artifacts.
"""

import os, glob, re, sys, time, pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score

sys.stdout.reconfigure(encoding='utf-8')

print("====================================================================")
print("🚀 [LifeLine] Starting Upgraded CrisisMMD v2.0 NLP Model Training...")
print("====================================================================")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS_DIR = os.path.join(BASE_DIR, 'CrisisMMD_v2.0', 'CrisisMMD_v2.0', 'annotations')

tsv_files = glob.glob(os.path.join(ANNOTATIONS_DIR, "*.tsv"))
tsv_files = [f for f in tsv_files if not os.path.basename(f).startswith("._")]

print(f"Found {len(tsv_files)} CrisisMMD dataset TSV files:")
for f in tsv_files:
    print(f"  - {os.path.basename(f)}")

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

# Clean and filter text
df = full_df.dropna(subset=['tweet_text']).copy()
df['tweet_text'] = df['tweet_text'].astype(str).str.strip()

# Advanced Text Preprocessing
def clean_tweet_text(text):
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text) # Remove URLs
    text = re.sub(r'@\w+', ' ', text)                 # Remove Twitter mentions
    text = re.sub(r'#([A-Z][a-z]+)', r' \1', text)     # Split camel-case hashtags like #HurricaneHarvey
    text = re.sub(r'#(\w+)', r' \1', text)            # Un-hash tags
    text = re.sub(r'&amp;', ' and ', text)
    text = re.sub(r'&lt;', ' ', text)
    text = re.sub(r'&gt;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_text'] = df['tweet_text'].apply(clean_tweet_text)

# Standardized LifeLine Disaster Category Mapping
def map_category(row):
    text_h = str(row.get('text_human', '')).lower()
    text = str(row.get('clean_text', '')).lower()
    
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

print("\n--- Class Distribution across 8 Disaster Categories ---")
print(df['target_category'].value_counts())

# Stratified Train-Test Split (80% Train, 20% Held-out Test)
X_train, X_test, y_train, y_test = train_test_split(
    df['clean_text'], 
    df['target_category'], 
    test_size=0.20, 
    random_state=42, 
    stratify=df['target_category']
)
print(f"\nTrain set: {len(X_train)} samples | Test set: {len(X_test)} samples")

# Dual-Granularity Feature Representation: Word (1-3 grams) + Character (3-5 grams)
print("\nExtracting Dual-Granularity TF-IDF Features...")
word_vectorizer = TfidfVectorizer(
    ngram_range=(1, 3), 
    max_features=16000, 
    sublinear_tf=True, 
    stop_words='english',
    strip_accents='unicode'
)
char_vectorizer = TfidfVectorizer(
    ngram_range=(3, 5), 
    analyzer='char_wb', 
    max_features=16000, 
    sublinear_tf=True,
    strip_accents='unicode'
)

feature_union = FeatureUnion([
    ('word_tfidf', word_vectorizer),
    ('char_tfidf', char_vectorizer)
])

t0 = time.time()
X_train_vec = feature_union.fit_transform(X_train)
X_test_vec = feature_union.transform(X_test)
print(f"Feature matrix created in {time.time()-t0:.2f}s! Shape: {X_train_vec.shape}")

# Model Benchmarking
print("\n--- Training & Benchmarking Candidate Classifiers ---")

candidates = {
    'Calibrated LinearSVC': CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2500, random_state=42), cv=3),
    'Tuned Logistic Regression': LogisticRegression(C=2.5, max_iter=1000, solver='lbfgs', random_state=42),
    'SGD Modified Huber Classifier': SGDClassifier(loss='modified_huber', alpha=2e-5, max_iter=1000, random_state=42),
    'Complement Naive Bayes': ComplementNB(alpha=0.15)
}

trained_models = {}
for name, clf in candidates.items():
    t_start = time.time()
    clf.fit(X_train_vec, y_train)
    preds = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='weighted')
    prec = precision_score(y_test, preds, average='weighted')
    rec = recall_score(y_test, preds, average='weighted')
    print(f"[{name}] Acc: {acc*100:.2f}% | F1: {f1:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} ({time.time()-t_start:.1f}s)")
    trained_models[name] = clf

# Soft Voting Ensemble
print("\n--- Building Soft Voting Multi-Model Ensemble ---")
ensemble_clf = VotingClassifier(
    estimators=[
        ('svc', trained_models['Calibrated LinearSVC']),
        ('lr', trained_models['Tuned Logistic Regression']),
        ('cnb', trained_models['Complement Naive Bayes'])
    ],
    voting='soft',
    weights=[3.0, 2.5, 1.0]
)

# Fit ensemble (pre-fitted estimators already available, but VotingClassifier wraps cleanly)
ensemble_clf.fit(X_train_vec, y_train)
ens_preds = ensemble_clf.predict(X_test_vec)
ens_acc = accuracy_score(y_test, ens_preds)
ens_f1 = f1_score(y_test, ens_preds, average='weighted')
ens_prec = precision_score(y_test, ens_preds, average='weighted')
ens_rec = recall_score(y_test, ens_preds, average='weighted')

print(f"\n🏆 [Ensemble Result] Test Accuracy: {ens_acc*100:.2f}% | F1: {ens_f1:.4f} | Precision: {ens_prec:.4f} | Recall: {ens_rec:.4f}")
print("\n--- Detailed Classification Report ---")
print(classification_report(y_test, ens_preds, digits=4))

# Export Serialized Model Artifacts
MODEL_PATH = os.path.join(BASE_DIR, "crisismmd_model.pkl")
VEC_PATH = os.path.join(BASE_DIR, "crisismmd_vectorizer.pkl")

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(ensemble_clf, f)

with open(VEC_PATH, 'wb') as f:
    pickle.dump(feature_union, f)

print("====================================================================")
print(f"✅ Champion NLP Model saved successfully to: {MODEL_PATH}")
print(f"✅ Dual-Granularity Vectorizer saved to: {VEC_PATH}")
print("====================================================================")
