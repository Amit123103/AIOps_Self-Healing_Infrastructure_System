# === FILE: aiops_engine/main.py ===
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any

from anomaly_detector import AnomalyDetector
from log_analyzer import LogAnalyzer
from decision_engine import DecisionEngine
from feedback_loop import FeedbackLoop
from k8s_actions import K8sActions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("aiops-backend")

app = FastAPI(title="AIOps Backend")

# Initialize modules
anomaly_detector = AnomalyDetector(model_dir="../models")
log_analyzer = LogAnalyzer(model_dir="../models")
feedback_loop = FeedbackLoop(db_path="../data/feedback.db", model_dir="../models")
decision_engine = DecisionEngine(feedback_loop=feedback_loop)
k8s_actions = K8sActions(dry_run=True) # Set to False in real production

class MetricsPayload(BaseModel):
    cpu: float
    memory: float
    latency: float
    error_rate: float

class LogPayload(BaseModel):
    message: str

class FeedbackPayload(BaseModel):
    metrics: dict
    log_class: str
    action: str
    success: bool

@app.on_event("startup")
async def startup_event():
    # Train models on startup if necessary files exist
    try:
        anomaly_detector.train("sample_metrics.csv")
        log_analyzer.train("sample_logs.csv")
    except Exception as e:
        logger.error(f"Error during startup model training: {e}")

@app.get("/api/health")
def health_check():
    return {"status": "AIOps engine running"}

@app.post("/api/metrics/ingest")
def ingest_metrics(payload: MetricsPayload):
    metrics = payload.dict()
    anomaly_result = anomaly_detector.predict(metrics)
    return {"status": "ingested", "anomaly_score": anomaly_result}

@app.get("/api/anomalies/latest")
def get_latest_anomalies():
    # In a full system, this would query a TSDB or database
    return {"status": "endpoint ready, implement db fetch"}

@app.post("/api/actions/trigger")
def trigger_action(action_req: Dict[str, Any]):
    action = action_req.get("action")
    if action == "restart_pod":
        res = k8s_actions.restart_pod("aiops", "microservice")
        return {"status": "triggered", "success": res}
    elif action == "scale_deployment":
        res = k8s_actions.scale_deployment("aiops", "microservice", 3)
        return {"status": "triggered", "success": res}
    return {"status": "ignored", "reason": "Unknown action"}

@app.post("/api/feedback/submit")
def submit_feedback(payload: FeedbackPayload, background_tasks: BackgroundTasks):
    feedback_loop.record_action(
        payload.metrics, 
        payload.log_class, 
        payload.action, 
        payload.success
    )
    # Retrain model in background
    background_tasks.add_task(feedback_loop.retrain_model)
    return {"status": "feedback recorded"}

@app.get("/api/actions/history")
def get_history():
    import sqlite3
    try:
        conn = sqlite3.connect("../data/feedback.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return {"history": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
