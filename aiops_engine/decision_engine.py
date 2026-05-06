# === FILE: aiops_engine/decision_engine.py ===
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DecisionEngine:
    def __init__(self, feedback_loop=None):
        """
        Initializes the Decision Engine.
        Uses rule-based logic and hooks into an optional ML feedback loop.
        """
        self.feedback_loop = feedback_loop

    def decide(self, metrics_anomaly: dict, log_analysis: dict, metrics: dict) -> Dict[str, Any]:
        """
        Makes a decision based on anomaly score, log classification, and raw metrics.
        Returns the chosen action, reason, confidence, and priority.
        """
        action = "none"
        reason = "System normal"
        confidence = 1.0
        priority = "low"

        is_anomaly = metrics_anomaly.get("is_anomaly", False)
        log_class = log_analysis.get("classification", "normal")
        cpu = metrics.get("cpu", 0)
        memory = metrics.get("memory", 0)

        # Rule-based layer
        if is_anomaly or log_class == "critical":
            priority = "high"
            
            if log_class == "critical" and "memory" in str(log_analysis.get("message", "")).lower():
                action = "restart_pod"
                reason = "Critical memory error in logs"
                confidence = 0.95
            elif cpu > 90.0:
                action = "scale_deployment"
                reason = "CPU utilization exceeded 90%"
                confidence = 0.9
            elif is_anomaly and memory > 200 * 1024 * 1024:
                action = "restart_pod"
                reason = "High anomaly score coupled with high memory usage (potential leak)"
                confidence = 0.85
            else:
                action = "alert_only"
                reason = "Anomaly detected but no specific remediation rule matched"
                confidence = 0.7
                priority = "medium"

        # ML-based layer (consulting feedback loop if available)
        if self.feedback_loop and action != "none":
            # For this simple prototype, if we have a model, we consult it
            ml_action = self.feedback_loop.suggest_action(metrics, log_class)
            if ml_action and ml_action != "unknown":
                logger.info(f"ML layer suggested action: {ml_action} instead of {action}")
                # We could override rule based here, but for now we just log it or blend it
                # For safety, let's use rule-based unless ML confidence is very high
                pass

        return {
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "priority": priority
        }

if __name__ == "__main__":
    engine = DecisionEngine()
    decision = engine.decide(
        metrics_anomaly={"is_anomaly": True},
        log_analysis={"classification": "critical", "message": "Out of memory"},
        metrics={"cpu": 95.0, "memory": 250000000}
    )
    print(decision)
