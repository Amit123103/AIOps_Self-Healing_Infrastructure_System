# AI-Based Self-Healing Infrastructure System (AIOps)

## Overview
A production-ready AIOps system demonstrating a closed-loop architecture: **Observe → Detect → Decide → Act → Learn**. 

It monitors a sample microservice using Prometheus and ELK, detects anomalies using Isolation Forest & Autoencoders, classifies logs using NLP, makes remediation decisions, executes Kubernetes actions (scaling, restarting), and learns from the outcomes.

## Architecture Diagram
```text
+-------------------+      +-------------------+      +-------------------+
|  Microservice     | ---> | Prometheus        | ---> | AIOps Engine      |
|  (FastAPI)        |      | (Metrics)         |      | (Observe/Detect)  |
+-------------------+      +-------------------+      +---------+---------+
         |                                                      |
         v                                                      v
+-------------------+      +-------------------+      +---------+---------+
|  Filebeat/StdOut  | ---> | Logstash/Elastic  | ---> | Decision Engine   |
+-------------------+      +-------------------+      +---------+---------+
                                                                |
+-------------------+                                           v
| Feedback Loop     | <-------------------------------| K8s Actions (Act) |
| (SQLite + ML)     |                                 +-------------------+
+-------------------+
```

## Prerequisites
- Docker & Docker Compose
- Kubernetes Cluster (Minikube/Kind for local testing)
- Python 3.10+
- `kubectl` configured

## 🚀 How to Run and Deploy

### Option 1: Local Docker Compose (Recommended for Testing)
This will spin up the entire stack (Microservice, Prometheus, Grafana, ELK, AIOps Engine).

1. **Navigate to the project directory:**
   ```bash
   cd /path/to/project
   ```

2. **Build and start the containers in the background:**
   ```bash
   docker-compose up --build -d
   ```

3. **Verify the services are running:**
   - **Microservice API**: http://localhost:8000/docs
   - **AIOps API**: http://localhost:8001/docs
   - **Grafana**: http://localhost:3000 (Login: `admin` / `admin`)
   - **Kibana**: http://localhost:5601

### Option 2: Kubernetes Deployment
To deploy this system into a Kubernetes cluster (like Minikube, Kind, or a managed cloud K8s):

1. **Ensure you have a cluster running and `kubectl` configured.**

2. **Build the Docker images locally (if using Minikube):**
   ```bash
   minikube image build -t microservice:latest ./microservice
   minikube image build -t aiops_engine:latest ./aiops_engine
   ```

3. **Apply the Kubernetes manifests in order:**
   ```bash
   # Create the aiops namespace
   kubectl apply -f k8s/namespace.yaml
   
   # Deploy the microservice, service, and HPA
   kubectl apply -f k8s/microservice.yaml
   
   # Deploy the monitoring components (Requires Prometheus Operator)
   kubectl apply -f k8s/monitoring.yaml
   ```

4. **Verify the deployment:**
   ```bash
   kubectl get all -n aiops
   ```
   *Note: Ensure your cluster has a Prometheus Operator installed if you are using the `ServiceMonitor` kind.*

### 🛠️ How to Test the Self-Healing Flow
Once deployed (either Docker or K8s), you can simulate an incident to see the AIOps engine in action:

1. Trigger a failure mode in the microservice by sending a POST request to `http://localhost:8000/stress`:
   ```json
   {
     "mode": "cpu_spike",
     "active": true
   }
   ```
2. Open Grafana (`http://localhost:3000`) and watch the **Anomaly Score** rise.
3. Check the AIOps engine logs to see it detect the anomaly, consult the Decision Engine, and trigger a K8s recovery action!

## 🔄 CI/CD Pipeline (GitHub Actions)
This repository is configured with a perfect, production-ready CI/CD pipeline located in `.github/workflows/ci-cd.yml`.

Whenever code is pushed to the `main` branch, GitHub Actions will automatically:
1. **Lint & Test**: Run `flake8` to ensure Python code quality and execute a dry-run test of the Machine Learning training script.
2. **Validate K8s**: Use `kubeval` to ensure all Kubernetes manifests in `k8s/` are structurally flawless.
3. **Build & Push**: Concurrently build the Docker images for the `microservice` and `aiops_engine` and push them directly to **GitHub Container Registry (GHCR)**.
4. **Package Deployment**: Zip the deployment files (Compose, K8s, Grafana dashboards) into a downloadable Artifact on the GitHub Release page!

*Note: No extra secret configuration is required! The pipeline securely uses the automatic `GITHUB_TOKEN` to push packages to your repository's registry.*

## API Documentation

### Target Microservice (`:8000`)
| Endpoint | Method | Description |
|---|---|---|
| `/metrics` | GET | Prometheus metrics |
| `/health` | GET | Liveness probe |
| `/stress` | POST | Toggle failure modes (`cpu_spike`, `memory_leak`, `error_mode`) |

### AIOps Backend (`:8001`)
| Endpoint | Method | Description |
|---|---|---|
| `/api/metrics/ingest` | POST | Manually ingest metrics for anomaly scoring |
| `/api/actions/trigger` | POST | Manually trigger a K8s action |
| `/api/actions/history` | GET | View historical actions taken and their success |

## ML Models Note
The AI Engine uses the following models:
1. **Anomaly Detector**: `IsolationForest` (Scikit-learn) + `Autoencoder` (TensorFlow/Keras).
2. **Log Analyzer**: `TfidfVectorizer` + `LogisticRegression` (Scikit-learn).
3. **Action Selector (Feedback Loop)**: `RandomForestClassifier` (Scikit-learn).

Models are saved in the `models/` directory and are automatically generated on the first run of the engine if `sample_metrics.csv` and `sample_logs.csv` are present.

## Troubleshooting
- **Metrics not appearing in Grafana**: Check the Prometheus targets at `http://localhost:9090/targets`. Ensure the `microservice` job is UP.
- **K8s Actions failing**: Ensure the AIOps engine has a valid `kubeconfig` mounted, or the appropriate RBAC roles if running in-cluster. (Currently runs in `dry-run` mode by default for safety).
- **Out of Memory on ELK**: Elasticsearch is memory intensive. Ensure Docker has at least 4GB of RAM allocated.
