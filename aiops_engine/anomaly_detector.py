# === FILE: aiops_engine/anomaly_detector.py ===
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense
import joblib
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, model_dir: str = "../models"):
        """
        Initializes Anomaly Detector using Isolation Forest and Autoencoder.
        """
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        self.if_model_path = os.path.join(self.model_dir, "isolation_forest.pkl")
        self.ae_model_path = os.path.join(self.model_dir, "autoencoder.h5")
        
        self.scaler = StandardScaler()
        self.if_model = None
        self.ae_model = None
        
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
            if os.path.exists(self.if_model_path):
                self.if_model = joblib.load(self.if_model_path)
            if os.path.exists(self.ae_model_path):
                self.ae_model = load_model(self.ae_model_path)
        except Exception as e:
            logger.warning(f"Failed to load models (will need retraining): {e}")

    def build_autoencoder(self, input_dim: int) -> Sequential:
        """Builds a simple autoencoder model."""
        model = Sequential([
            Dense(16, activation='relu', input_shape=(input_dim,)),
            Dense(8, activation='relu'),
            Dense(16, activation='relu'),
            Dense(input_dim, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train(self, data_path: str):
        """
        Trains models on the given CSV data.
        Assumes columns: timestamp, cpu, memory, latency, error_rate
        """
        logger.info(f"Training AnomalyDetector on {data_path}")
        df = pd.read_csv(data_path)
        
        # Features to train on
        features = ['cpu', 'memory', 'latency', 'error_rate']
        X = df[features].values
        
        # Preprocessing
        X_scaled = self.scaler.fit_transform(X)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Train Isolation Forest
        self.if_model = IsolationForest(contamination=0.1, random_state=42)
        self.if_model.fit(X_scaled)
        joblib.dump(self.if_model, self.if_model_path)
        
        # Train Autoencoder
        self.ae_model = self.build_autoencoder(X_scaled.shape[1])
        self.ae_model.fit(X_scaled, X_scaled, epochs=50, batch_size=16, validation_split=0.1, verbose=0)
        self.ae_model.save(self.ae_model_path)
        
        logger.info("Training complete. Models saved.")

    def predict(self, metrics: dict) -> dict:
        """
        Real-time scoring of a single metrics point.
        Returns anomaly scores and boolean anomaly flag.
        """
        if not self.if_model or not self.ae_model:
            logger.warning("Models not loaded. Returning defaults.")
            return {"is_anomaly": False, "anomaly_score": 0.0}
            
        features = np.array([[
            metrics.get('cpu', 0),
            metrics.get('memory', 0),
            metrics.get('latency', 0),
            metrics.get('error_rate', 0)
        ]])
        
        X_scaled = self.scaler.transform(features)
        
        # Isolation Forest prediction
        if_pred = self.if_model.predict(X_scaled)[0] # -1 for anomaly, 1 for normal
        
        # Autoencoder prediction (reconstruction error)
        ae_pred = self.ae_model.predict(X_scaled, verbose=0)
        mse = np.mean(np.power(X_scaled - ae_pred, 2))
        
        # Combine logic: if IF says anomaly OR MSE > threshold
        ae_threshold = 2.0
        is_anomaly = bool(if_pred == -1 or mse > ae_threshold)
        
        # Normalize score
        score = float(mse)
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "if_prediction": int(if_pred),
            "ae_mse": float(mse)
        }

if __name__ == "__main__":
    # Test the module locally
    logging.basicConfig(level=logging.INFO)
    detector = AnomalyDetector(model_dir="../models")
    detector.train("sample_metrics.csv")
    test_metrics = {"cpu": 98.0, "memory": 200000000, "latency": 3.5, "error_rate": 0.1}
    print("Prediction:", detector.predict(test_metrics))
