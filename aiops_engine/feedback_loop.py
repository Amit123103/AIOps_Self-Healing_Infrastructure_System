# === FILE: aiops_engine/feedback_loop.py ===
import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import logging
import time

logger = logging.getLogger(__name__)

class FeedbackLoop:
    def __init__(self, db_path: str = "../data/feedback.db", model_dir: str = "../models"):
        self.db_path = db_path
        self.model_dir = model_dir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.model_path = os.path.join(self.model_dir, "action_selector.pkl")
        self.encoder_path = os.path.join(self.model_dir, "action_encoder.pkl")
        
        self.model = RandomForestClassifier()
        self.encoder = LabelEncoder()
        
        self._init_db()
        self._load_model()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                cpu REAL,
                memory REAL,
                latency REAL,
                error_rate REAL,
                log_class TEXT,
                action_taken TEXT,
                success INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def _load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
            self.model = joblib.load(self.model_path)
            self.encoder = joblib.load(self.encoder_path)

    def record_action(self, metrics: dict, log_class: str, action: str, success: bool):
        """Records an action and its outcome (triplet)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO incidents (timestamp, cpu, memory, latency, error_rate, log_class, action_taken, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            time.time(),
            metrics.get('cpu', 0),
            metrics.get('memory', 0),
            metrics.get('latency', 0),
            metrics.get('error_rate', 0),
            log_class,
            action,
            1 if success else 0
        ))
        conn.commit()
        conn.close()
        logger.info(f"Recorded action {action} with success={success}")

    def retrain_model(self):
        """Retrains the Random Forest based on historical success."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM incidents WHERE success = 1", conn)
        conn.close()

        if len(df) < 10:
            logger.info("Not enough successful data points to retrain ML decision layer (need 10+).")
            return

        # Prepare features and target
        # Simplified: map log_class to integer
        df['log_class_int'] = df['log_class'].map({'normal': 0, 'warning': 1, 'critical': 2}).fillna(0)
        
        X = df[['cpu', 'memory', 'latency', 'error_rate', 'log_class_int']]
        y = self.encoder.fit_transform(df['action_taken'])
        
        self.model.fit(X, y)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.encoder, self.encoder_path)
        logger.info("Retrained Decision Model on historical feedback.")

    def suggest_action(self, metrics: dict, log_class: str) -> str:
        """Suggests an action based on learned patterns."""
        if not hasattr(self.model, "classes_"):
            return "unknown"
            
        log_class_int = {'normal': 0, 'warning': 1, 'critical': 2}.get(log_class, 0)
        X_new = [[
            metrics.get('cpu', 0),
            metrics.get('memory', 0),
            metrics.get('latency', 0),
            metrics.get('error_rate', 0),
            log_class_int
        ]]
        
        try:
            pred_idx = self.model.predict(X_new)[0]
            action = self.encoder.inverse_transform([pred_idx])[0]
            return action
        except Exception as e:
            logger.error(f"Error in ML suggestion: {e}")
            return "unknown"
