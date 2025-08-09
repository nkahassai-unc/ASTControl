// === SOCKET SETUP ===
const socket = io({ transports: ["websocket", "polling"] });
window.addEventListener("error", e => console.error("[JS error]", e.message, e.filename, e.lineno));
window.addEventListener("unhandledrejection", e => console.error("[Promise rejection]", e.reason));
socket.on("connect_error", err => console.error("[Socket connect_error]", err?.message || err));
socket.on("error", err => console.error("[Socket error]", err));

// === TARGET + CARD THEME (Tailwind, single card only) ===
let ACTIVE_TARGET = "sun"; // "sun" | "moon"
let LAST_PROFILE = null;   // chapel_hill | kansas_city (from astro_update)

function applyTargetTheme(target) {
  ACTIVE_TARGET = target === "moon" ? "moon" : "sun";

  const card     = document.getElementById("astro-card");
  const title    = document.getElementById("astro-forecast-title");
  const posTitle = document.getElementById("astro-position-title");

  // Titles
  if (title)    title.textContent    = (ACTIVE_TARGET === "moon") ? "Lunar & Weather Forecast" : "Solar & Weather Forecast";
  if (posTitle) posTitle.textContent = (ACTIVE_TARGET === "moon") ? "Lunar Position" : "Solar Position";

  // Swap label text inside the single block
  // (we change the static text around the <strong> values)
  const sunriseLabel = document.querySelector('#sunrise')?.parentElement;
  const noonLabel    = document.querySelector('#solar_noon')?.parentElement;
  const sunsetLabel  = document.querySelector('#sunset')?.parentElement;

  if (sunriseLabel) sunriseLabel.firstChild.textContent = (ACTIVE_TARGET === "moon") ? "Moonrise: " : "Sunrise: ";
  if (noonLabel)    noonLabel.firstChild.textContent    = (ACTIVE_TARGET === "moon") ? "— "       : "Noon: ";
  if (sunsetLabel)  sunsetLabel.firstChild.textContent  = (ACTIVE_TARGET === "moon") ? "Moonset: " : "Sunset: ";

  // Card theme
  if (card) {
    const solarOn = ["bg-white", "text-gray-900", "shadow"];
    const lunarOn = ["bg-gray-800", "text-gray-100", "shadow"];
    card.classList.remove(...solarOn, ...lunarOn);
    card.classList.add(...(ACTIVE_TARGET === "moon" ? lunarOn : solarOn));
  }

  // Canvas visibility
  const solarCanvas = document.getElementById("solar-canvas");
  const lunarCanvas = document.getElementById("lunar-canvas");
  if (solarCanvas) solarCanvas.classList.toggle("hidden", ACTIVE_TARGET === "moon");
  if (lunarCanvas) lunarCanvas.classList.toggle("hidden", ACTIVE_TARGET === "sun");

  // Redraw whichever is active
  redrawActiveCanvas();
}

// === ON CONNECT BOOTSTRAP ===
socket.on("connect", () => {
  console.log("[SocketIO] Connected. Requesting current data...");
  socket.emit("get_weather");
  socket.emit("get_solar"); // backend responds with astro_update
  socket.emit("check_indigo_status");
  socket.emit("get_mount_coordinates");
  socket.emit("get_mount_solar_state");
  socket.emit("get_fc_status");
  updateArduinoStatus();
});

// === INDIGO SERVER CONTROL ===
const startBtn  = document.getElementById("start-server");
const stopBtn   = document.getElementById("kill-server");
const serverBtn = document.getElementById("server-manager");
const logBox    = document.getElementById("server-log");
const piIpAttr  = document.querySelector("[data-pi-ip]");
const piIp      = (piIpAttr && piIpAttr.dataset.piIp) || "";

if (startBtn) startBtn.addEventListener("click", () => {
  if (logBox) logBox.innerHTML += "<div>[CLIENT] Starting INDIGO server...</div>";
  socket.emit("start_indigo");
});
if (stopBtn) stopBtn.addEventListener("click", () => {
  if (logBox) logBox.innerHTML += "<div>[CLIENT] Stopping INDIGO server...</div>";
  socket.emit("stop_indigo");
});
if (serverBtn) serverBtn.addEventListener("click", () => {
  if (!piIp) return;
  window.open(`http://${piIp}:7624`, "_blank");
});

