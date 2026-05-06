import os
import sys
import logging

# Ensure we are in the correct directory to find modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from anomaly_detector import AnomalyDetector
from log_analyzer import LogAnalyzer
from feedback_loop import FeedbackLoop

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("model-trainer")

def train_all():
    logger.info("Starting complete model training pipeline...")
    
    model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    metrics_csv = os.path.join(os.path.dirname(__file__), "sample_metrics.csv")
    logs_csv = os.path.join(os.path.dirname(__file__), "sample_logs.csv")
    db_path = os.path.join(data_dir, "feedback.db")

    # 1. Train Anomaly Detector (Isolation Forest + Autoencoder)
    logger.info("Training Anomaly Detector...")
    detector = AnomalyDetector(model_dir=model_dir)
    detector.train(metrics_csv)
    
    # 2. Train Log Analyzer (TF-IDF + Logistic Regression)
    logger.info("Training Log Analyzer...")
    analyzer = LogAnalyzer(model_dir=model_dir)
    analyzer.train(logs_csv)
    
    # 3. Train Action Selector (Feedback Loop Random Forest)
    logger.info("Populating Feedback DB and Training Action Selector...")
    feedback = FeedbackLoop(db_path=db_path, model_dir=model_dir)
    
    # Inject 15 successful incidents to trigger training threshold
    mock_data = [
        ({"cpu": 95, "memory": 100000000, "latency": 2.5, "error_rate": 0.05}, "warning", "scale_deployment"),
        ({"cpu": 98, "memory": 100000000, "latency": 3.0, "error_rate": 0.10}, "warning", "scale_deployment"),
        ({"cpu": 90, "memory": 100000000, "latency": 1.5, "error_rate": 0.01}, "normal", "scale_deployment"),
        ({"cpu": 96, "memory": 100000000, "latency": 2.1, "error_rate": 0.04}, "warning", "scale_deployment"),
        ({"cpu": 99, "memory": 100000000, "latency": 3.5, "error_rate": 0.15}, "warning", "scale_deployment"),
        
        ({"cpu": 20, "memory": 300000000, "latency": 0.1, "error_rate": 0.00}, "critical", "restart_pod"),
        ({"cpu": 22, "memory": 350000000, "latency": 0.2, "error_rate": 0.00}, "critical", "restart_pod"),
        ({"cpu": 21, "memory": 400000000, "latency": 0.1, "error_rate": 0.05}, "critical", "restart_pod"),
        ({"cpu": 19, "memory": 500000000, "latency": 5.0, "error_rate": 0.80}, "critical", "restart_pod"),
        ({"cpu": 25, "memory": 250000000, "latency": 0.5, "error_rate": 0.00}, "critical", "restart_pod"),
        
        ({"cpu": 20, "memory": 100000000, "latency": 0.1, "error_rate": 0.00}, "normal", "none"),
        ({"cpu": 21, "memory": 100000000, "latency": 0.1, "error_rate": 0.00}, "normal", "none"),
        ({"cpu": 19, "memory": 100000000, "latency": 0.1, "error_rate": 0.00}, "normal", "none"),
        ({"cpu": 20, "memory": 100000000, "latency": 0.1, "error_rate": 0.00}, "normal", "none"),
        ({"cpu": 22, "memory": 100000000, "latency": 0.1, "error_rate": 0.00}, "normal", "none"),
    ]
    
    for metrics, log_class, action in mock_data:
        feedback.record_action(metrics, log_class, action, success=True)
        
    feedback.retrain_model()
    
    logger.info("All models generated perfectly in the 'models' folder.")

if __name__ == "__main__":
    train_all()
