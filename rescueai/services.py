"""
RescueAI Core Services: Inference Engine, Data Access, Interpretability, and Evaluation.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score, recall_score
from src.preprocessing import clean_disaster_text
from rescueai.constants import (
    CATEGORY_NAMES, CATEGORY_CONFIG, DISASTER_EVENTS,
    snowflake_to_iso
)
from rescueai.database import (
    get_all_triage_statuses, get_db_connection, DB_PATH_DEFAULT
)


class DataService:
    """Manages processed CrisisMMD datasets, snowflake timestamps, and test set cache."""

    def __init__(self, data_dir: str = "data/processed", models_service: Optional['ModelService'] = None):
        self.data_dir = data_dir
        self.models_service = models_service
        
        # Load parquet splits
        train_path = os.path.join(data_dir, "train_processed.parquet")
        dev_path = os.path.join(data_dir, "dev_processed.parquet")
        test_path = os.path.join(data_dir, "test_processed.parquet")
        
        if not os.path.exists(test_path):
            raise FileNotFoundError(f"Processed dataset not found at {data_dir}. Please run preprocessing first.")
            
        self.df_train = pd.read_parquet(train_path) if os.path.exists(train_path) else pd.DataFrame()
        self.df_dev = pd.read_parquet(dev_path) if os.path.exists(dev_path) else pd.DataFrame()
        self.df_test = pd.read_parquet(test_path)
        
        # Compute real snowflake timestamps
        for df in [self.df_train, self.df_dev, self.df_test]:
            if not df.empty and "tweet_id" in df.columns:
                df["timestamp"] = df["tweet_id"].apply(snowflake_to_iso)
                
        # Precompute in-memory predictions for the entire test set
        self._precompute_test_cache()

    def _precompute_test_cache(self):
        """Computes champion model predictions for all test messages at startup."""
        if self.models_service is None:
            return
            
        df = self.df_test.copy()
        X_vec = self.models_service.vectorizer.transform(df["clean_text"])
        preds = self.models_service.champion_model.predict(X_vec)
        probs = self.models_service.champion_model.predict_proba(X_vec)
        
        df["predicted_label"] = preds.astype(int)
        df["predicted_category"] = [CATEGORY_NAMES[p] for p in preds]
        df["confidence"] = np.max(probs, axis=1).round(4)
        df["probabilities"] = [
            {CATEGORY_NAMES[i]: round(float(p[i]), 4) for i in range(5)}
            for p in probs
        ]
        df["is_correct"] = (df["target_label"].astype(int) == df["predicted_label"]).astype(bool)
        df["urgency"] = [CATEGORY_CONFIG[p]["urgency"] for p in preds]
        
        # Sort chronologically by snowflake timestamp
        df = df.sort_values("timestamp", ascending=True).reset_index(drop=True)
        self.test_cache = df

    def get_events_summary(self) -> List[Dict[str, Any]]:
        """Aggregates test set and event metrics across the 7 real disasters."""
        triage_map = get_all_triage_statuses()
        results = []
        
        for event_id, meta in DISASTER_EVENTS.items():
            ev_df = self.test_cache[self.test_cache["event_name"] == event_id]
            total_msgs = len(ev_df)
            
            # Category breakdown
            counts_by_class = {cat: 0 for cat in CATEGORY_NAMES.values()}
            for cat, count in ev_df["predicted_category"].value_counts().items():
                counts_by_class[cat] = int(count)
                
            urgency_counts = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
            for urg, count in ev_df["urgency"].value_counts().items():
                urgency_counts[urg] = int(count)
                
            high_urgency_pct = (
                round((urgency_counts["High"] / total_msgs) * 100, 1)
                if total_msgs > 0 else 0.0
            )
            
            start_date = ev_df["timestamp"].min() if total_msgs > 0 else "2017-01-01"
            end_date = ev_df["timestamp"].max() if total_msgs > 0 else "2017-12-31"
            
            results.append({
                "event_id": event_id,
                "display_name": meta["display_name"],
                "disaster_type": meta["disaster_type"],
                "lat": meta["lat"],
                "lon": meta["lon"],
                "source": meta["source"],
                "total_messages": total_msgs,
                "start_date": start_date,
                "end_date": end_date,
                "counts_by_class": counts_by_class,
                "urgency_counts": urgency_counts,
                "high_urgency_percent": high_urgency_pct
            })
            
        return results

    def get_messages(
        self,
        split: str = "test",
        event: Optional[str] = None,
        true_cls: Optional[int] = None,
        pred_cls: Optional[int] = None,
        correct: Optional[bool] = None,
        min_conf: Optional[float] = None,
        q: Optional[str] = None,
        status: Optional[str] = None,
        sort: str = "timestamp",
        order: str = "desc",
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Filters, sorts, and paginates messages with live SQLite triage status."""
        # Select target split
        df = self.test_cache if split == "test" else self.df_train if split == "train" else self.df_dev
        
        # Apply filters
        if event:
            df = df[df["event_name"] == event]
        if true_cls is not None:
            df = df[df["target_label"].astype(int) == int(true_cls)]
        if pred_cls is not None and "predicted_label" in df.columns:
            df = df[df["predicted_label"] == int(pred_cls)]
        if correct is not None and "is_correct" in df.columns:
            df = df[df["is_correct"] == bool(correct)]
        if min_conf is not None and "confidence" in df.columns:
            df = df[df["confidence"] >= float(min_conf)]
        if q:
            df = df[df["tweet_text"].str.contains(q, case=False, na=False)]
            
        # Merge triage statuses from SQLite
        triage_map = get_all_triage_statuses()
        
        if status:
            if status == "unreviewed":
                df = df[~df["tweet_id"].isin(triage_map.keys()) | (df["tweet_id"].map(triage_map) == "unreviewed")]
            else:
                df = df[df["tweet_id"].map(triage_map) == status]
                
        total = len(df)
        
        # Sorting
        ascending = (order.lower() == "asc")
        if sort in df.columns:
            df = df.sort_values(sort, ascending=ascending)
        elif sort == "timestamp":
            df = df.sort_values("timestamp", ascending=ascending)
            
        # Pagination
        offset = (page - 1) * size
        paged_df = df.iloc[offset:offset + size]
        
        items = []
        for _, row in paged_df.iterrows():
            tid = str(row["tweet_id"])
            items.append({
                "tweet_id": tid,
                "event_name": row["event_name"],
                "tweet_text": row["tweet_text"],
                "clean_text": row["clean_text"],
                "timestamp": row.get("timestamp", snowflake_to_iso(tid)),
                "true_label": int(row["target_label"]),
                "true_category": CATEGORY_NAMES[int(row["target_label"])],
                "predicted_label": int(row.get("predicted_label", row["target_label"])),
                "predicted_category": row.get("predicted_category", CATEGORY_NAMES[int(row["target_label"])]),
                "confidence": float(row.get("confidence", 1.0)),
                "urgency": row.get("urgency", CATEGORY_CONFIG[int(row.get("predicted_label", 0))]["urgency"]),
                "is_correct": bool(row.get("is_correct", True)),
                "status": triage_map.get(tid, "unreviewed"),
                "probabilities": row.get("probabilities", {})
            })
            
        return items, total

    def get_message_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single message with rich feature attributions."""
        ev_df = self.test_cache[self.test_cache["tweet_id"].astype(str) == str(tweet_id)]
        if ev_df.empty:
            # Fallback to train or dev
            for split_df in [self.df_train, self.df_dev]:
                match = split_df[split_df["tweet_id"].astype(str) == str(tweet_id)]
                if not match.empty:
                    ev_df = match
                    break
        if ev_df.empty:
            return None
            
        row = ev_df.iloc[0]
        tid = str(row["tweet_id"])
        triage_map = get_all_triage_statuses()
        
        clean_text = row["clean_text"]
        pred_label = int(row.get("predicted_label", row["target_label"]))
        
        terms = []
        if self.models_service:
            terms = self.models_service.explain_text(clean_text, pred_label)
            
        return {
            "tweet_id": tid,
            "event_name": row["event_name"],
            "tweet_text": row["tweet_text"],
            "clean_text": clean_text,
            "timestamp": row.get("timestamp", snowflake_to_iso(tid)),
            "true_label": int(row["target_label"]),
            "true_category": CATEGORY_NAMES[int(row["target_label"])],
            "predicted_label": pred_label,
            "predicted_category": row.get("predicted_category", CATEGORY_NAMES[pred_label]),
            "confidence": float(row.get("confidence", 1.0)),
            "probabilities": row.get("probabilities", {}),
            "urgency": row.get("urgency", CATEGORY_CONFIG[pred_label]["urgency"]),
            "is_correct": bool(row.get("is_correct", pred_label == int(row["target_label"]))),
            "status": triage_map.get(tid, "unreviewed"),
            "terms": terms
        }

    def get_timeline(self, event: Optional[str] = None, bucket: str = "day") -> List[Dict[str, Any]]:
        """Computes message time-series frequency buckets per category."""
        df = self.test_cache.copy()
        if event:
            df = df[df["event_name"] == event]
            
        if df.empty:
            return []
            
        # Parse timestamp to datetime for grouping
        df["dt"] = pd.to_datetime(df["timestamp"], format="ISO8601")
        freq = "1D" if bucket == "day" else "1h"
        
        grouped = df.groupby([pd.Grouper(key="dt", freq=freq), "predicted_category"]).size().unstack(fill_value=0)
        
        timeline = []
        for dt_idx, row in grouped.iterrows():
            total = int(row.sum())
            if total > 0:
                timeline.append({
                    "time": dt_idx.isoformat(),
                    "total": total,
                    "counts": {cat: int(row.get(cat, 0)) for cat in CATEGORY_NAMES.values()}
                })
        return timeline

    def get_replay_stream(self, event: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns ordered stream of test messages for chronological operations playback."""
        df = self.test_cache
        if event:
            df = df[df["event_name"] == event]
            
        # Strictly chronological order
        df = df.sort_values("timestamp", ascending=True)
        
        stream = []
        for _, row in df.iterrows():
            stream.append({
                "tweet_id": str(row["tweet_id"]),
                "timestamp": row["timestamp"],
                "event_name": row["event_name"],
                "tweet_text": row["tweet_text"],
                "clean_text": row["clean_text"],
                "true_label": int(row["target_label"]),
                "true_category": CATEGORY_NAMES[int(row["target_label"])],
                "predicted_label": int(row["predicted_label"]),
                "predicted_category": row["predicted_category"],
                "confidence": float(row["confidence"]),
                "probabilities": row["probabilities"],
                "urgency": row["urgency"]
            })
        return stream


