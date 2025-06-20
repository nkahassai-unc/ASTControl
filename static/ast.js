// === SOCKET SETUP ===
const socket = io();

// === SECTION: UI ELEMENTS ===
socket.on("connect", () => {
  console.log("[SocketIO] Connected. Requesting current data...");
  socket.emit("get_weather");
  socket.emit("check_indigo_status");
  socket.emit("get_mount_coordinates"); 
});

// === SECTION: INDIGO SERVER CONTROL ===

const startBtn     = document.getElementById("start-server");
const stopBtn      = document.getElementById("kill-server");
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
    ipText.textContent = "192.168.1.160 :7624";  // or dynamically from config
  } else {
    statusText.textContent = "● Offline";
    statusText.classList.remove("text-green-700");
    statusText.classList.add("text-red-700");
    ipText.textContent = "-";
  }
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
  const speed = document.getElementById("nstepSpeed").value;
  socket.emit("nstep_move", {
    direction,
    speed: parseInt(speed),
  });
}

// Handle slider update (reflects "set" position & speed)
const nstepSpeedSlider = document.getElementById("nstepSpeed");
const nstepSpeedValue = document.getElementById("nstepSpeedValue");

nstepSpeedSlider.addEventListener("input", () => {
  const val = nstepSpeedSlider.value;
  nstepSpeedValue.textContent = `Set: ${val}%`;
});

// Receive focuser feedback from backend (INDIGO)
socket.on("nstep_position", (data) => {
  if ("set" in data) {
    document.getElementById("nstepSetPosition").textContent = data.set;
  }
  if ("current" in data) {
    document.getElementById("nstepCurrentPosition").textContent = data.current;
  }
});

// === SECTION: FILE HANDLER ===
