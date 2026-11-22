"""
RescueAI: Inference Pipeline Module
Loads serialized TF-IDF vectorizer and trained models,
applies preprocessing, and provides multi-class predictions
with class-wise confidence distributions.
"""

import os
import joblib
from typing import Dict, Any, List, Optional
from src.preprocessing import clean_disaster_text

CATEGORY_NAMES = {
    0: "Affected People & Medical Emergencies",
    1: "Infrastructure Damage",
    2: "Rescue & Volunteering",
    3: "Other Relevant Information",
    4: "Not Humanitarian / Irrelevant"
}

CATEGORY_ICONS = {
    0: "🚨",
    1: "🏚️",
    2: "🤝",
    3: "📢",
    4: "🌐"
}

CATEGORY_COLORS = {
    0: "#D9534F",  # Danger Red
    1: "#F0AD4E",  # Warning Orange
    2: "#0275D8",  # Primary Blue
    3: "#5BC0DE",  # Info Cyan
    4: "#6C757D"   # Muted Gray
}


class RescueAIInferencePipeline:
    def __init__(
        self,
        model_name: str = "champion",
        models_dir: str = "models"
    ):
        self.models_dir = models_dir
        self.model_name = model_name
        self.vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.joblib")
        
        # Select appropriate model file
        model_file_map = {
            "champion": "logistic_regression_champion.joblib",
            "logistic_regression": "logistic_regression_champion.joblib",
            "linear_svm": "linear_svm_model.joblib",
            "naive_bayes": "naive_bayes_model.joblib",
            "random_forest": "random_forest_model.joblib"
        }
        
        target_file = model_file_map.get(model_name, "logistic_regression_champion.joblib")
        self.model_path = os.path.join(models_dir, target_file)
        
        # Load artifacts
        if not os.path.exists(self.model_path) or not os.path.exists(self.vectorizer_path):
            raise FileNotFoundError(
                f"Model artifacts not found in '{models_dir}'. Please train and serialize models first."
            )
            
        self.vectorizer = joblib.load(self.vectorizer_path)
        self.model = joblib.load(self.model_path)
        self.categories = CATEGORY_NAMES

    def predict(self, raw_message: str) -> Dict[str, Any]:
        """
        Classifies a raw disaster text message and returns category,
        confidence score, and full probability distribution.
        """
        clean_text = clean_disaster_text(raw_message)
        
        # Edge case: Empty after cleaning
        if not clean_text.strip():
            return {
                "raw_message": raw_message,
                "clean_text": "",
                "predicted_label": 4,
                "predicted_category": self.categories[4],
                "icon": CATEGORY_ICONS[4],
                "color": CATEGORY_COLORS[4],
                "confidence": 0.0,
                "probabilities": {self.categories[i]: 0.20 for i in range(5)}
            }
            
        # Feature extraction
        X_vec = self.vectorizer.transform([clean_text])
        
        # Inference
        pred_label = int(self.model.predict(X_vec)[0])
        
        # Probability estimation
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_vec)[0]
            confidence = float(probs[pred_label])
        else:
            # Fallback for models without native probability
            probs = [0.2] * 5
            probs[pred_label] = 1.0
            confidence = 1.0
            
        prob_dict = {self.categories[i]: round(float(probs[i]), 4) for i in range(len(probs))}
        
        return {
            "raw_message": raw_message,
            "clean_text": clean_text,
            "predicted_label": pred_label,
            "predicted_category": self.categories[pred_label],
            "icon": CATEGORY_ICONS[pred_label],
            "color": CATEGORY_COLORS[pred_label],
            "confidence": round(confidence, 4),
            "probabilities": prob_dict
        }

    def predict_batch(self, raw_messages: List[str]) -> List[Dict[str, Any]]:
        """Classifies a list of messages."""
        return [self.predict(msg) for msg in raw_messages]
