# === FILE: microservice/app.py ===
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import time
import random
import logging
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("microservice")

app = FastAPI(title="Sample Microservice")

# Prometheus Metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total number of requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['method', 'endpoint'])
CPU_USAGE_GAUGE = Gauge('app_cpu_usage_percent', 'Simulated CPU usage percentage')
MEMORY_USAGE_GAUGE = Gauge('app_memory_usage_bytes', 'Simulated Memory usage in bytes')

# Mount prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# State for intentional failure modes
state = {
    "cpu_spike": False,
    "memory_leak": False,
    "high_latency": False,
    "error_mode": False,
    "memory_allocated": 100 * 1024 * 1024 # Start with 100MB
}

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    
    # Simulate high latency
    if state["high_latency"]:
        time.sleep(random.uniform(2.0, 5.0))
        
    response = await call_next(request)
    
    # Track latency
    process_time = time.time() - start_time
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
    
    # Track requests
    status_code = response.status_code
    if state["error_mode"] and request.url.path != "/metrics":
        status_code = 500
        
    REQUEST_COUNT.labels(request.method, request.url.path, status_code).inc()
    
    return response

@app.on_event("startup")
async def startup_event():
    # Set initial dummy metrics
    CPU_USAGE_GAUGE.set(10.0)
    MEMORY_USAGE_GAUGE.set(state["memory_allocated"])
    logger.info("Application started. Metrics initialized.")

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AIOps | Self-Healing Infrastructure</title>
        <meta name="description" content="Production-ready AIOps Self-Healing Infrastructure System Dashboard. Monitoring, Anomaly Detection, and Automated Remediation.">
        <style>
            :root {
                --primary: #00f2fe;
                --secondary: #4facfe;
                --bg: #0a0e17;
                --card-bg: rgba(255, 255, 255, 0.05);
                --success: #00ff88;
                --danger: #ff4b2b;
            }
            body {
                margin: 0;
                font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg);
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                overflow-x: hidden;
            }
            .background-glow {
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: radial-gradient(circle at 50% 50%, #1a2333 0%, #0a0e17 100%);
                z-index: -1;
            }
            header {
                padding: 40px 20px;
                text-align: center;
                width: 100%;
                max-width: 1200px;
            }
            h1 {
                font-size: 3rem;
                margin: 0;
                background: linear-gradient(to right, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -1px;
            }
            .status-badge {
                display: inline-block;
                padding: 8px 20px;
                border-radius: 20px;
                background: rgba(0, 255, 136, 0.1);
                color: var(--success);
                border: 1px solid rgba(0, 255, 136, 0.2);
                font-weight: 600;
                margin-top: 20px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(0, 255, 136, 0); }
                100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
            }
            .container {
                width: 90%;
                max-width: 1000px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
                padding: 20px;
            }
            .card {
                background: var(--card-bg);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 24px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.3s ease, border 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                border: 1px solid rgba(0, 242, 254, 0.3);
            }
            .card h2 {
                margin: 0 0 15px 0;
                font-size: 1.2rem;
                color: rgba(255, 255, 255, 0.7);
            }
            .btn {
                display: block;
                width: 100%;
                padding: 12px;
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                color: #0a0e17;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 700;
                margin-top: 20px;
                transition: opacity 0.3s;
            }
            .btn:hover { opacity: 0.9; }
            .endpoint {
                font-family: monospace;
                background: rgba(0, 0, 0, 0.3);
                padding: 4px 8px;
                border-radius: 4px;
                color: var(--primary);
            }
            footer {
                margin-top: auto;
                padding: 40px;
                color: rgba(255, 255, 255, 0.4);
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="background-glow"></div>
        <header>
            <h1>AIOps Self-Healing Engine</h1>
            <div class="status-badge">● SYSTEM OPERATIONAL</div>
        </header>
        
        <div class="container">
            <div class="card">
                <h2>Infrastructure Health</h2>
                <p>Monitoring real-time telemetry from <strong>GHCR Containers</strong>.</p>
                <p>Status: <span style="color: var(--success)">Healthy</span></p>
                <div style="height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 10px;">
                    <div style="width: 85%; height: 100%; background: var(--success); border-radius: 2px;"></div>
                </div>
            </div>
            
            <div class="card">
                <h2>API Documentation</h2>
                <p>Explore the full API spec, including <strong>Stress Testing</strong> endpoints.</p>
                <a href="/docs" class="btn">View Swagger UI</a>
            </div>
            
            <div class="card">
                <h2>Real-time Metrics</h2>
                <p>Prometheus exporter is active at <span class="endpoint">/metrics</span>.</p>
                <a href="/metrics" class="btn" style="background: rgba(255,255,255,0.1); color: white;">Open Metrics</a>
            </div>
        </div>
        
        <footer>
            Built with FastAPI, TensorFlow, and ❤️ by AIOps Engineers
        </footer>
    </body>
    </html>
    """


@app.get("/health")
def health_check():
    if state["error_mode"]:
        logger.error("Health check failed due to error mode.")
        raise HTTPException(status_code=500, detail="Internal Server Error due to error_mode")
    return {"status": "ok"}

@app.get("/api/data")
def get_data():
    if state["error_mode"]:
        logger.error("Data fetch failed due to error mode.")
        raise HTTPException(status_code=500, detail="Simulated 500 Error")
        
    # Simulate CPU usage
    if state["cpu_spike"]:
        CPU_USAGE_GAUGE.set(random.uniform(90.0, 100.0))
        # Busy loop to actually consume some CPU briefly
        _ = [i * i for i in range(1000000)]
    else:
        CPU_USAGE_GAUGE.set(random.uniform(10.0, 30.0))

    # Simulate Memory Leak
    if state["memory_leak"]:
        state["memory_allocated"] += 50 * 1024 * 1024 # add 50MB
        MEMORY_USAGE_GAUGE.set(state["memory_allocated"])
        
    logger.info("Data fetched successfully")
    return {"data": "sample_data", "timestamp": time.time()}

class StressRequest(BaseModel):
    mode: str
    active: bool

@app.post("/stress")
def toggle_stress(req: StressRequest):
    """
    Toggle failure modes:
    - cpu_spike
    - memory_leak
    - high_latency
    - error_mode
    """
    if req.mode in state:
        state[req.mode] = req.active
        logger.warning(f"Toggled failure mode: {req.mode} = {req.active}")
        return {"message": f"Failure mode {req.mode} set to {req.active}"}
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")
