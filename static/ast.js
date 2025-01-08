// JS for AST Control Panel
//////////////////////////////

// INDIGO Server Control JS

// Append log messages to the log output
function appendLog(message) {
    const logDiv = document.querySelector(".log-output");
    const newLog = document.createElement("p");
    newLog.textContent = message;
    logDiv.appendChild(newLog);
    logDiv.scrollTop = logDiv.scrollHeight; // Auto-scroll to the latest log
}

// Event listener for starting the INDIGO server
document.getElementById("start-server").addEventListener("click", () => {
    fetch("/start_server", { method: "POST" })
        .then(response => response.json())
        .then(data => appendLog(data.message))
        .catch(error => {
            console.error("Error starting server:", error);
            appendLog("Error starting server.");
        });
});

// Event listener for killing the INDIGO server
document.getElementById("kill-server").addEventListener("click", () => {
    fetch("/kill_server", { method: "POST" })
        .then(response => response.json())
        .then(data => appendLog(data.message))
        .catch(error => {
            console.error("Error killing server:", error);
            appendLog("Error killing server.");
        });
});

//////////////////////////////

// Weather Monitor JS

// Function to update the weather data on the webpage
function updateWeather(data) {
    document.getElementById("condition").textContent = data.sky_conditions || "Unknown";
    document.getElementById("temperature").textContent = data.temperature || "--";
    document.getElementById("wind").textContent = data.wind_speed || "--";
    document.getElementById("last_checked").textContent = data.last_checked || "N/A";
}

// Fetch weather data from the backend
function fetchWeather() {
    fetch('/refresh_weather')
        .then(response => response.json())
        .then(data => {
            console.log("Weather data:", data); // Optional logging for debugging
            updateWeather(data); // Update the webpage with new data
        })
        .catch(error => console.error("Error fetching weather data:", error));
}

//////////////////////////////

// Solar Calculations JS

// Update solar data on the webpage
function updateSolar(data) {
    document.getElementById("solar_alt").textContent = data.solar_alt || "--";
    document.getElementById("solar_az").textContent = data.solar_az || "--";
    document.getElementById("sunrise").textContent = data.sunrise || "--";
    document.getElementById("sunset").textContent = data.sunset || "--";
    document.getElementById("solar_noon").textContent = data.solar_noon || "--";
    document.getElementById("sun_time").textContent = data.sun_time || "--";
}

// Fetch solar data from the backend
function fetchSolarData() {
    fetch('/refresh_solar')
        .then(response => response.json())
        .then(data => {
            console.log("Solar data:", data); // Optional logging for debugging
            updateSolar(data); // Update the webpage with new data
        })
        .catch(error => console.error("Error fetching solar data:", error));
}

//////////////////////////////

// Real-Time Updates via Socket.IO
const socket = io();

// WebSocket for real-time log streaming
socket.on("server_log", (message) => {
    appendLog(message);
});

// Listen for real-time weather updates
socket.on("weather_update", (data) => {
    console.log("Real-time weather update:", data);
    updateWeather(data);
});

// Listen for real-time solar updates
socket.on("solar_update", (data) => {
    console.log("Real-time solar update:", data);
    updateSolar(data);
});


//////////////////////////////

// Placeholder functions for other features
function slewMount(direction) {
    console.log(`Slewing mount ${direction}`);
    // TODO: Add implementation to call backend and update mount movement
}

function controlDome(action) {
    console.log(`Dome action: ${action}`);
    // TODO: Add implementation to call backend for dome control
}

function controlEtalon(etalonId, action) {
    console.log(`Etalon ${etalonId} action: ${action}`);
    // TODO: Add implementation to call backend for etalon control
}

// Event listeners for mount slewing
document.getElementById("slew-north").addEventListener("click", () => slewMount("north"));
document.getElementById("slew-east").addEventListener("click", () => slewMount("east"));
document.getElementById("slew-west").addEventListener("click", () => slewMount("west"));
document.getElementById("slew-south").addEventListener("click", () => slewMount("south"));
document.getElementById("stop-mount").addEventListener("click", () => slewMount("stop"));

// Event listeners for dome control
document.getElementById("open-dome").addEventListener("click", () => controlDome("open"));
document.getElementById("close-dome").addEventListener("click", () => controlDome("close"));

// Event listeners for etalon control
document.getElementById("etalon1-inward").addEventListener("click", () => controlEtalon(1, "inward"));
document.getElementById("etalon1-outward").addEventListener("click", () => controlEtalon(1, "outward"));
document.getElementById("etalon2-inward").addEventListener("click", () => controlEtalon(2, "inward"));
document.getElementById("etalon2-outward").addEventListener("click", () => controlEtalon(2, "outward"));

//////////////////////////////

// Initial Data Fetch on Page Load
window.addEventListener("load", () => {
    fetchWeather(); // Fetch initial weather data
    fetchSolarData(); // Fetch initial solar data
});