const MAX_LOG_LINES = 100;
socket.on("server_log", (msg) => {
  if (!logBox) return;
  const line = document.createElement("div");
  line.textContent = msg;
  logBox.appendChild(line);
  while (logBox.children.length > MAX_LOG_LINES) logBox.removeChild(logBox.firstChild);
  logBox.scrollTop = logBox.scrollHeight;
});

setInterval(() => socket.emit("check_indigo_status"), 5000);
socket.on("indigo_status", (data) => {
  const statusText = document.getElementById("indigo-status");
  const ipText     = document.getElementById("server-ip");
  if (!statusText || !ipText) return;
  if (data.running) {
    statusText.textContent = "● Online";
    statusText.classList.remove("text-red-700");
    statusText.classList.add("text-green-700");
    ipText.textContent = `${data.ip}:7624`;
  } else {
    statusText.textContent = "● Offline";
    statusText.classList.remove("text-green-700");
    statusText.classList.add("text-red-700");
    ipText.textContent = "-";
  }
});
document.addEventListener("DOMContentLoaded", () => socket.emit("check_indigo_status"));

// === WEATHER ===
socket.on("update_weather", updateWeather);

function updateWeather(data) {
  const c = (id) => document.getElementById(id);
  if (c("condition"))     c("condition").textContent    = data.sky_conditions ?? "--";
  if (c("temperature"))   c("temperature").textContent  = data.temperature !== "--" ? `${data.temperature} °C` : "--";
  if (c("wind"))          c("wind").textContent         = data.wind_speed !== "--" ? `${data.wind_speed} mph` : "--";
  if (c("precip"))        c("precip").textContent       = data.precip_chance !== "--" ? `${data.precip_chance}%` : "--";
  if (c("last_checked"))  c("last_checked").textContent = data.last_checked ?? "--";

  const locEl = document.getElementById("weather-location");
  if (locEl && data.location_profile) {
    locEl.textContent = data.location_profile.replace("_", " ").toUpperCase();
  }
}

// === SUN & MOON PATH CANVASES ===
const solarCanvas = document.getElementById("solar-canvas");
const solarCtx    = solarCanvas ? solarCanvas.getContext("2d") : null;
const lunarCanvas = document.getElementById("lunar-canvas");
const lunarCtx    = lunarCanvas ? lunarCanvas.getContext("2d") : null;

let sunPath = [];
let moonPath = [];
let sunDot = { az: null, alt: null };
let moonDot = { az: null, alt: null };
let mountDot = { az: null, alt: null };

function toXY(canvas, az, alt) {
  const padding = 20;
  const w = canvas.width, h = canvas.height;
  const clampedAz = Math.min(360, Math.max(0, Number(az)));
  const clampedAlt = Math.min(90, Math.max(0, Number(alt)));
  const x = padding + (clampedAz / 360) * (w - 2 * padding);
  const y = h - padding - (clampedAlt / 90) * (h - 2 * padding);
  return [x, y];
}

