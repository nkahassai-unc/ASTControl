// === SOCKET SETUP ===
const socket = io();

// === SECTION: UI ELEMENTS ===
socket.on("connect", () => {
  console.log("[SocketIO] Connected. Requesting current data...");
  socket.emit("get_weather");
  socket.emit("check_indigo_status");
  socket.emit("get_mount_coordinates");
  socket.emit("get_mount_status");
  socket.emit("get_fc_status");
  updateArduinoStatus();
});

// === SECTION: INDIGO SERVER CONTROL ===

const startBtn     = document.getElementById("start-server");
const stopBtn      = document.getElementById("kill-server");
const serverBtn    = document.getElementById("server-manager");
const logBox       = document.getElementById("server-log");
const statusLight  = document.getElementById("indigo-status");
const ipText       = document.getElementById("server-ip");

// Emit start/stop commands
startBtn.addEventListener("click", () => {
  logBox.innerHTML += "<div>[CLIENT] Starting INDIGO server...</div>";
  socket.emit("start_indigo");
});

stopBtn.addEventListener("click", () => {
  logBox.innerHTML += "<div>[CLIENT] Stopping INDIGO server...</div>";
  socket.emit("stop_indigo");
});

// Open server manager in new tab
serverBtn.addEventListener("click", () => {
  window.open(`http://${piIp}:7624`, "_blank");
});

// Handle live INDIGO server log streaming
const MAX_LOG_LINES = 100;

socket.on("server_log", (msg) => {
  const line = document.createElement("div");
  line.textContent = msg;
  logBox.appendChild(line);

  // Limit lines
  while (logBox.children.length > MAX_LOG_LINES) {
    logBox.removeChild(logBox.firstChild);
  }

  logBox.scrollTop = logBox.scrollHeight;
});

// Poll for server status every 5 seconds
setInterval(() => {
  socket.emit("check_indigo_status");
}, 5000);

// Update status light and IP display
socket.on("indigo_status", (data) => {
  const statusText = document.getElementById("indigo-status");
  const ipText = document.getElementById("server-ip");

  if (data.running) {
    statusText.textContent = "● Online";
    statusText.classList.remove("text-red-700");
    statusText.classList.add("text-green-700");
    ipText.textContent = `${data.ip}:7624`;  // dynamically update
  } else {
    statusText.textContent = "● Offline";
    statusText.classList.remove("text-green-700");
    statusText.classList.add("text-red-700");
    ipText.textContent = "-";
  }
});

document.addEventListener("DOMContentLoaded", () => {
  socket.emit("check_indigo_status");
});


// === SECTION: WEATHER DATA ===

socket.on("update_weather", updateWeather);

function updateWeather(data) {
  document.getElementById("condition").textContent    = data.sky_conditions ?? "--";
  document.getElementById("temperature").textContent  = data.temperature !== "--" ? `${data.temperature} °C` : "--";
  document.getElementById("wind").textContent         = data.wind_speed !== "--" ? `${data.wind_speed} mph` : "--";
  document.getElementById("precip").textContent       = data.precip_chance !== "--" ? `${data.precip_chance}%` : "--";
  document.getElementById("last_checked").textContent = data.last_checked ?? "--";
}


// === SECTION: SOLAR POSITION DATA ===

socket.on("solar_update", updateSolar);
socket.emit("get_solar");

function updateSolar(data) {
  document.getElementById("solar_alt").textContent   = data.solar_alt ?? "--";
  document.getElementById("solar_az").textContent    = data.solar_az ?? "--";
  document.getElementById("sunrise").textContent     = data.sunrise ?? "--";
  document.getElementById("sunset").textContent      = data.sunset ?? "--";
  document.getElementById("solar_noon").textContent  = data.solar_noon ?? "--";
  document.getElementById("sun_time").textContent    = data.sun_time ?? "--";
}

// === Mount + Solar RA/DEC State Polling ===
setInterval(() => {
  socket.emit("get_mount_solar_state");
}, 1000); // every 1 second

