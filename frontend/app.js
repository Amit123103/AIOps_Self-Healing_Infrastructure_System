const API_BASE = "https://aiops-self-healing-infrastructure-system.onrender.com";
const terminal = document.getElementById('log-terminal');
const statusIndicator = document.getElementById('connection-status');
const apiLink = document.getElementById('api-link');

apiLink.href = API_BASE;
apiLink.innerText = API_BASE;

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
        const response = await fetch(`${API_BASE}/metrics`);
        const text = await response.text();
        
        // Parse Prometheus metrics
        const cpuMatch = text.match(/app_cpu_usage_percent ([\d\.]+)/);
        const memMatch = text.match(/app_memory_usage_bytes ([\d\.]+)/);
        const latMatch = text.match(/app_request_latency_seconds_sum ([\d\.]+)/);
        
        const cpu = cpuMatch ? parseFloat(cpuMatch[1]).toFixed(1) : 0;
        const mem = memMatch ? (parseFloat(memMatch[1]) / (1024 * 1024)).toFixed(0) : 0;
        const lat = latMatch ? (parseFloat(latMatch[1]) * 1000).toFixed(0) : 0;

        updateUI(cpu, mem, lat);
        statusIndicator.classList.add('online');
        statusIndicator.querySelector('.text').innerText = 'SYSTEM ONLINE';
    } catch (e) {
        statusIndicator.classList.remove('online');
        statusIndicator.querySelector('.text').innerText = 'CONNECTION LOST';
        log("Connection error to AIOps API", "alert");
    }
}

function updateUI(cpu, mem, lat) {
    document.getElementById('cpu-val').innerText = cpu;
    document.getElementById('cpu-bar').style.width = `${Math.min(cpu, 100)}%`;
    
    document.getElementById('mem-val').innerText = mem;
    document.getElementById('mem-bar').style.width = `${Math.min((mem/512)*100, 100)}%`;
    
    document.getElementById('latency-val').innerText = lat;
    document.getElementById('latency-bar').style.width = `${Math.min((lat/2000)*100, 100)}%`;

    // Visual Alerts
    if (cpu > 80 || lat > 1000) {
        log(`ANOMALY DETECTED: ${cpu > 80 ? 'CPU High' : 'Latency High'}`, "alert");
    }
}

async function toggleStress(mode) {
    activeModes[mode] = !activeModes[mode];
    const btn = document.getElementById(`btn-${mode.split('_')[0]}`);
    
    try {
        log(`Triggering chaos mode: ${mode} -> ${activeModes[mode]}`, activeModes[mode] ? 'alert' : 'success');
        const response = await fetch(`${API_BASE}/stress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode, active: activeModes[mode] })
        });
        
        if (response.ok) {
            btn.classList.toggle('active');
        }
    } catch (e) {
        log("Failed to send chaos command", "alert");
    }
}

// Start polling
setInterval(fetchMetrics, 2000);
fetchMetrics();
log("Connected to AIOps Control Plane.");
