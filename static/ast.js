// JS for AST Control Panel

function appendLog(message) {
    const logDiv = document.querySelector(".log-output");
    const newLog = document.createElement("p");
    newLog.textContent = message;
    logDiv.appendChild(newLog);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function updateIPStatus(ip) {
    document.getElementById("server-ip").textContent = ip || "Disconnected";
}

document.getElementById("start-server").addEventListener("click", () => {
    fetch("/start_server", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            appendLog(data.message);
            updateIPStatus(data.ip_status);
        });
});

document.getElementById("kill-server").addEventListener("click", () => {
    fetch("/kill_server", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            appendLog(data.message);
            updateIPStatus(data.ip_status);
        });
});

function updateWeather(data) {
    document.getElementById("condition").textContent = data.sky_conditions || "Unknown";
    document.getElementById("temperature").textContent = data.temperature || "--";
    document.getElementById("wind").textContent = data.wind_speed || "--";
    document.getElementById("last_checked").textContent = data.last_checked || "N/A";
}

function fetchWeather() {
    fetch("/refresh_weather")
        .then(res => res.json())
        .then(data => updateWeather(data));
}

function updateSolar(data) {
    document.getElementById("solar_alt").textContent = data.solar_alt;
    document.getElementById("solar_az").textContent = data.solar_az;
    document.getElementById("sunrise").textContent = data.sunrise;
    document.getElementById("sunset").textContent = data.sunset;
    document.getElementById("solar_noon").textContent = data.solar_noon;
    document.getElementById("sun_time").textContent = data.sun_time;
}

function fetchSolarData() {
    fetch("/refresh_solar")
        .then(res => res.json())
        .then(data => updateSolar(data));
}

// SOCKETS
const socket = io();
socket.on("server_log", appendLog);
socket.on("weather_update", updateWeather);
socket.on("solar_update", updateSolar);

// ==== SERVO CONTROL ==== 
function sendServoCommand(command) {
    fetch("/servo_control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command })
    }).then(res => res.json())
      .then(data => console.log("Command sent:", data))
      .catch(err => console.error("Servo command error:", err));
}

// Dome Control
document.getElementById("open-dome").addEventListener("click", () => {
    sendServoCommand("DOME_OPEN");
    document.getElementById("dome-position").textContent = "Open";
});

document.getElementById("close-dome").addEventListener("click", () => {
    sendServoCommand("DOME_CLOSE");
    document.getElementById("dome-position").textContent = "Closed";
});

// Link input ↔ slider for Etalon 1
const etalon1Input = document.getElementById("etalon1-input");
const etalon1Slider = document.getElementById("etalon1-slider");

etalon1Slider.addEventListener("input", () => {
  etalon1Input.value = etalon1Slider.value;
});
etalon1Input.addEventListener("input", () => {
  etalon1Slider.value = etalon1Input.value;
});
["mouseup", "touchend"].forEach(evt => {
  etalon1Slider.addEventListener(evt, () => {
    sendServoCommand(`ETALON1:${etalon1Slider.value}`);
  });
});

// Link input ↔ slider for Etalon 2
const etalon2Input = document.getElementById("etalon2-input");
const etalon2Slider = document.getElementById("etalon2-slider");

etalon2Slider.addEventListener("input", () => {
  etalon2Input.value = etalon2Slider.value;
});
etalon2Input.addEventListener("input", () => {
  etalon2Slider.value = etalon2Input.value;
});
["mouseup", "touchend"].forEach(evt => {
  etalon2Slider.addEventListener(evt, () => {
    sendServoCommand(`ETALON2:${etalon2Slider.value}`);
  });
});

// nstep
const nstepSlider = document.getElementById('nstep-rate');
const nstepLabel = document.getElementById('nstep-rate-value');

nstepSlider.addEventListener('input', () => {
  nstepLabel.textContent = nstepSlider.value;
});



// Initialize data on page load
window.addEventListener("load", () => {
    fetchWeather();
    fetchSolarData();
});
