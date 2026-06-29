// Water & Moisture Control Module
// - Simulates soil moisture readings
// - Provides automatic irrigation logic
// - Manual override controls

const cropTargets = {
  wheat: { min: 60, max: 70 },
  corn: { min: 55, max: 65 },
  tomato: { min: 70, max: 80 },
  sunflower: { min: 50, max: 60 },
  cotton: { min: 55, max: 65 }
};

// --- Sensor reading functions ---
export async function readSoilMoisture() {
  // Simulated sensor reading
  return simulateMoistureRead();
}

export async function activateWaterPump() {
  // Simulated pump activation
  console.debug('Pump activated (simulated)');
}

export async function deactivateWaterPump() {
  // Simulated pump deactivation
  console.debug('Pump deactivated (simulated)');
}

// --- Simulation ---
let simulatedValue = 48 + Math.round(Math.random() * 14); // start mid-range
let driftDirection = 1; // 1 up, -1 down

function simulateMoistureRead() {
  // Add some noise and directional drift
  const noise = Math.round((Math.random() - 0.5) * 4);
  simulatedValue += driftDirection * (1 + Math.round(Math.random() * 2)) + noise;
  // Clamp
  if (simulatedValue > 85) driftDirection = -1;
  if (simulatedValue < 35) driftDirection = 1;
  simulatedValue = Math.max(20, Math.min(90, simulatedValue));
  return simulatedValue;
}

// --- UI Elements ---
const els = {
  cropSelect: document.getElementById('cropSelect'),
  currentMoisture: document.getElementById('currentMoisture'),
  targetRange: document.getElementById('targetRange'),
  statusBadge: document.getElementById('statusBadge'),
  pumpIndicator: document.getElementById('pumpIndicator'),
  pumpLabel: document.getElementById('pumpLabel'),
  btnStart: document.getElementById('btnStart'),
  btnStop: document.getElementById('btnStop'),
  chartCanvas: document.getElementById('moistureChart')
};

// --- State ---
const state = {
  autoEnabled: true,
  manualOverride: false,
  manualOverrideTimeoutId: null,
  pumpOn: false,
  lastReading: 0,
  history: [] // { t: timestamp, v: value }
};

// --- Chart Setup ---
const chart = new Chart(els.chartCanvas.getContext('2d'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Moisture %',
      data: [],
      fill: false,
      borderColor: '#22c55e',
      pointBackgroundColor: '#22c55e',
      tension: 0.25
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: { color: '#94a3b8' },
        grid: { color: 'rgba(255,255,255,0.06)' }
      },
      x: {
        ticks: { color: '#94a3b8' },
        grid: { color: 'rgba(255,255,255,0.06)' }
      }
    },
    plugins: {
      legend: { labels: { color: '#cbd5e1' } }
    }
  }
});

function updateChart(value) {
  const now = new Date();
  const label = now.toLocaleTimeString([], { minute: '2-digit', second: '2-digit' });
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  // Keep roughly last 2 minutes assuming 2s sampling => 60 points
  if (chart.data.labels.length > 60) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

// --- Helpers ---
function getTargetRange() {
  const key = els.cropSelect.value || 'wheat';
  return cropTargets[key] || cropTargets['wheat'];
}

function setStatusOk() {
  els.statusBadge.classList.remove('warning');
  els.statusBadge.textContent = '✅ Optimal Moisture';
}

function setStatusDry() {
  els.statusBadge.classList.add('warning');
  els.statusBadge.textContent = '⚠️ Too Dry — Activating Irrigation';
}

function renderTargets() {
  const { min, max } = getTargetRange();
  els.targetRange.textContent = `${min}% – ${max}%`;
}

function renderReading(v) {
  els.currentMoisture.textContent = `${v}%`;
}

function renderPump(on) {
  els.pumpIndicator.classList.toggle('on', on);
  els.pumpLabel.textContent = on ? 'Pump ON' : 'Pump OFF';
}

function blinkPumpIndicator() {
  // Visual soft pulse handled by CSS shadow; keep class on while ON
  // No extra blink logic needed, but this function documents intent.
}

// --- Control Logic ---
async function turnPumpOn(reason = 'auto') {
  if (state.pumpOn) return;
  state.pumpOn = true;
  renderPump(true);
  blinkPumpIndicator();
  await activateWaterPump();
  console.log(`Pump ON (${reason})`);
}

async function turnPumpOff(reason = 'auto') {
  if (!state.pumpOn) return;
  state.pumpOn = false;
  renderPump(false);
  await deactivateWaterPump();
  console.log(`Pump OFF (${reason})`);
}

function enableManualOverride() {
  state.manualOverride = true;
  if (state.manualOverrideTimeoutId) clearTimeout(state.manualOverrideTimeoutId);
  // Manual override lasts 30 seconds by default
  state.manualOverrideTimeoutId = setTimeout(() => {
    state.manualOverride = false;
    console.log('Manual override expired; returning to automatic control');
  }, 30000);
}

async function controlLoopTick() {
  const value = await readSoilMoisture();
  state.lastReading = value;

  // Update UI
  renderReading(value);
  updateChart(value);

  const { min, max } = getTargetRange();
  const within = value >= min && value <= max;
  if (within) setStatusOk(); else setStatusDry();

  if (!state.manualOverride && state.autoEnabled) {
    if (!within && value < min) {
      await turnPumpOn('auto');
    } else if (value >= min) {
      await turnPumpOff('auto');
    }
  }
}

// --- Event Bindings ---
els.btnStart.addEventListener('click', async () => {
  enableManualOverride();
  await turnPumpOn('manual');
});

els.btnStop.addEventListener('click', async () => {
  enableManualOverride();
  await turnPumpOff('manual');
});

els.cropSelect.addEventListener('change', () => {
  renderTargets();
});

// Initial render
renderTargets();
renderPump(false);

// Start control loop (2s sampling)
controlLoopTick();
setInterval(controlLoopTick, 2000);


