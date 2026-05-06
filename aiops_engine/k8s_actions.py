# === FILE: aiops_engine/k8s_actions.py ===
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class K8sActions:
    def __init__(self, dry_run: bool = False):
        """
        Initializes Kubernetes client. Supports in-cluster or kubeconfig loading.
        """
        self.dry_run = dry_run
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("Loaded local kubeconfig")
            except Exception as e:
                logger.error(f"Failed to load Kubernetes config: {e}")
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()

    def restart_pod(self, namespace: str, deployment_name: str) -> bool:
        """
        Triggers a restart of the deployment by patching its annotations.
        """
        logger.info(f"[{'DRY-RUN' if self.dry_run else 'EXEC'}] Restarting deployment {deployment_name} in {namespace}")
        if self.dry_run:
            return True
            
        import datetime
        now = datetime.datetime.utcnow()
        now = str(now.isoformat("T") + "Z")
        body = {
            'spec': {
                'template':{
                    'metadata': {
                        'annotations': {
                            'kubectl.kubernetes.io/restartedAt': now
                        }
                    }
                }
            }
        }
        try:
            self.apps_v1.patch_namespaced_deployment(deployment_name, namespace, body, pretty='true')
            logger.info("Deployment restarted successfully.")
            return True
        except ApiException as e:
            logger.error(f"Exception when calling AppsV1Api->patch_namespaced_deployment: {e}")
            return False

    def scale_deployment(self, namespace: str, deployment_name: str, replicas: int) -> bool:
        """
        Scales a deployment to the specified number of replicas.
        """
        logger.info(f"[{'DRY-RUN' if self.dry_run else 'EXEC'}] Scaling deployment {deployment_name} in {namespace} to {replicas}")
        if self.dry_run:
            return True
            
        body = {"spec": {"replicas": replicas}}
        try:
            self.apps_v1.patch_namespaced_deployment_scale(deployment_name, namespace, body)
            logger.info("Deployment scaled successfully.")
            return True
        except ApiException as e:
            logger.error(f"Exception when calling AppsV1Api->patch_namespaced_deployment_scale: {e}")
            return False

    def get_pod_status(self, namespace: str, label_selector: str) -> dict:
        """
        Retrieves status of pods matching the label selector.
        """
        try:
            pods = self.core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
            status = {}
            for pod in pods.items:
                status[pod.metadata.name] = pod.status.phase
            return status
        except ApiException as e:
            logger.error(f"Exception when calling CoreV1Api->list_namespaced_pod: {e}")
            return {}

if __name__ == "__main__":
    k8s = K8sActions(dry_run=True)
    k8s.restart_pod("aiops", "microservice")
    k8s.scale_deployment("aiops", "microservice", 3)