class ModelService:
    """Manages loaded Scikit-Learn models, inference, explainability, and diagnostics."""

    def __init__(self, models_dir: str = "models", reports_dir: str = "reports"):
        self.models_dir = models_dir
        self.reports_dir = reports_dir
        
        # Load Vectorizer
        vec_path = os.path.join(models_dir, "tfidf_vectorizer.joblib")
        if not os.path.exists(vec_path):
            raise FileNotFoundError(f"Missing vectorizer at {vec_path}. Run training pipeline first.")
        self.vectorizer = joblib.load(vec_path)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())
        
        # Load Models
        self.models = {
            "logistic_regression": joblib.load(os.path.join(models_dir, "logistic_regression_champion.joblib")),
            "linear_svm": joblib.load(os.path.join(models_dir, "linear_svm_model.joblib")),
            "naive_bayes": joblib.load(os.path.join(models_dir, "naive_bayes_model.joblib")),
            "random_forest": joblib.load(os.path.join(models_dir, "random_forest_model.joblib"))
        }
        self.champion_model = self.models["logistic_regression"]
        
        # Load Benchmarks
        bench_path = os.path.join(reports_dir, "model_benchmarks.json")
        if os.path.exists(bench_path):
            with open(bench_path, "r") as f:
                self.benchmarks = json.load(f)
        else:
            self.benchmarks = []

    def predict(self, raw_text: str, model_name: str = "champion") -> Dict[str, Any]:
        """Classifies text with calibrated probabilities, low-confidence alerts, and term attribution."""
        model_key = "logistic_regression" if model_name in ("champion", "logistic_regression") else model_name
        model = self.models.get(model_key, self.champion_model)
        
        clean_text = clean_disaster_text(raw_text)
        if not clean_text.strip():
            return {
                "raw_text": raw_text,
                "clean_text": "",
                "predicted_label": 4,
                "predicted_category": CATEGORY_NAMES[4],
                "urgency": "None",
                "confidence": 0.20,
                "probabilities": {cat: 0.20 for cat in CATEGORY_NAMES.values()},
                "is_low_confidence": True,
                "runner_up": None,
                "terms": []
            }
            
        X = self.vectorizer.transform([clean_text])
        probs = model.predict_proba(X)[0]
        pred_label = int(np.argmax(probs))
        confidence = round(float(probs[pred_label]), 4)
        
        prob_dict = {CATEGORY_NAMES[i]: round(float(probs[i]), 4) for i in range(len(probs))}
        
        # Find runner-up
        sorted_indices = np.argsort(probs)[::-1]
        runner_up_idx = int(sorted_indices[1])
        runner_up_conf = round(float(probs[runner_up_idx]), 4)
        
        # Low confidence criteria: top < 0.50 OR gap < 0.10
        gap = confidence - runner_up_conf
        is_low_conf = bool(confidence < 0.50 or gap < 0.10)
        
        runner_up = {
            "label": runner_up_idx,
            "category": CATEGORY_NAMES[runner_up_idx],
            "confidence": runner_up_conf,
            "gap": round(gap, 4)
        }
        
        # Feature attributions (words pushing toward predicted class vs runner-up)
        terms = self.explain_text(clean_text, pred_label, runner_up_idx=runner_up_idx)
        
        return {
            "raw_text": raw_text,
            "clean_text": clean_text,
            "predicted_label": pred_label,
            "predicted_category": CATEGORY_NAMES[pred_label],
            "urgency": CATEGORY_CONFIG[pred_label]["urgency"],
            "confidence": confidence,
            "probabilities": prob_dict,
            "is_low_confidence": is_low_conf,
            "runner_up": runner_up,
            "terms": terms
        }

    def detect_event(self, text: str) -> Optional[Dict[str, Any]]:
        """
        AI heuristic event detector: extracts disaster and geographical keywords
        to automatically assign coordinates and map focus.
        """
        lower = text.lower()
        keyword_map = {
            "hurricane_harvey": ["harvey", "houston", "harris", "texas", "bayou", "corpus christi", "rockport", "galveston", "beaumont", "katy", "dickinson", "pasadena"],
            "hurricane_irma": ["irma", "florida", "miami", "keys", "key west", "tampa", "naples", "barbuda", "marathon", "islamorada", "homestead"],
            "hurricane_maria": ["maria", "puerto rico", "san juan", "ponce", "utuado", "arecibo", "fajardo", "vieques", "culebra"],
            "california_wildfires": ["wildfire", "firestorm", "sonoma", "santa rosa", "napa", "coffey park", "calistoga", "calfire", "tubbs", "kenwood"],
            "mexico_earthquake": ["mexico", "sismo", "terremoto", "earthquake", "puebla", "jojutla", "cdmx", "mexico city", "alvaro obregon", "morelos", "raboso", "atlixco"],
            "srilanka_floods": ["sri lanka", "lanka", "ratnapura", "kalutara", "galle", "matara", "mudslide", "kalu ganga", "bulathsinhala"],
            "iraq_iran_earthquake": ["iran", "iraq", "kermanshah", "sarpol", "ezgeleh", "halabja", "qasr-e shirin", "kurdish"]
        }
        for ev_id, kws in keyword_map.items():
            matches = [kw for kw in kws if kw in lower]
            if matches:
                ev_meta = DISASTER_EVENTS[ev_id]
                return {
                    "event_id": ev_id,
                    "display_name": ev_meta["display_name"],
                    "matched_keywords": matches,
                    "lat": ev_meta["lat"],
                    "lon": ev_meta["lon"],
                    "confidence": min(0.99, 0.65 + len(matches) * 0.12)
                }
        return None

    def explain_text(self, clean_text: str, pred_label: int, runner_up_idx: Optional[int] = None, top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Computes honest term attributions using TF-IDF weights * model coefficients.
        Identifies whether a term favors the predicted class or the runner-up class.
        """
        if not clean_text.strip():
            return []
            
        X = self.vectorizer.transform([clean_text])
        active_indices = X.nonzero()[1]
        if len(active_indices) == 0:
            return []
            
        # Use champion model coefficients (Logistic Regression)
        clf = self.champion_model
        pred_weights = clf.coef_[pred_label]
        runner_weights = clf.coef_[runner_up_idx] if runner_up_idx is not None else None
        
        term_scores = []
        for idx in active_indices:
            term = str(self.feature_names[idx])
            tfidf_val = float(X[0, idx])
            pred_contrib = tfidf_val * float(pred_weights[idx])
            
            runner_contrib = 0.0
            if runner_weights is not None and runner_up_idx is not None:
                runner_contrib = tfidf_val * float(runner_weights[idx])
                favored = "predicted" if pred_contrib >= runner_contrib else "runner_up"
                category_name = CATEGORY_NAMES[pred_label] if favored == "predicted" else CATEGORY_NAMES[runner_up_idx]
            else:
                favored = "predicted"
                category_name = CATEGORY_NAMES[pred_label]
                
            term_scores.append({
                "term": term,
                "score": round(pred_contrib, 4),
                "runner_score": round(runner_contrib, 4),
                "favored": favored,
                "category": category_name
            })
            
        # Sort by magnitude of contribution
        term_scores.sort(key=lambda x: abs(x["score"]), reverse=True)
        return term_scores[:top_k]

    def predict_ablate(self, raw_text: str, remove_tokens: List[str]) -> Dict[str, Any]:
        """
        Removes selected tokens to demonstrate Bag-of-Words causal contribution.
        Returns original vs ablated prediction comparison.
        """
        orig_pred = self.predict(raw_text)
        
        # Token ablation
        clean = orig_pred["clean_text"]
        words = clean.split()
        ablated_words = [w for w in words if w.lower() not in [r.lower() for r in remove_tokens]]
        ablated_text = " ".join(ablated_words)
        
        new_pred = self.predict(ablated_text)
        
        return {
            "original": orig_pred,
            "ablated": new_pred,
            "removed_tokens": remove_tokens,
            "prediction_changed": bool(orig_pred["predicted_label"] != new_pred["predicted_label"]),
            "confidence_delta": round(new_pred["confidence"] - orig_pred["confidence"], 4)
        }

    def predict_batch(self, raw_messages: List[str], max_rows: int = 5000) -> Dict[str, Any]:
        """Performs vectorized batch classification for uploaded CSV datasets."""
        capped_messages = raw_messages[:max_rows]
        cleaned_list = [clean_disaster_text(msg) for msg in capped_messages]
        
        X_vec = self.vectorizer.transform(cleaned_list)
        preds = self.champion_model.predict(X_vec)
        probs = self.champion_model.predict_proba(X_vec)
        
        confidences = np.max(probs, axis=1).round(4)
        
        items = []
        counts_by_class = {cat: 0 for cat in CATEGORY_NAMES.values()}
        
        for i, (raw, pred_idx, conf) in enumerate(zip(capped_messages, preds, confidences)):
            cat_name = CATEGORY_NAMES[pred_idx]
            counts_by_class[cat_name] += 1
            items.append({
                "index": i + 1,
                "text": raw,
                "predicted_label": int(pred_idx),
                "predicted_category": cat_name,
                "confidence": float(conf),
                "urgency": CATEGORY_CONFIG[pred_idx]["urgency"]
            })
            
        mean_conf = float(np.mean(confidences)) if len(confidences) > 0 else 0.0
        
        return {
            "total_rows": len(items),
            "mean_confidence": round(mean_conf, 4),
            "category_summary": counts_by_class,
            "predictions": items
        }

    def get_confusion_matrix_data(self, model_name: str, normalize: bool = False, test_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Calculates 5x5 confusion matrix on real test data."""
        model_key = "logistic_regression" if model_name in ("champion", "logistic_regression") else model_name
        model = self.models.get(model_key, self.champion_model)
        
        if test_df is None or test_df.empty:
            return {"matrix": [], "labels": list(CATEGORY_NAMES.values())}
            
        y_true = test_df["target_label"].astype(int).values
        X_vec = self.vectorizer.transform(test_df["clean_text"])
        y_pred = model.predict(X_vec)
        
        cm = confusion_matrix(y_true, y_pred, labels=list(range(5)))
        if normalize:
            cm = (cm.astype('float') / cm.sum(axis=1)[:, np.newaxis])
            cm = np.nan_to_num(cm).round(4)
            
        return {
            "model_name": model_key,
            "normalized": normalize,
            "labels": list(CATEGORY_NAMES.values()),
            "matrix": cm.tolist()
        }

    def get_confusion_cell_samples(self, model_name: str, true_label: int, pred_label: int, test_df: pd.DataFrame, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """Retrieves exact test tweets for a specific cell in the confusion matrix."""
        model_key = "logistic_regression" if model_name in ("champion", "logistic_regression") else model_name
        model = self.models.get(model_key, self.champion_model)
        
        X_vec = self.vectorizer.transform(test_df["clean_text"])
        preds = model.predict(X_vec)
        
        mask = (test_df["target_label"].astype(int) == int(true_label)) & (preds == int(pred_label))
        cell_df = test_df[mask]
        total = len(cell_df)
        
        offset = (page - 1) * size
        paged = cell_df.iloc[offset:offset + size]
        
        items = []
        for _, row in paged.iterrows():
            items.append({
                "tweet_id": str(row["tweet_id"]),
                "event_name": row["event_name"],
                "tweet_text": row["tweet_text"],
                "clean_text": row["clean_text"],
                "true_label": int(true_label),
                "true_category": CATEGORY_NAMES[int(true_label)],
                "predicted_label": int(pred_label),
                "predicted_category": CATEGORY_NAMES[int(pred_label)]
            })
            
        return {
            "true_label": int(true_label),
            "true_category": CATEGORY_NAMES[int(true_label)],
            "predicted_label": int(pred_label),
            "predicted_category": CATEGORY_NAMES[int(pred_label)],
            "total_count": total,
            "page": page,
            "size": size,
            "items": items
        }

    def get_threshold_analysis(self, model_name: str, t: float, test_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates the manual review confidence trade-off:
        Messages with confidence < t are routed to human review; metrics are computed on retained set.
        """
        model_key = "logistic_regression" if model_name in ("champion", "logistic_regression") else model_name
        model = self.models.get(model_key, self.champion_model)
        
        X_vec = self.vectorizer.transform(test_df["clean_text"])
        probs = model.predict_proba(X_vec)
        preds = np.argmax(probs, axis=1)
        confs = np.max(probs, axis=1)
        y_true = test_df["target_label"].astype(int).values
        
        total = len(test_df)
        retained_mask = (confs >= t)
        flagged_mask = ~retained_mask
        
        flagged_count = int(np.sum(flagged_mask))
        retained_count = int(np.sum(retained_mask))
        flagged_pct = round((flagged_count / total) * 100, 2) if total > 0 else 0.0
        
        if retained_count > 0:
            retained_acc = round(float(accuracy_score(y_true[retained_mask], preds[retained_mask])), 4)
            retained_f1 = round(float(f1_score(y_true[retained_mask], preds[retained_mask], average="macro", zero_division=0)), 4)
            recalls = recall_score(y_true[retained_mask], preds[retained_mask], average=None, labels=list(range(5)), zero_division=0)
            per_class_recall = {CATEGORY_NAMES[i]: round(float(recalls[i]), 4) for i in range(5)}
        else:
            retained_acc = 0.0
            retained_f1 = 0.0
            per_class_recall = {CATEGORY_NAMES[i]: 0.0 for i in range(5)}
            
        return {
            "model_name": model_key,
            "threshold": round(float(t), 2),
            "total_messages": total,
            "flagged_count": flagged_count,
            "flagged_percent": flagged_pct,
            "retained_count": retained_count,
            "retained_accuracy": retained_acc,
            "retained_macro_f1": retained_f1,
            "per_class_recall": per_class_recall
        }

    def get_top_terms_by_class(self, cls_idx: Optional[int] = None, top_k: int = 15) -> List[Dict[str, Any]]:
        """Extracts top positive n-gram coefficients per class from champion model."""
        clf = self.champion_model
        results = []
        
        classes_to_query = [cls_idx] if cls_idx is not None else list(range(5))
        for c in classes_to_query:
            coefs = clf.coef_[c]
            top_indices = np.argsort(coefs)[::-1][:top_k]
            terms = [
                {"term": str(self.feature_names[i]), "weight": round(float(coefs[i]), 4)}
                for i in top_indices if coefs[i] > 0
            ]
            results.append({
                "class_index": c,
                "category_name": CATEGORY_NAMES[c],
                "color": CATEGORY_CONFIG[c]["color"],
                "terms": terms
            })
            
        return results
