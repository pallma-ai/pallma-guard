import os
import threading

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class ModelRunner:
    def __init__(self):
        self.ready = False
        self.tokenizer = None
        self.model = None

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        thread = threading.Thread(target=self._load_model)
        thread.start()

    def _load_model(self):
        model_name = "pallma-ai/pallma-guard"
        try:
            print(f"Loading model {model_name}...")

            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name
            ).to(self.device)

            self.tokenizer = AutoTokenizer.from_pretrained(
                "distilbert/distilbert-base-uncased"
            )
            self.model.eval()
            print("Model loaded.")
            self.ready = True
        except Exception as e:
            print(f"Model loading failed: {e}")
            self.ready = False

    def run(self, texts):
        encoded = self.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            logits = self.model(**encoded).logits
            probs = torch.softmax(logits, dim=-1)
        return probs.tolist()
