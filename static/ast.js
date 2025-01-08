// JS for AST Control Panel

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

// Event listener for the weather refresh button
document.getElementById("weather-refresh").addEventListener("click", () => {
    fetchWeather();
});

// Initial weather fetch when the page loads
window.addEventListener("load", () => {
    fetchWeather(); // Fetch weather immediately on page load
});

//////////////////////////////

// Solar Calculations JS

// Update solar data on the webpage
function updateSolar(data) {
    document.getElementById("solar_alt").textContent = data.altitude || "--";
    document.getElementById("solar_az").textContent = data.azimuth || "--";
    document.getElementById("sunrise").textContent = data.sunrise || "--";
    document.getElementById("sunset").textContent = data.sunset || "--";
    document.getElementById("solar_noon").textContent = data.solar_noon || "--";
}

// Fetch initial solar data on load
function fetchSolarData() {
    fetch('/refresh_solar')
        .then(response => response.json())
        .then(data => updateSolar(data))
        .catch(error => console.error("Error fetching solar data:", error));
}

// Listen for real-time updates via Socket.IO
const socket = io();
socket.on("solar_update", updateSolar);

// Fetch data on page load
window.addEventListener("load", fetchSolarData);


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

// Example event listeners for other features
document.getElementById("slew-north").addEventListener("click", () => slewMount("north"));
document.getElementById("slew-east").addEventListener("click", () => slewMount("east"));
document.getElementById("slew-west").addEventListener("click", () => slewMount("west"));
document.getElementById("slew-south").addEventListener("click", () => slewMount("south"));
document.getElementById("stop-mount").addEventListener("click", () => slewMount("stop"));

document.getElementById("open-dome").addEventListener("click", () => controlDome("open"));
document.getElementById("close-dome").addEventListener("click", () => controlDome("close"));

document.getElementById("etalon1-inward").addEventListener("click", () => controlEtalon(1, "inward"));
document.getElementById("etalon1-outward").addEventListener("click", () => controlEtalon(1, "outward"));
document.getElementById("etalon2-inward").addEventListener("click", () => controlEtalon(2, "inward"));
document.getElementById("etalon2-outward").addEventListener("click", () => controlEtalon(2, "outward"));

// Placeholder for additional features
// TODO: Add event listeners and functions for nSTEP, cameras, and file status
