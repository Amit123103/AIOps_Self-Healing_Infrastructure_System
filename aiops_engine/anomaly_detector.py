# === FILE: aiops_engine/anomaly_detector.py ===
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, model_dir: str = "../models"):
        """
        Initializes Anomaly Detector using Isolation Forest.
        Optimized for low-memory environments.
        """
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        self.if_model_path = os.path.join(self.model_dir, "isolation_forest.pkl")
        
        self.scaler = StandardScaler()
        self.if_model = None
        
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
            if os.path.exists(self.if_model_path):
                self.if_model = joblib.load(self.if_model_path)
                logger.info("Anomaly detection models loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load models: {e}")

    def train(self, data_path: str):
        """
        Trains the Isolation Forest model.
        """
        logger.info(f"Training AnomalyDetector on {data_path}")
        df = pd.read_csv(data_path)
        
        features = ['cpu', 'memory', 'latency', 'error_rate']
        X = df[features].values
        
        # Preprocessing
        X_scaled = self.scaler.fit_transform(X)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Train Isolation Forest
        self.if_model = IsolationForest(contamination=0.1, random_state=42)
        self.if_model.fit(X_scaled)
        joblib.dump(self.if_model, self.if_model_path)
        
        logger.info("Training complete. Models saved.")

    def predict(self, metrics: dict) -> dict:
        """
        Real-time scoring using Isolation Forest.
        """
        if not self.if_model:
            return {"is_anomaly": False, "anomaly_score": 0.0}
            
        features = np.array([[
            metrics.get('cpu', 0),
            metrics.get('memory', 0),
            metrics.get('latency', 0),
            metrics.get('error_rate', 0)
        ]])
        
        try:
            X_scaled = self.scaler.transform(features)
            if_score = self.if_model.decision_function(X_scaled)[0] # higher is more normal
            if_pred = self.if_model.predict(X_scaled)[0] # -1 for anomaly, 1 for normal
            
            # Convert decision function to a positive anomaly score (lower is more anomalous)
            # Normalizing it: score > 0 is normal, score < 0 is anomaly.
            anomaly_score = float(-if_score) 
            
            return {
                "is_anomaly": bool(if_pred == -1),
                "anomaly_score": anomaly_score,
                "if_prediction": int(if_pred)
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"is_anomaly": False, "anomaly_score": 0.0}
