# === FILE: aiops_engine/pipeline.py ===
import asyncio
import time
import requests
import logging

from anomaly_detector import AnomalyDetector
from log_analyzer import LogAnalyzer
from decision_engine import DecisionEngine
from feedback_loop import FeedbackLoop
from k8s_actions import K8sActions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("aiops-pipeline")

class AIOpsPipeline:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector(model_dir="../models")
        self.log_analyzer = LogAnalyzer(model_dir="../models")
        self.feedback_loop = FeedbackLoop(db_path="../data/feedback.db", model_dir="../models")
        self.decision_engine = DecisionEngine(feedback_loop=self.feedback_loop)
        self.k8s_actions = K8sActions(dry_run=True)
        
        # Load sample models
        try:
            self.anomaly_detector.train("sample_metrics.csv")
            self.log_analyzer.train("sample_logs.csv")
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")

    def fetch_metrics(self) -> dict:
        """Fetch metrics from Prometheus (mocked for this example)."""
        try:
            # In real scenario, query Prometheus API
            # response = requests.get('http://prometheus:9090/api/v1/query?query=app_cpu_usage_percent')
            # Mocking fetch
            return {
                "cpu": 25.0,
                "memory": 150000000,
                "latency": 0.15,
                "error_rate": 0.0
            }
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return {}

    def fetch_logs(self) -> str:
        """Fetch latest logs from Elasticsearch (mocked)."""
        return "Service started successfully"

    async def run_loop(self):
        logger.info("Starting AIOps closed-loop pipeline...")
        while True:
            try:
                # 1. Observe (Collect)
                metrics = self.fetch_metrics()
                log_message = self.fetch_logs()
                
                if not metrics:
                    await asyncio.sleep(30)
                    continue

                # 2. Detect (Analyze)
                anomaly_result = self.anomaly_detector.predict(metrics)
                log_result = self.log_analyzer.classify_log(log_message)
                
                # 3. Decide
                decision = self.decision_engine.decide(anomaly_result, log_result, metrics)
                action = decision.get("action")
                
                # 4. Act
                if action != "none" and action != "alert_only":
                    logger.info(f"Taking action: {action}. Reason: {decision.get('reason')}")
                    success = False
                    if action == "restart_pod":
                        success = self.k8s_actions.restart_pod("aiops", "microservice")
                    elif action == "scale_deployment":
                        success = self.k8s_actions.scale_deployment("aiops", "microservice", 3)
                        
                    # 5. Learn (Record Feedback)
                    self.feedback_loop.record_action(metrics, log_result.get("classification", "normal"), action, success)
                else:
                    logger.debug("System healthy. No action needed.")
                    
            except Exception as e:
                logger.error(f"Error in pipeline loop: {e}")
                
            # Wait 30 seconds before next cycle
            await asyncio.sleep(30)

if __name__ == "__main__":
    pipeline = AIOpsPipeline()
    asyncio.run(pipeline.run_loop())
