const MICROSERVICE_URL = "https://aiops-self-healing-infrastructure-system.onrender.com";
const ENGINE_URL = "https://aiops-self-healing-infrastructure-system-3n5p.onrender.com";

const terminal = document.getElementById('log-terminal');
const statusIndicator = document.getElementById('connection-status');
const apiLink = document.getElementById('api-link');

apiLink.href = MICROSERVICE_URL;
apiLink.innerText = `Connected: API & Engine Live`;

let lastHistoryTime = "";

let activeModes = {
    cpu_spike: false,
    memory_leak: false,
    high_latency: false,
    error_mode: false
};

function log(msg, type = '') {
    const line = document.createElement('div');
    line.className = `line ${type}`;
    line.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    terminal.prepend(line);
    if (terminal.children.length > 50) terminal.lastChild.remove();
}

async function fetchMetrics() {
    try {
        const response = await fetch(`${MICROSERVICE_URL}/metrics`);
        const text = await response.text();
        
        const cpuMatch = text.match(/app_cpu_usage_percent ([\d\.]+)/);
        const memMatch = text.match(/app_memory_usage_bytes ([\d\.]+)/);
        const latMatch = text.match(/app_request_latency_seconds_sum ([\d\.]+)/);
        
        const cpu = cpuMatch ? parseFloat(cpuMatch[1]).toFixed(1) : 0;
        const mem = memMatch ? (parseFloat(memMatch[1]) / (1024 * 1024)).toFixed(0) : 0;
        const lat = latMatch ? (parseFloat(latMatch[1]) * 1000).toFixed(0) : 0;

        updateUI(cpu, mem, lat);
        statusIndicator.classList.add('online');
        statusIndicator.querySelector('.text').innerText = 'SYSTEM ONLINE';
        
        // Also fetch AI history
        fetchHistory();
    } catch (e) {
        statusIndicator.classList.remove('online');
        statusIndicator.querySelector('.text').innerText = 'CONNECTION LOST';
    }
}

async function fetchHistory() {
    try {
        const response = await fetch(`${ENGINE_URL}/api/actions/history`);
        const data = await response.json();
        if (data.history && data.history.length > 0) {
            const latest = data.history[0];
            if (latest.time !== lastHistoryTime) {
                lastHistoryTime = latest.time;
                log(`AI DECISION: ${latest.action} | SUCCESS: ${latest.success}`, latest.success ? 'success' : 'alert');
            }
        }
    } catch (e) {
        // AI Engine might be offline, ignore silently
    }
}

function updateUI(cpu, mem, lat) {
    const cpuCard = document.getElementById('cpu-card');
    const latCard = document.getElementById('latency-card');

    document.getElementById('cpu-val').innerText = cpu;
    document.getElementById('cpu-bar').style.width = `${Math.min(cpu, 100)}%`;
    cpuCard.classList.toggle('anomaly', cpu > 80);
    
    document.getElementById('mem-val').innerText = mem;
    document.getElementById('mem-bar').style.width = `${Math.min((mem/512)*100, 100)}%`;
    
    document.getElementById('latency-val').innerText = lat;
    document.getElementById('latency-bar').style.width = `${Math.min((lat/2000)*100, 100)}%`;
    latCard.classList.toggle('anomaly', lat > 1000);

    if (cpu > 80) log("CRITICAL: CPU Spike detected by monitor!", "alert");
    if (lat > 1000) log("CRITICAL: High Latency detected by monitor!", "alert");
}

async function toggleStress(mode) {
    activeModes[mode] = !activeModes[mode];
    const btn = document.getElementById(`btn-${mode.split('_')[0]}`);
    
    try {
        log(`Injecting Fault: ${mode}...`, activeModes[mode] ? 'alert' : 'success');
        await fetch(`${MICROSERVICE_URL}/stress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode, active: activeModes[mode] })
        });
        btn.classList.toggle('active');
    } catch (e) {
        log("Failed to inject fault. Check API connection.", "alert");
    }
}

// Start polling
setInterval(fetchMetrics, 2000);
fetchMetrics();
log("Connected to AIOps Control Plane.");