// === Socket listener for mount/solar state ===
socket.on("mount_solar_state", (data) => {
  const raSolar = document.getElementById("ra-solar");
  const decSolar = document.getElementById("dec-solar");
  const raMount = document.getElementById("ra-mount");
  const decMount = document.getElementById("dec-mount");

  if (raSolar) raSolar.textContent = data.ra_solar || "--:--:--";
  if (decSolar) decSolar.textContent = data.dec_solar || "--:--:--";
  if (raMount) raMount.textContent = data.ra_mount || "--:--:--";
  if (decMount) decMount.textContent = data.dec_mount || "--:--:--";
});

// === SECTION: MOUNT CONTROL ===

const trackBtn       = document.getElementById("track-sun");
const parkBtn        = document.getElementById("park-mount");
const mountStatus    = document.getElementById("mount-status");
const slewRateSelect = document.getElementById("slew-rate");
const slewRate       = () => slewRateSelect.value;

const directions = {
  "slew-north": "north",
  "slew-south": "south",
  "slew-east":  "east",
  "slew-west":  "west"
};

// Wire DPAD buttons for slew
Object.keys(directions).forEach((btnId) => {
  document.getElementById(btnId).addEventListener("click", () => {
    socket.emit("slew_mount", {
      direction: directions[btnId],
      rate: slewRate()
    });
  });
});

// Stop button
document.getElementById("stop-mount").addEventListener("click", () => {
  socket.emit("stop_mount");
});

// Track Sun
trackBtn.addEventListener("click", () => {
  socket.emit("track_sun");
});

// Park Mount
parkBtn.addEventListener("click", () => {
  socket.emit("park_mount");
});

// Mount status and coordinates
socket.on("mount_status", (status) => {
  mountStatus.textContent = status;
});

socket.on("mount_coordinates", (coords) => {
  document.getElementById("ra-placeholder").textContent  = coords.ra ?? "--";
  document.getElementById("dec-placeholder").textContent = coords.dec ?? "--";
});


// === SECTION: FOCUSER CONTROL ===

function nstepMove(direction) {
  socket.emit("nstep_move", {
    direction: direction,
  });
}

// Receive focuser feedback from backend (INDIGO)
socket.on("nstep_position", (data) => {
  if ("set" in data) {
    document.getElementById("nstepSetPosition").textContent = data.set;
  }
  if ("current" in data) {
    document.getElementById("nstepCurrentPosition").textContent = data.current;
  }
});


// === SECTION: SCIENCE CAMERA ===

const img = document.getElementById("fc-preview");
const piIp = img?.dataset.piIp;
const indicator = document.getElementById("fc-status-indicator");
let previewPoll = null;

function startFcPreview() {
  socket.emit("start_fc_preview");

  img.classList.remove("opacity-50", "max-w-[300px]", "bg-gray-400");

  if (previewPoll) clearInterval(previewPoll);
  previewPoll = setInterval(() => {
    img.src = `http://${piIp}:8082/fc_preview.jpg?cache=${Date.now()}`;
  }, 500);

  // Move these outside the interval so they don’t reassign every time
  img.onload = () => {
    indicator.classList.replace("bg-red-500", "bg-green-500");
    img.classList.remove("opacity-50", "max-w-[300px]");
  };

  img.onerror = () => {
    indicator.classList.replace("bg-green-500", "bg-red-500");
    img.src = "/static/no_preview.png";
    img.classList.add("opacity-50", "max-w-[300px]");
  };
}

function stopFcPreview() {
  socket.emit("stop_fc_preview");

  if (previewPoll) clearInterval(previewPoll);
  previewPoll = null;

  img.src = "/static/no_preview.png";
  img.onload = null;
  img.onerror = null;

  indicator.classList.remove("bg-green-500");
  indicator.classList.add("bg-red-500");

  img.classList.add("opacity-50", "max-w-[300px]", "bg-gray-400");
}

function triggerFcCapture() {
  socket.emit("trigger_fc_capture");

  img.classList.add("ring", "ring-blue-400");

  setTimeout(() => {
    img.classList.remove("ring", "ring-blue-400");
  }, 500);
}

