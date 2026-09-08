"""
LifeLine ML Module 1: Natural Language Processing (NLP) Triage Pipeline
Author: ML Engineer 1
Description: Preprocesses crisis text datasets and fine-tunes DistilBERT for disaster category & urgency classification.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

print("=== LifeLine NLP Pipeline Initializer ===")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

# Category Mapping
LABEL_MAPPING = {
    0: "Flood",
    1: "Fire",
    2: "Earthquake",
    3: "Landslide",
    4: "Medical Emergency"
}

MODEL_NAME = "distilbert-base-uncased"

def load_tokenizer():
    print(f"Loading tokenizer for {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return tokenizer

def preprocess_sample_data():
    sample_texts = [
        "Severe flood water rising to 2nd floor, family trapped near riverside road",
        "Huge fire outbreak at chemical factory, black smoke spreading fast",
        "Landslide blocked main highway, vehicles buried under mud",
        "Earthquake tremor damaged residential building wall, medical emergency required",
        "Minor rain water logging on street"
    ]
    sample_labels = [0, 1, 3, 2, 0]
    return sample_texts, sample_labels

def main():
    tokenizer = load_tokenizer()
    texts, labels = preprocess_sample_data()
    
    encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)
    print("Sample Tokenization Complete:")
    print("Input IDs shape:", [len(x) for x in encodings['input_ids']])
    print("NLP Pipeline Environment Ready for Month 2 Model Training!")

if __name__ == "__main__":
    main()
