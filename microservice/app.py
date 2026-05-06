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