socket.on("fc_preview_status", (status) => {
  if (status) {
    startFcPreview();
  } else {
    stopFcPreview();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  socket.emit("get_fc_status");
});

window.startFcPreview = startFcPreview;
window.stopFcPreview = stopFcPreview;
window.triggerFcCapture = triggerFcCapture;


// === SECTION: DOME CAMERA ===

// Set dome cam stream src on page load
const domeView = document.getElementById("dome-view");
if (domeView && piIp) {
  domeView.src = `http://${piIp}:8081/0/stream`;
}


// === SECTION: ARDUINO CONTROL ===

// === Dome control ===
function setDome(state) {
  socket.emit("set_dome", { state });
  console.log("[ARDUINO] Setting dome state to:", state);
}

// === Etalon sliders ===
["1", "2"].forEach((index) => {
  const slider = document.getElementById(`etalon${index}Slider`);
  const valueLabel = document.getElementById(`etalon${index}Value`);

  if (slider && valueLabel) {
    slider.addEventListener("input", () => {
      const val = parseInt(slider.value);
      valueLabel.textContent = `${val}°`;
      socket.emit("set_etalon", {
        index: parseInt(index),
        value: val
      });
    });
  }
});

// === Unified state updater ===
socket.on("arduino_state", (state) => {
  setArduinoStatus(state.connected);
  console.log("[ARDUINO] Arduino state:", state);

  // Dome
  const domeLabel = document.getElementById("domeStatus");
  if (domeLabel) domeLabel.textContent = "Status: " + state.dome;

  // Etalons
  for (let i = 1; i <= 2; i++) {
    const val = state[`etalon${i}`];
    const slider = document.getElementById(`etalon${i}Slider`);
    const label = document.getElementById(`etalon${i}Value`);
    if (slider && label) {
      slider.value = val;
      label.textContent = `${val}°`;
    }
  }
});

// === Arduino Status Check ===
function updateArduinoStatus() {
  window._arduinoResponded = true;
  socket.emit("get_arduino_state");

  setTimeout(() => {
    if (!window._arduinoResponded) {
      setArduinoStatus(false);
    }
  }, 2000);
}

function setArduinoStatus(connected) {
  const dot = document.getElementById("arduinoStatusDot");
  const text = document.getElementById("arduinoStatusText");
  if (!dot || !text) return;

  if (connected) {
    dot.classList.remove("bg-gray-400", "animate-pulse");
    dot.classList.add("bg-green-500");
    text.textContent = "Connected";
  } else {
    dot.classList.remove("bg-green-500");
    dot.classList.add("bg-gray-400", "animate-pulse");
    text.textContent = "Disconnected";
  }
}


// === SECTION: FILE HANDLER ===
function fetchFileList() {
  const tableBody = document.getElementById("file-table-body");
  const statusSpan = document.getElementById("file-status");

  if (!tableBody || !statusSpan) return;

  fetch("/get_file_list")
    .then((response) => response.json())
    .then((files) => {
      tableBody.innerHTML = "";

      let currentStatus = "Idle";

      files.forEach((file) => {
        const row = document.createElement("tr");

        // Assign row background color based on file status
        let rowClass = "";
        if (file.status === "Copied") rowClass = "bg-green-100";
        else if (file.status === "Copying") rowClass = "bg-yellow-100";
        else if (file.status === "Failed") rowClass = "bg-red-100";

        row.className = rowClass;

        row.innerHTML = `
          <td class="px-4 py-2">${file.name}</td>
          <td class="px-4 py-2">${file.size}</td>
          <td class="px-4 py-2">${file.modified}</td>
        `;
        tableBody.appendChild(row);

        if (file.status === "Copying" || file.status === "Failed") {
          currentStatus = file.status;
        }
      });

      statusSpan.textContent = currentStatus;
    })
    .catch((err) => {
      console.error("Error fetching file list:", err);
      statusSpan.textContent = "Error";
    });
}

window.addEventListener("load", fetchFileList);
setInterval(fetchFileList, 5000);