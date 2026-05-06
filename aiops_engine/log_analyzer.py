# === FILE: aiops_engine/log_analyzer.py ===
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import joblib
import logging

logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self, model_dir: str = "../models"):
        """
        Initializes Log Analyzer using TF-IDF and Logistic Regression.
        """
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.vectorizer_path = os.path.join(self.model_dir, "tfidf_vectorizer.pkl")
        self.classifier_path = os.path.join(self.model_dir, "log_classifier.pkl")
        self.encoder_path = os.path.join(self.model_dir, "label_encoder.pkl")
        
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = LogisticRegression()
        self.encoder = LabelEncoder()
        
        self._load_models()

    def _load_models(self):
        if os.path.exists(self.vectorizer_path):
            self.vectorizer = joblib.load(self.vectorizer_path)
        if os.path.exists(self.classifier_path):
            self.classifier = joblib.load(self.classifier_path)
        if os.path.exists(self.encoder_path):
            self.encoder = joblib.load(self.encoder_path)

    def train(self, data_path: str):
        """
        Trains the log classification model.
        CSV Columns: timestamp, message, label (normal/warning/critical)
        """
        logger.info(f"Training LogAnalyzer on {data_path}")
        df = pd.read_csv(data_path)
        
        X = self.vectorizer.fit_transform(df['message'])
        y = self.encoder.fit_transform(df['label'])
        
        self.classifier.fit(X, y)
        
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.classifier, self.classifier_path)
        joblib.dump(self.encoder, self.encoder_path)
        
        logger.info("LogAnalyzer training complete. Models saved.")

    def classify_log(self, message: str) -> dict:
        """
        Classifies a single log message.
        """
        if not hasattr(self.classifier, "classes_"):
            logger.warning("LogAnalyzer not trained. Returning default.")
            return {"classification": "unknown", "confidence": 0.0}
            
        X_new = self.vectorizer.transform([message])
        pred_idx = self.classifier.predict(X_new)[0]
        probs = self.classifier.predict_proba(X_new)[0]
        
        classification = self.encoder.inverse_transform([pred_idx])[0]
        confidence = float(max(probs))
        
        return {
            "classification": classification,
            "confidence": confidence
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = LogAnalyzer(model_dir="../models")
    analyzer.train("sample_logs.csv")
    test_msg = "Out of memory error in java application"
    print(f"Prediction for '{test_msg}':", analyzer.classify_log(test_msg))