function drawPath(ctx, canvas, path, pathColor = "#FFA500", dot, dotFill = "orange") {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const padding = 20;

  // Gridlines
  ctx.strokeStyle = "#ddd";
  ctx.lineWidth = 1;
  ctx.setLineDash([3, 3]);

  for (let alt = 0; alt <= 90; alt += 15) {
    const [, y] = toXY(canvas, 0, alt);
    ctx.beginPath(); ctx.moveTo(padding, y); ctx.lineTo(canvas.width - padding, y); ctx.stroke();
  }
  for (let az = 0; az <= 360; az += 45) {
    const [x] = toXY(canvas, az, 0);
    ctx.beginPath(); ctx.moveTo(x, padding); ctx.lineTo(x, canvas.height - padding); ctx.stroke();
  }
  ctx.setLineDash([]);

  // Labels
  ctx.fillStyle = "#333";
  ctx.font = "11px sans-serif";
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (let az = 0; az <= 360; az += 45) {
    const [x] = toXY(canvas, az, 0);
    ctx.fillText(`${az}°`, x, canvas.height - padding + 4);
  }
  ctx.textAlign = "right"; ctx.textBaseline = "middle";
  for (let alt = 0; alt <= 90; alt += 15) {
    const [, y] = toXY(canvas, 0, alt);
    ctx.fillText(`${alt}°`, padding - 4, y);
  }

  // Path
  if (path.length > 0) {
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    path.forEach((pt, i) => {
      const [x, y] = toXY(canvas, parseFloat(pt.az), parseFloat(pt.alt));
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = pathColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Target dot
  if (dot && dot.az != null && dot.alt != null) {
    const [dx, dy] = toXY(canvas, dot.az, dot.alt);
    ctx.beginPath();
    ctx.arc(dx, dy, 5, 0, 2 * Math.PI);
    ctx.fillStyle = dotFill;
    ctx.fill();
    ctx.strokeStyle = "#000";
    ctx.stroke();
  }

  // Mount dot
  if (mountDot.az != null && mountDot.alt != null) {
    const [mx, my] = toXY(canvas, mountDot.az, mountDot.alt);
    ctx.beginPath();
    ctx.arc(mx, my, 5, 0, 2 * Math.PI);
    ctx.fillStyle = "#007BFF";
    ctx.fill();
    ctx.strokeStyle = "#000";
    ctx.stroke();
  }
}

function resizeCanvas(cvs) {
  if (!cvs) return;
  cvs.width = cvs.clientWidth;
  cvs.height = cvs.clientHeight;
}
function redrawActiveCanvas() {
  if (ACTIVE_TARGET === "moon" && lunarCanvas && lunarCtx) {
    drawPath(lunarCtx, lunarCanvas, moonPath, "#cbd5e1", moonDot, "#cbd5e1"); // slate-300
  } else if (solarCanvas && solarCtx) {
    drawPath(solarCtx, solarCanvas, sunPath, "#FFA500", sunDot, "orange");
  }
}

window.addEventListener("resize", () => {
  resizeCanvas(solarCanvas); resizeCanvas(lunarCanvas);
  redrawActiveCanvas();
});
setTimeout(() => { resizeCanvas(solarCanvas); resizeCanvas(lunarCanvas); redrawActiveCanvas(); }, 100);

// Initial paths
function fetchSolarPath() {
  return fetch("/get_solar_path").then((res) => res.json()).then((data) => {
    sunPath = data.map(d => ({ az: parseFloat(d.az), alt: parseFloat(d.alt), time: d.time }));
  }).catch(() => {});
}
function fetchMoonPath() {
  return fetch("/get_moon_path").then((res) => res.json()).then((data) => {
    moonPath = data.map(d => ({ az: parseFloat(d.az), alt: parseFloat(d.alt), time: d.time }));
  }).catch(() => {});
}
Promise.all([fetchSolarPath(), fetchMoonPath()]).then(redrawActiveCanvas);

// === Tooltip (solar canvas) ===
const tooltip = document.getElementById("solar-tooltip");
let hoverPt = null;
if (solarCanvas && solarCtx) {
  solarCanvas.addEventListener("mousemove", (e) => {
    const rect = solarCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let closest = null;
    let minDist = Infinity;

    sunPath.forEach((pt) => {
      const [x, y] = toXY(solarCanvas, pt.az, pt.alt);
      const dist = Math.hypot(x - mouseX, y - mouseY);
      if (dist < minDist && dist < 10) {
        closest = { x, y, time: pt.time };
        minDist = dist;
      }
    });

    redrawActiveCanvas();
    if (closest && ACTIVE_TARGET === "sun") {
      hoverPt = closest;
      const [x, y] = [closest.x, closest.y];
      solarCtx.beginPath();
      solarCtx.arc(x, y, 6, 0, 2 * Math.PI);
      solarCtx.fillStyle = "rgba(255,165,0,0.3)";
      solarCtx.fill();

      solarCtx.fillStyle = "#000";
      solarCtx.font = "12px sans-serif";
      solarCtx.textAlign = "center";
      solarCtx.textBaseline = "bottom";
      solarCtx.fillText(closest.time ?? "??", x, y - 8);
    } else {
      hoverPt = null;
    }
  });
}

// === Astro/Solar updates (new + legacy) ===
function handleAstroOrSolarUpdate(data) {
  const g = (id) => document.getElementById(id);

  if (ACTIVE_TARGET === "moon") {
    // Use lunar values but populate the same elements
    g("sun_time")   && (g("sun_time").textContent   = data.moon_time ?? "--");
    g("solar_alt")  && (g("solar_alt").textContent  = data.lunar_alt ?? "--");
    g("solar_az")   && (g("solar_az").textContent   = data.lunar_az  ?? "--");
    g("sunrise")    && (g("sunrise").textContent    = data.moonrise  ?? "--");
    g("solar_noon") && (g("solar_noon").textContent = "—"); // no lunar noon
    g("sunset")     && (g("sunset").textContent     = data.moonset   ?? "--");

    // live dot
    if (data.lunar_az != null && data.lunar_alt != null) {
      moonDot.az = +data.lunar_az;
      moonDot.alt = +data.lunar_alt;
    }
  } else {
    // Normal solar fill
    g("sun_time")   && (g("sun_time").textContent   = data.sun_time ?? "--");
    g("solar_alt")  && (g("solar_alt").textContent  = data.solar_alt ?? "--");
    g("solar_az")   && (g("solar_az").textContent   = data.solar_az ?? "--");
    g("sunrise")    && (g("sunrise").textContent    = data.sunrise ?? "--");
    g("solar_noon") && (g("solar_noon").textContent = data.solar_noon ?? "--");
    g("sunset")     && (g("sunset").textContent     = data.sunset ?? "--");

    if (data.solar_az != null && data.solar_alt != null) {
      sunDot.az = +data.solar_az;
      sunDot.alt = +data.solar_alt;
    }
  }

  redrawActiveCanvas();
}
socket.on("solar_update", handleAstroOrSolarUpdate);  // legacy
socket.on("astro_update", handleAstroOrSolarUpdate);  // new unified

// === Mount state updates ===
setInterval(() => socket.emit("get_mount_solar_state"), 3000);

socket.on("mount_solar_state", (data) => {
  const raSolar  = document.getElementById("ra-solar");
  const decSolar = document.getElementById("dec-solar");
  const raMount  = document.getElementById("ra-mount");
  const decMount = document.getElementById("dec-mount");

  if (raSolar)  raSolar.textContent  = data.ra_solar  || "--:--:--";
  if (decSolar) decSolar.textContent = data.dec_solar || "--:--:--";
  if (raMount)  raMount.textContent  = data.ra_mount  || "--:--:--";
  if (decMount) decMount.textContent = data.dec_mount || "--:--:--";

  if (data.az_mount != null && data.alt_mount != null) {
    mountDot.az = parseFloat(data.az_mount);
    mountDot.alt = parseFloat(data.alt_mount);
    redrawActiveCanvas();
  }
});

socket.on("mount_altaz", ({ alt, az }) => {
  if (typeof alt === "number" && typeof az === "number") {
    mountDot.az = az;
    mountDot.alt = alt;
    redrawActiveCanvas();
  }
});

// === Mount status (string or object) ===
socket.on("mount_status", (payload) => {
  const statusEl = document.getElementById("mount-status");
  const statusText = (typeof payload === "string") ? payload : (payload?.status || "");

  if (statusEl) {
    statusEl.textContent = statusText;
    statusEl.classList.remove("text-gray-700","text-orange-500","text-green-600","text-blue-600","text-red-600");
    const s = statusText.toLowerCase();
    if (s.includes("slewing")) statusEl.classList.add("text-orange-500");
    else if (s.includes("tracking")) statusEl.classList.add("text-green-600");
    else if (s.includes("parked") || s.includes("unpark")) statusEl.classList.add("text-blue-600");
    else if (s.includes("error") || s.includes("fail")) statusEl.classList.add("text-red-600");
    else statusEl.classList.add("text-gray-700");
  }

  if (payload && typeof payload === "object") {
    const target = payload.target || ACTIVE_TARGET;
    applyTargetTheme(target);

    const tEl = document.getElementById("target-mode");
    const lEl = document.getElementById("location-profile");
    if (tEl) tEl.textContent = target.toUpperCase();
    if (lEl && payload.location) lEl.textContent = payload.location.replace("_", " ").toUpperCase();

    const targetRaEl = document.getElementById("target-ra");
    const targetDeEl = document.getElementById("target-dec");
    if (targetRaEl && payload.target_ra) targetRaEl.textContent = payload.target_ra;
    if (targetDeEl && payload.target_dec) targetDeEl.textContent = payload.target_dec;
  }
});

// === MOUNT CONTROL ===
const trackBtn       = document.getElementById("track-sun");
const parkBtn        = document.getElementById("park-mount");
const unparkBtn      = document.getElementById("unpark-mount");
const slewRateSelect = document.getElementById("slew-rate");
const slewRate       = () => (slewRateSelect && slewRateSelect.value) || "solar";

const directions = {
  "slew-north": "north",
  "slew-south": "south",
  "slew-east":  "east",
  "slew-west":  "west"
};

Object.keys(directions).forEach((btnId) => {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.addEventListener("mousedown", () => {
    socket.emit("slew_mount", { direction: directions[btnId], rate: slewRate() });
  });
  btn.addEventListener("mouseup", () => socket.emit("stop_mount"));
  btn.addEventListener("mouseleave", () => socket.emit("stop_mount"));
});

document.getElementById("stop-mount")?.addEventListener("click", () => socket.emit("stop_mount"));
if (trackBtn) trackBtn.addEventListener("click", () => socket.emit("track_sun"));
if (parkBtn)  parkBtn.addEventListener("click", () => socket.emit("park_mount"));
if (unparkBtn)unparkBtn.addEventListener("click", () => socket.emit("unpark_mount"));

socket.on("mount_coordinates", (coords) => {
  document.getElementById("ra-mount")?.textContent  = coords.ra_str ?? "--:--:--";
  document.getElementById("dec-mount")?.textContent = coords.dec_str ?? "--:--:--";
});

// === DROPDOWNS (safe if not present) ===
document.getElementById("target-select")?.addEventListener("change", async (e) => {
  const mode = (e.target.value || "sun").toLowerCase();

  // Immediate UI flip
  applyTargetTheme(mode);

  // Tell backend
  socket.emit("set_target", { mode });

  // Make sure the correct path is loaded right now
  try {
    if (mode === "moon") {
      const d = await fetch("/get_moon_path").then(r => r.json());
      moonPath = d.map(p => ({ az: +p.az, alt: +p.alt, time: p.time }));
    } else {
      const d = await fetch("/get_solar_path").then(r => r.json());
      sunPath = d.map(p => ({ az: +p.az, alt: +p.alt, time: p.time }));
    }
  } catch (_) { /* ignore fetch hiccups; next astro_update will fix */ }

  redrawActiveCanvas();
});

document.getElementById("location-select")?.addEventListener("change", async (e) => {
  const profile = (e.target.value || "chapel_hill").toLowerCase();

  // Tell backend (it will also emit fresh astro/weather)
  socket.emit("set_location_profile", { profile });

  // Optimistically update weather location label
  const locEl = document.getElementById("weather-location");
  if (locEl) locEl.textContent = profile.replace("_", " ").toUpperCase();

  // Re-fetch both paths so plot matches new site immediately
  try {
    const [sunData, moonData] = await Promise.all([
      fetch("/get_solar_path").then(r => r.json()),
      fetch("/get_moon_path").then(r => r.json())
    ]);
    sunPath  = sunData.map(p  => ({ az: +p.az,  alt: +p.alt,  time: p.time }));
    moonPath = moonData.map(p => ({ az: +p.az, alt: +p.alt, time: p.time }));
  } catch (_) { /* ignore; next astro_update will correct */ }

  redrawActiveCanvas();
});

// === FOCUSER ===
function nstepMove(direction) {
  socket.emit("nstep_move", { direction });
}
socket.on("nstep_position", (data) => {
  const setEl = document.getElementById("nstepSetPosition");
  const curEl = document.getElementById("nstepCurrentPosition");
  if ("set" in data && setEl)     setEl.textContent = data.set;
  if ("current" in data && curEl) curEl.textContent = data.current;
});

// === SCIENCE CAMERA ===
const img = document.getElementById("fc-preview");
const indicator = document.getElementById("fc-status-indicator");
let isPreviewRunning = false;
let previewPoll = null;

function startFcPreview() {
  if (isPreviewRunning) return;
  socket.emit("start_fc_preview");
  isPreviewRunning = true;

  if (img) {
    img.classList.remove("opacity-50", "max-w-[300px]", "bg-gray-400");
    if (previewPoll) clearInterval(previewPoll);
    previewPoll = setInterval(() => {
      if (!img) return;
      img.src = `http://${piIp}:8082/fc_preview.jpg?cache=${Date.now()}`;
    }, 500);

    img.onload = () => {
      indicator?.classList.replace("bg-red-500", "bg-green-500");
      img.classList.remove("opacity-50", "max-w-[300px]");
    };
    img.onerror = () => {
      indicator?.classList.replace("bg-green-500", "bg-red-500");
      img.src = "/static/no_preview.png";
      img.classList.add("opacity-50", "max-w-[300px]");
    };
  }
}
function stopFcPreview() {
  if (!isPreviewRunning) return;
  socket.emit("stop_fc_preview");
  isPreviewRunning = false;

  if (previewPoll) clearInterval(previewPoll);
  previewPoll = null;

  if (img) {
    img.src = "/static/no_preview.png";
    img.onload = null; img.onerror = null;
    indicator?.classList.remove("bg-green-500");
    indicator?.classList.add("bg-red-500");
    img.classList.add("opacity-50", "max-w-[300px]", "bg-gray-400");
  }
}
function triggerFcCapture() {
  socket.emit("trigger_fc_capture");
  if (!img) return;
  img.classList.add("ring", "ring-blue-400");
  setTimeout(() => img.classList.remove("ring", "ring-blue-400"), 500);
}
socket.on("fc_preview_status", (status) => { status ? startFcPreview() : stopFcPreview(); });
document.addEventListener("DOMContentLoaded", () => socket.emit("get_fc_status"));
window.startFcPreview = startFcPreview;
window.stopFcPreview = stopFcPreview;
window.triggerFcCapture = triggerFcCapture;

// === DOME CAMERA STATUS ===
const domeDot = document.getElementById("dome-status-indicator");
function updateDomeStatus() {
  fetch("/ping_dome_status").then((res) => {
    if (!domeDot) return;
    if (res.ok) {
      domeDot.classList.remove("bg-red-500");
      domeDot.classList.add("bg-green-500");
    } else {
      domeDot.classList.remove("bg-green-500");
      domeDot.classList.add("bg-red-500");
    }
  }).catch(() => {
    if (!domeDot) return;
    domeDot.classList.remove("bg-green-500");
    domeDot.classList.add("bg-red-500");
  });
}
setInterval(updateDomeStatus, 5000);
updateDomeStatus();

// === ARDUINO ===
function setDome(state) {
  socket.emit("set_dome", { state });
  console.log("[ARDUINO] Setting dome state:", state);
}
["1", "2"].forEach((index) => {
  const slider = document.getElementById(`etalon${index}Slider`);
  const valueLabel = document.getElementById(`etalon${index}Value`);
  if (slider && valueLabel) {
    slider.addEventListener("input", () => {
      const val = parseInt(slider.value);
      valueLabel.textContent = `${val}°`;
      socket.emit("set_etalon", { index: parseInt(index), value: val });
    });
  }
});
socket.on("arduino_state", (state) => {
  setArduinoStatus(state.connected);
  const domeLabel = document.getElementById("domeStatus");
  if (domeLabel) domeLabel.textContent = "Status: " + state.dome;
  for (let i = 1; i <= 2; i++) {
    const val = state[`etalon${i}`];
    const slider = document.getElementById(`etalon${i}Slider`);
    const label  = document.getElementById(`etalon${i}Value`);
    if (slider && label) { slider.value = val; label.textContent = `${val}°`; }
  }
});
function updateArduinoStatus() {
  window._arduinoResponded = true;
  socket.emit("get_arduino_state");
  setTimeout(() => { if (!window._arduinoResponded) setArduinoStatus(false); }, 2000);
}
function setArduinoStatus(connected) {
  const dot = document.getElementById("arduinoStatusDot");
  const text = document.getElementById("arduinoStatusText");
  if (!dot || !text) return;
  dot.classList.remove("bg-green-500","bg-gray-400","animate-pulse","bg-red-500");
  if (connected) { dot.classList.add("bg-green-500"); text.textContent = "Connected"; }
  else { dot.classList.add("bg-red-500","animate-pulse"); text.textContent = "Disconnected"; }
}

// === FILE HANDLER ===
const tableBody = document.getElementById("file-table-body");
const statusSpan = document.getElementById("file-status");

function renderFileList(files) {
  if (!tableBody || !statusSpan) return;
  tableBody.innerHTML = "";
  if (files.length === 0) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = `<td class="px-4 py-2 text-center text-gray-500" colspan="3">No files found</td>`;
    tableBody.appendChild(emptyRow);
    statusSpan.textContent = "Idle";
    return;
  }
  let currentStatus = "Idle";
  files.forEach((file) => {
    const row = document.createElement("tr");
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
    if (file.status === "Copying" || file.status === "Failed") currentStatus = file.status;
  });
  statusSpan.textContent = currentStatus;
}
socket.on("file_watch_status", (data) => {
  if (!data || !data.status || !statusSpan) return;
  if (data.status === "connected") { statusSpan.textContent = "Connected"; statusSpan.style.color = "green"; }
  else if (data.status === "disconnected") { statusSpan.textContent = "Disconnected"; statusSpan.style.color = "red"; }
});
fetch("/get_file_list").then((res) => res.json()).then(renderFileList).catch((err) => {
  console.error("Initial file list error:", err);
  if (statusSpan) statusSpan.textContent = "Error";
});
socket.on("file_list_update", (files) => renderFileList(files));