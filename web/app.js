const API_BASE = "";

const APP_DISPLAY_NAMES = {
  chrome: "Google Chrome",
  msedge: "Microsoft Edge",
  firefox: "Mozilla Firefox",
  brave: "Brave Browser",
  opera: "Opera",
  code: "Visual Studio Code",
  pycharm64: "PyCharm",
  idea64: "IntelliJ IDEA",
  devenv: "Visual Studio",
  notion: "Notion",
  teams: "Microsoft Teams",
  slack: "Slack",
  discord: "Discord",
  zoom: "Zoom",
  telegram: "Telegram",
  whatsapp: "WhatsApp",
  spotify: "Spotify",
  steam: "Steam",
  vlc: "VLC Media Player",
  obs64: "OBS Studio",
  winword: "Microsoft Word",
  excel: "Microsoft Excel",
  powerpnt: "Microsoft PowerPoint",
  outlook: "Microsoft Outlook",
  onenote: "Microsoft OneNote",
  notepad: "Notepad",
  "notepad++": "Notepad++",
};

function formatAppDisplayName(appKey) {
  const key = (appKey || "").trim().toLowerCase();
  if (!key) return "";
  return APP_DISPLAY_NAMES[key] || key;
}

function normalizeLockerAppInput(input) {
  const raw = (input || "").trim().toLowerCase();
  if (!raw) {
    return "";
  }
  if (APP_DISPLAY_NAMES[raw]) {
    return raw;
  }

  const directMatch = Object.entries(APP_DISPLAY_NAMES).find(
    ([, label]) => label.toLowerCase() === raw
  );
  if (directMatch) {
    return directMatch[0];
  }

  return raw;
}

const titles = {
  dashboard: {
    title: "Dashboard",
    subtitle: "Your usage overview in one place.",
  },
  reports: {
    title: "Reports",
    subtitle: "Weekly summaries of usage and mood.",
  },
  settings: {
    title: "Settings",
    subtitle: "Control limits, notifications, and integrations.",
  },
  health: {
    title: "Health",
    subtitle: "Adaptive focus score and recovery coaching.",
  },
  achievements: {
    title: "Achievements",
    subtitle: "Progress, rewards, and milestones.",
  },
  social: {
    title: "Social",
    subtitle: "Groups, challenges, and accountability.",
  },
  wellbeing: {
    title: "Well-Being",
    subtitle: "Mood trends and recommendations.",
  },
  locker: {
    title: "App Locker",
    subtitle: "Set per-app time limits and manage locked apps.",
  },
};

const state = {
  selectedGroupId: null,
  selectedChallengeId: null,
  healthTimer: null,
  health: null,
  activeAppTimer: null,
  usageAutoLogTimer: null,
  autoLoggingEnabled: true,
  moodAutoLogTimer: null,
  lockerRefreshTimer: null,
  lockerLiveStatusTimer: null,
  nextUsageLogAt: 0,
  usageChartMode: "stacked",
  weeklyUsageRows: [],
  localUsername: "",
  dailyLimitHours: 6,
  limitPopupDate: "",
  knownUnlockedAchievements: [],
  achievementSnapshotReady: false,
  nameModalResolver: null,
  nameModalInitialized: false,
};

function sanitizeUserName(name) {
  return (name || "").trim().replace(/\s+/g, " ").slice(0, 24);
}

function getSubtitleWithGreeting(viewName) {
  const base = titles[viewName].subtitle;
  if (!state.localUsername) {
    return base;
  }
  return `${base} Hi, ${state.localUsername}!`;
}

function updateGreetingUI() {
  const sidebarStatus = document.getElementById("sidebar-status");
  sidebarStatus.textContent = state.localUsername
    ? `Welcome, ${state.localUsername} • Status: synced`
    : "Status: synced";

  const activeButton = document.querySelector(".nav-btn.is-active");
  const activeView = activeButton ? activeButton.dataset.view : "dashboard";
  pageSubtitle.textContent = getSubtitleWithGreeting(activeView);
}

function loadUsageChartMode() {
  try {
    const stored = (localStorage.getItem("sg_usage_chart_mode") || "").trim().toLowerCase();
    return stored === "area" ? "area" : "stacked";
  } catch {
    return "stacked";
  }
}

function saveUsageChartMode(value) {
  try {
    localStorage.setItem("sg_usage_chart_mode", value === "area" ? "area" : "stacked");
  } catch {
  }
}

function loadAutoLoggingEnabled() {
  try {
    const stored = (localStorage.getItem("sg_auto_logging_enabled") || "").trim().toLowerCase();
    if (stored === "0" || stored === "false" || stored === "off") {
      return false;
    }
    return true;
  } catch {
    return true;
  }
}

function saveAutoLoggingEnabled(value) {
  try {
    localStorage.setItem("sg_auto_logging_enabled", value ? "1" : "0");
  } catch {
  }
}

const views = document.querySelectorAll(".view");
const navButtons = document.querySelectorAll(".nav-btn");
const toast = document.getElementById("toast");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function showPopupNotification(title, message) {
  showToast(`${title}: ${message}`);
  if (!("Notification" in window)) {
    return;
  }
  if (Notification.permission === "granted") {
    try {
      new Notification(title, { body: message });
    } catch {
    }
    return;
  }
  if (Notification.permission !== "denied") {
    Notification.requestPermission().then((permission) => {
      if (permission === "granted") {
        try {
          new Notification(title, { body: message });
        } catch {
        }
      }
    });
  }
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

async function apiPost(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

async function apiDelete(path) {
  const response = await fetch(`${API_BASE}${path}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

// ── App Locker ───────────────────────────────────────────────────────────────

async function refreshLocker() {
  const [statusData, limitsData, appsData] = await Promise.all([
    apiGet("/api/locker/status"),
    apiGet("/api/locker/limits"),
    apiGet("/api/locker/apps"),
  ]);

  const appOptions = document.getElementById("locker-app-options");
  const appInput = document.getElementById("locker-app-name");
  if (appOptions) {
    const currentInput = appInput ? appInput.value : "";
    appOptions.innerHTML = "";
    (appsData.items || []).forEach((app) => {
      const option = document.createElement("option");
      option.value = app;
      option.label = `${formatAppDisplayName(app)} (${app})`;
      appOptions.appendChild(option);
    });
    if (appInput && currentInput) {
      appInput.value = currentInput;
    }
  }

  // ── Locked apps ──────────────────────────────────────────────────────────
  const lockedList = document.getElementById("locker-locked-list");
  lockedList.innerHTML = "";
  const locked = statusData.items.filter((item) => item.locked);
  if (!locked.length) {
    lockedList.innerHTML = "<li>No apps are locked right now.</li>";
  } else {
    locked.forEach((item) => {
      const li = document.createElement("li");
      const since = item.locked_at ? item.locked_at.slice(0, 16) : "";
      li.innerHTML = `
        <span>🔒 <strong>${formatAppDisplayName(item.app)}</strong> (${item.app}) — locked since ${since} (${item.locked_reason || ""})</span>
        <button class="ghost-btn locker-unlock-btn" data-app="${item.app}">Unlock</button>
      `;
      lockedList.appendChild(li);
    });
  }

  // ── Limits + usage ────────────────────────────────────────────────────────
  const limitsList = document.getElementById("locker-limits-list");
  limitsList.innerHTML = "";
  if (!limitsData.items.length) {
    limitsList.innerHTML = "<li>No app limits configured yet.</li>";
  } else {
    limitsData.items.forEach((lim) => {
      const statusItem = statusData.items.find((s) => s.app === lim.app);
      const used = statusItem ? statusItem.used_minutes : 0;
      const isLocked = statusItem ? statusItem.locked : false;
      const pct = Math.min(100, Math.round((used / lim.daily_minutes) * 100));
      const li = document.createElement("li");
      li.innerHTML = `
        <span>${isLocked ? "🔒 " : ""}<strong>${formatAppDisplayName(lim.app)}</strong> (${lim.app}) — ${used}/${lim.daily_minutes} min (${pct}%)</span>
        <button class="ghost-btn locker-remove-btn" data-app="${lim.app}">Remove</button>
      `;
      limitsList.appendChild(li);
    });
  }
}

document.getElementById("locker-locked-list").addEventListener("click", async (event) => {
  const btn = event.target.closest(".locker-unlock-btn");
  if (!btn) return;
  const app = btn.dataset.app;
  try {
    await apiPost("/api/locker/unlock", { app });
    document.getElementById("locker-unlock-status").textContent = `${formatAppDisplayName(app)} unlocked.`;
    await refreshLocker();
  } catch (err) {
    document.getElementById("locker-unlock-status").textContent = `Error: ${err.message}`;
  }
});

document.getElementById("locker-limits-list").addEventListener("click", async (event) => {
  const btn = event.target.closest(".locker-remove-btn");
  if (!btn) return;
  const app = btn.dataset.app;
  const statusEl = document.getElementById("locker-add-status");
  try {
    await apiPost("/api/locker/limits/remove", { app });
    statusEl.textContent = `Removed limit: ${formatAppDisplayName(app)}`;
    await refreshLocker();
  } catch (err) {
    try {
      await apiDelete(`/api/locker/limits/${encodeURIComponent(app)}`);
      statusEl.textContent = `Removed limit: ${formatAppDisplayName(app)}`;
      await refreshLocker();
    } catch (fallbackErr) {
      showToast(`Error removing limit: ${fallbackErr.message}`);
    }
  }
});

document.getElementById("locker-save-btn").addEventListener("click", async () => {
  const rawAppInput = document.getElementById("locker-app-name").value.trim();
  const appName = normalizeLockerAppInput(rawAppInput);
  const dailyMinutes = Number(document.getElementById("locker-daily-minutes").value);
  const statusEl = document.getElementById("locker-add-status");
  if (!appName) {
    statusEl.textContent = "Please enter an app name.";
    return;
  }
  if (!dailyMinutes || dailyMinutes < 1) {
    statusEl.textContent = "Please enter a valid number of minutes.";
    return;
  }
  try {
    await apiPost("/api/locker/limits", { app: appName, daily_minutes: dailyMinutes });
    statusEl.textContent = `Limit set: ${formatAppDisplayName(appName)} → ${dailyMinutes} min / day`;
    document.getElementById("locker-app-name").value = "";
    await refreshLocker();
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
});

function resolveNameModal(value) {
  const backdrop = document.getElementById("username-onboarding");
  if (backdrop) {
    backdrop.hidden = true;
  }
  if (state.nameModalResolver) {
    const resolver = state.nameModalResolver;
    state.nameModalResolver = null;
    resolver(value);
  }
}

function initNameOnboardingModal() {
  if (state.nameModalInitialized) {
    return;
  }
  const backdrop = document.getElementById("username-onboarding");
  const input = document.getElementById("username-onboarding-input");
  const saveBtn = document.getElementById("username-onboarding-save");
  const skipBtn = document.getElementById("username-onboarding-skip");

  if (!backdrop || !input || !saveBtn || !skipBtn) {
    return;
  }

  state.nameModalInitialized = true;

  const doSave = () => resolveNameModal(input.value || "");
  const doSkip = () => resolveNameModal("");

  window.__sgSaveNameFromModal = doSave;
  window.__sgSkipNameFromModal = doSkip;

  saveBtn.onclick = doSave;
  skipBtn.onclick = doSkip;
  ["click", "pointerdown", "mousedown", "touchend"].forEach((eventName) => {
    saveBtn.addEventListener(eventName, (event) => {
      event.preventDefault();
      doSave();
    });
    skipBtn.addEventListener(eventName, (event) => {
      event.preventDefault();
      doSkip();
    });
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      doSave();
    }
    if (event.key === "Escape") {
      event.preventDefault();
      doSkip();
    }
  });

  document.addEventListener("click", (event) => {
    if (backdrop.hidden) {
      return;
    }
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }
    if (target.id === "username-onboarding-save") {
      doSave();
    }
    if (target.id === "username-onboarding-skip") {
      doSkip();
    }
  });

  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) {
      doSkip();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (!backdrop.hidden && event.key === "Escape") {
      event.preventDefault();
      doSkip();
    }
  });
}

function askNameInWebsiteModal() {
  return new Promise((resolve) => {
    initNameOnboardingModal();
    const backdrop = document.getElementById("username-onboarding");
    const input = document.getElementById("username-onboarding-input");
    if (!backdrop || !input) {
      resolve("");
      return;
    }
    state.nameModalResolver = resolve;
    backdrop.hidden = false;
    input.value = "";
    input.focus();
    setTimeout(() => {
      if (state.nameModalResolver === resolve && document.activeElement !== input) {
        input.focus();
      }
    }, 30);
  });
}

function formatMinutes(total) {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

function renderUsageChart(weeklyRows) {
  const chartCanvas = document.getElementById("usage-chart");
  if (!chartCanvas) {
    return;
  }

  const chartContext = chartCanvas.getContext("2d");
  const chartWidth = chartCanvas.clientWidth || 460;
  const chartHeight = chartCanvas.height || 170;
  chartCanvas.width = chartWidth;

  chartContext.clearRect(0, 0, chartWidth, chartHeight);

  const weeklyTotals = {};
  weeklyRows.forEach((row) => {
    Object.entries(row.totals).forEach(([appName, minutes]) => {
      weeklyTotals[appName] = (weeklyTotals[appName] || 0) + minutes;
    });
  });

  const topApps = Object.entries(weeklyTotals)
    .sort((first, second) => second[1] - first[1])
    .slice(0, 5)
    .map(([appName]) => appName);

  if (!topApps.length) {
    chartContext.fillStyle = "rgba(148, 163, 184, 0.9)";
    chartContext.font = "13px sans-serif";
    chartContext.textAlign = "center";
    chartContext.fillText("No weekly usage data yet", chartWidth / 2, chartHeight / 2);
    return;
  }

  const seriesNames = [...topApps];
  const otherUsed = weeklyRows.some((row) =>
    Object.entries(row.totals).some(([appName, minutes]) => !topApps.includes(appName) && minutes > 0)
  );
  if (otherUsed) {
    seriesNames.push("Other");
  }

  const dayTotals = weeklyRows.map((row) =>
    Object.values(row.totals).reduce((sum, minutes) => sum + minutes, 0)
  );
  const maxMinutes = Math.max(...dayTotals, 1);
  const leftPadding = 36;
  const rightPadding = 12;
  const topPadding = 38;
  const bottomPadding = 38;
  const chartAreaWidth = chartWidth - leftPadding - rightPadding;
  const chartAreaHeight = chartHeight - topPadding - bottomPadding;
  const barGap = 10;
  const barWidth = (chartAreaWidth - barGap * (weeklyRows.length - 1)) / weeklyRows.length;
  const themeStyles = getComputedStyle(document.documentElement);
  const labelColor = themeStyles.getPropertyValue("--text").trim() || "#e2e8f0";
  const palette = ["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa", "#fb7185", "#94a3b8"];
  const colorBySeries = {};
  seriesNames.forEach((name, index) => {
    colorBySeries[name] = palette[index % palette.length];
  });

  chartContext.strokeStyle = "rgba(148, 163, 184, 0.35)";
  chartContext.beginPath();
  chartContext.moveTo(leftPadding, chartHeight - bottomPadding);
  chartContext.lineTo(chartWidth - rightPadding, chartHeight - bottomPadding);
  chartContext.stroke();

  chartContext.fillStyle = labelColor;
  chartContext.font = "11px sans-serif";
  chartContext.textAlign = "left";
  let legendX = leftPadding;
  const legendY = 16;
  seriesNames.forEach((name) => {
    chartContext.fillStyle = colorBySeries[name];
    chartContext.fillRect(legendX, legendY - 9, 10, 10);
    chartContext.fillStyle = labelColor;
    chartContext.fillText(name, legendX + 14, legendY);
    legendX += Math.max(70, chartContext.measureText(name).width + 26);
  });

  const stackedSeries = seriesNames.map((seriesName) =>
    weeklyRows.map((row) => {
      if (seriesName === "Other") {
        return Object.entries(row.totals)
          .filter(([appName]) => !topApps.includes(appName))
          .reduce((sum, [, minutes]) => sum + minutes, 0);
      }
      return row.totals[seriesName] || 0;
    })
  );

  if (state.usageChartMode === "area") {
    const xPositions = weeklyRows.map((_, index) => leftPadding + index * (barWidth + barGap) + barWidth / 2);
    const cumulative = new Array(weeklyRows.length).fill(0);

    const smoothPathThroughPoints = (points, closeToBaseline = false) => {
      if (!points.length) {
        return;
      }
      chartContext.beginPath();
      chartContext.moveTo(points[0].x, points[0].y);
      for (let pointIndex = 0; pointIndex < points.length - 1; pointIndex += 1) {
        const current = points[pointIndex];
        const next = points[pointIndex + 1];
        const midX = (current.x + next.x) / 2;
        chartContext.quadraticCurveTo(current.x, current.y, midX, (current.y + next.y) / 2);
        if (pointIndex === points.length - 2) {
          chartContext.quadraticCurveTo(next.x, next.y, next.x, next.y);
        }
      }
      if (closeToBaseline) {
        chartContext.lineTo(points[points.length - 1].x, chartHeight - bottomPadding);
        chartContext.lineTo(points[0].x, chartHeight - bottomPadding);
        chartContext.closePath();
      }
    };

    stackedSeries.forEach((values, seriesIndex) => {
      const topPoints = values.map((value, dayIndex) => {
        cumulative[dayIndex] += value;
        const y = chartHeight - bottomPadding - (cumulative[dayIndex] / maxMinutes) * chartAreaHeight;
        return { x: xPositions[dayIndex], y };
      });

      const lowerBaseline = values.map((value, dayIndex) => {
        const lower = cumulative[dayIndex] - value;
        const y = chartHeight - bottomPadding - (lower / maxMinutes) * chartAreaHeight;
        return { x: xPositions[dayIndex], y };
      }).reverse();

      const areaPoints = [...topPoints, ...lowerBaseline];
      chartContext.fillStyle = `${colorBySeries[seriesNames[seriesIndex]]}cc`;
      smoothPathThroughPoints(areaPoints, true);
      chartContext.fill();
    });

    chartContext.fillStyle = labelColor;
    chartContext.textAlign = "center";
    weeklyRows.forEach((row, index) => {
      const yTop = chartHeight - bottomPadding - (dayTotals[index] / maxMinutes) * chartAreaHeight;
      if (dayTotals[index] > 0) {
        chartContext.fillText(String(dayTotals[index]), xPositions[index], yTop - 4);
      }
      chartContext.fillText(row.label, xPositions[index], chartHeight - bottomPadding + 14);
    });
  } else {
    chartContext.textAlign = "center";
    weeklyRows.forEach((row, index) => {
      const x = leftPadding + index * (barWidth + barGap);
      let accumulated = 0;

      seriesNames.forEach((seriesName, seriesIndex) => {
        const value = stackedSeries[seriesIndex][index];
        if (!value) {
          return;
        }

        const segmentHeight = (value / maxMinutes) * chartAreaHeight;
        const y = chartHeight - bottomPadding - accumulated - segmentHeight;
        chartContext.fillStyle = colorBySeries[seriesName];
        chartContext.fillRect(x, y, barWidth, segmentHeight);
        accumulated += segmentHeight;
      });

      if (dayTotals[index] > 0) {
        chartContext.fillStyle = labelColor;
        chartContext.fillText(String(dayTotals[index]), x + barWidth / 2, chartHeight - bottomPadding - accumulated - 4);
      }
      chartContext.fillStyle = labelColor;
      chartContext.fillText(row.label, x + barWidth / 2, chartHeight - bottomPadding + 14);
    });
  }
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function dateIso(daysAgo) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

async function refreshActiveAppField() {
  try {
    const result = await apiGet("/api/usage/current-app");
    const app = (result.app || "").trim();
    const appInput = document.getElementById("usage-app");
    const autoLogStatus = document.getElementById("auto-log-status");
    appInput.value = app;
    if (!state.autoLoggingEnabled) {
      autoLogStatus.textContent = "Auto logging: PAUSED";
      return;
    }
    autoLogStatus.textContent = app
      ? `Auto logging: ON (${app})`
      : "Auto logging: ON (waiting for active app)";
  } catch {
    document.getElementById("usage-app").value = "";
    document.getElementById("auto-log-status").textContent = state.autoLoggingEnabled
      ? "Auto logging: ON (active app unavailable)"
      : "Auto logging: PAUSED";
  }
}

async function autoLogActiveUsageMinute() {
  if (!state.autoLoggingEnabled) {
    document.getElementById("auto-log-status").textContent = "Auto logging: PAUSED";
    return;
  }
  try {
    const result = await apiGet("/api/usage/current-app");
    const app = (result.app || "").trim();
    if (!app) {
      document.getElementById("auto-log-status").textContent =
        "Auto logging: ON (waiting for active app)";
      return;
    }
    await apiPost("/api/usage", { app, duration: 1 });
    document.getElementById("auto-log-status").textContent = `Auto logging: ON (${app})`;
    await refreshDashboard();
    await refreshReports();
    await refreshLocker();
    state.nextUsageLogAt = Date.now() + 60000;
  } catch {
    document.getElementById("auto-log-status").textContent =
      "Auto logging: ON (active app unavailable)";
  }
}

function updateLockerLiveStatus() {
  const status = document.getElementById("locker-live-status");
  if (!status) {
    return;
  }
  if (!state.autoLoggingEnabled) {
    status.textContent = "Live sync: auto logging paused.";
    return;
  }
  const now = Date.now();
  const next = Number(state.nextUsageLogAt || 0);
  if (!next || next <= now) {
    status.textContent = "Live sync: usage tick due now...";
    return;
  }
  const secondsLeft = Math.max(0, Math.ceil((next - now) / 1000));
  status.textContent = `Live sync: next usage tick in ${secondsLeft}s.`;
}

async function autoLogMoodCheckin() {
  try {
    const result = await apiPost("/api/mood/auto", {});
    if (result.created) {
      document.getElementById("mood-status").textContent =
        `Auto mood check-in logged: ${result.mood}/10`;
      await refreshWellbeing();
      await refreshReports();
    }
  } catch {
  }
}

function updateAutoLogToggleUI() {
  const toggle = document.getElementById("auto-log-toggle");
  toggle.textContent = state.autoLoggingEnabled
    ? "Pause auto logging"
    : "Resume auto logging";
}

function setActiveView(name) {
  views.forEach((view) => view.classList.remove("is-visible"));
  document.getElementById(`view-${name}`).classList.add("is-visible");
  navButtons.forEach((btn) => btn.classList.remove("is-active"));
  const activeBtn = document.querySelector(`[data-view="${name}"]`);
  if (activeBtn) {
    activeBtn.classList.add("is-active");
  }
  pageTitle.textContent = titles[name].title;
  pageSubtitle.textContent = getSubtitleWithGreeting(name);
}

function updateTodayChip() {
  const now = new Date();
  const formatted = now.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  document.getElementById("today-chip").textContent = formatted;
}

async function refreshDashboard() {
  const recommendations = await apiGet("/api/recommendations");
  const list = document.getElementById("recommendations-list");
  list.innerHTML = "";
  recommendations.items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });

  const todayUsage = await apiGet(`/api/usage?date_str=${todayIso()}`);
  const yesterdayUsage = await apiGet(`/api/usage?date_str=${dateIso(1)}`);
  const weeklyDates = Array.from({ length: 7 }, (_, index) => dateIso(6 - index));
  const weeklyUsage = await Promise.all(
    weeklyDates.map((dateValue) => apiGet(`/api/usage?date_str=${dateValue}`))
  );
  const totalMinutes = todayUsage.items.reduce((sum, entry) => sum + entry.duration, 0);
  const yesterdayTotal = yesterdayUsage.items.reduce((sum, entry) => sum + entry.duration, 0);

  const totals = {};
  todayUsage.items.forEach((entry) => {
    totals[entry.app] = (totals[entry.app] || 0) + entry.duration;
  });
  const topApps = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, minutes]) => `${name} (${formatMinutes(minutes)})`)
    .join(", ");

  const weeklyRows = weeklyDates.map((dateValue, index) => {
    const perDayTotals = {};
    weeklyUsage[index].items.forEach((entry) => {
      perDayTotals[entry.app] = (perDayTotals[entry.app] || 0) + entry.duration;
    });
    const dayLabel = new Date(`${dateValue}T00:00:00`).toLocaleDateString(undefined, { weekday: "short" });
    return { label: dayLabel, totals: perDayTotals };
  });
  state.weeklyUsageRows = weeklyRows;
  renderUsageChart(weeklyRows);

  document.getElementById("usage-total").textContent =
    totalMinutes === 0 ? "No usage yet" : formatMinutes(totalMinutes);
  document.getElementById("usage-top").textContent =
    topApps || "No usage logged yet";

  if (yesterdayTotal === 0) {
    document.getElementById("usage-trend").textContent = "No data for yesterday";
  } else {
    const diff = totalMinutes - yesterdayTotal;
    const direction = diff === 0 ? "No change" : diff > 0 ? "Up" : "Down";
    document.getElementById("usage-trend").textContent =
      diff === 0 ? "Same as yesterday" : `${direction} ${formatMinutes(Math.abs(diff))}`;
  }

  const dailyLimitMinutes = Number(state.dailyLimitHours || 6) * 60;
  const dateKey = todayIso();
  if (totalMinutes > dailyLimitMinutes && state.limitPopupDate !== dateKey) {
    state.limitPopupDate = dateKey;
    showPopupNotification(
      "Daily Limit Exceeded",
      `You have used ${formatMinutes(totalMinutes)} today (limit ${state.dailyLimitHours}h).`
    );
  }
  if (totalMinutes <= dailyLimitMinutes && state.limitPopupDate === dateKey) {
    state.limitPopupDate = "";
  }
}

async function refreshReports() {
  const weekly = await apiGet("/api/reports/weekly");
  const usageList = document.getElementById("weekly-usage");
  const moodList = document.getElementById("weekly-mood");
  usageList.innerHTML = "";
  moodList.innerHTML = "";

  weekly.items.forEach((row) => {
    const usageItem = document.createElement("li");
    usageItem.textContent = row.total_minutes
      ? `${row.date}: ${formatMinutes(row.total_minutes)}`
      : `${row.date}: no usage logged`;
    usageList.appendChild(usageItem);

    const moodItem = document.createElement("li");
    moodItem.textContent =
      row.mood_avg != null
        ? `${row.date}: mood ${row.mood_avg.toFixed(1)}/10`
        : `${row.date}: no mood check-ins`;
    moodList.appendChild(moodItem);
  });
}

async function refreshSettings() {
  const limits = await apiGet("/api/settings/limits");
  document.getElementById("daily-limit").value = limits.daily_hours;
  state.dailyLimitHours = Number(limits.daily_hours || 6);

  const theme = await apiGet("/api/settings/theme");
  document.getElementById("theme-select").value = theme.theme;
  document.documentElement.dataset.theme = theme.theme;

  const prefs = await apiGet("/api/settings/notifications");
  const channels = prefs.channels || [];
  document.getElementById("notify-desktop").checked = channels.includes("desktop");
  document.getElementById("notify-email").checked = channels.includes("email");
  document.getElementById("notify-sms").checked = channels.includes("sms");
  document.getElementById("notify-voice").checked = channels.includes("voice");
  document.getElementById("notify-wallpaper").checked = channels.includes("wallpaper");
  document.getElementById("min-urgency").value = prefs.min_urgency || "low";
  document.getElementById("quiet-start").value = prefs.quiet_start;
  document.getElementById("quiet-end").value = prefs.quiet_end;
  document.getElementById("dnd").checked = prefs.dnd;

  const privacy = await apiGet("/api/social/privacy");
  document.getElementById("privacy-achievements").checked = privacy.share_achievements;
  document.getElementById("privacy-stats").checked = privacy.share_stats;
  document.getElementById("privacy-anon").checked = privacy.anonymous_leaderboards;
  document.getElementById("privacy-username").value = privacy.local_username || "you";
  document.getElementById("settings-username").value = privacy.local_username || "";
  const cleaned = sanitizeUserName(privacy.local_username || "");
  state.localUsername = cleaned.toLowerCase() === "you" ? "" : cleaned;
  updateGreetingUI();
  return privacy;
}

async function saveLocalUserNameFromSettings() {
  const currentPrivacy = await apiGet("/api/social/privacy");
  const chosen = sanitizeUserName(document.getElementById("settings-username").value) || "you";
  await apiPost("/api/social/privacy", {
    share_achievements: currentPrivacy.share_achievements,
    share_stats: currentPrivacy.share_stats,
    anonymous_leaderboards: currentPrivacy.anonymous_leaderboards,
    local_username: chosen,
  });

  document.getElementById("settings-username").value = chosen;
  document.getElementById("privacy-username").value = chosen;
  state.localUsername = chosen.toLowerCase() === "you" ? "" : chosen;
  localStorage.setItem("sg_name_onboarded", "1");
  updateGreetingUI();
  document.getElementById("username-status").textContent = "Name saved.";
}

async function ensureFirstTimeUserName(privacy) {
  let currentPrivacy = privacy;
  if (!currentPrivacy) {
    currentPrivacy = await apiGet("/api/social/privacy");
  }

  const storedOnboarding = localStorage.getItem("sg_name_onboarded") === "1";
  const currentName = sanitizeUserName(currentPrivacy.local_username || "");
  const hasRealName = currentName && currentName.toLowerCase() !== "you";

  if (hasRealName) {
    localStorage.setItem("sg_name_onboarded", "1");
    state.localUsername = currentName;
    updateGreetingUI();
    return;
  }

  if (!storedOnboarding) {
    const entered = await askNameInWebsiteModal();
    const cleaned = sanitizeUserName(entered);
    localStorage.setItem("sg_name_onboarded", "1");

    if (cleaned) {
      await apiPost("/api/social/privacy", {
        share_achievements: currentPrivacy.share_achievements,
        share_stats: currentPrivacy.share_stats,
        anonymous_leaderboards: currentPrivacy.anonymous_leaderboards,
        local_username: cleaned,
      });
      state.localUsername = cleaned;
      document.getElementById("privacy-username").value = cleaned;
      document.getElementById("settings-username").value = cleaned;
    }
  }

  updateGreetingUI();
}

async function refreshAchievements() {
  const status = await apiGet("/api/achievements/status");
  document.getElementById("achievement-level").textContent = `Level ${status.level}`;
  document.getElementById("level-progress").style.width = `${Math.round(
    status.progress * 100
  )}%`;
  document.getElementById("level-progress-text").textContent =
    `${Math.round(status.progress * 100)}% to next level`;

  const unlocked = document.getElementById("achievement-unlocked");
  unlocked.innerHTML = "";
  (status.unlocked.length ? status.unlocked : ["No achievements yet"]).forEach((name) => {
    const li = document.createElement("li");
    li.textContent = name;
    unlocked.appendChild(li);
  });

  const pending = document.getElementById("achievement-pending");
  pending.innerHTML = "";
  (status.pending.length ? status.pending : ["All achievements unlocked"]).forEach((name) => {
    const li = document.createElement("li");
    li.textContent = name;
    pending.appendChild(li);
  });

  const unlockedNames = status.unlocked || [];
  if (!state.achievementSnapshotReady) {
    state.knownUnlockedAchievements = [...unlockedNames];
    state.achievementSnapshotReady = true;
  } else {
    const newUnlocked = unlockedNames.filter(
      (name) => !state.knownUnlockedAchievements.includes(name)
    );
    newUnlocked.forEach((name) => {
      showPopupNotification("New Achievement Unlocked", name);
    });
    state.knownUnlockedAchievements = [...unlockedNames];
  }
}

async function refreshSocial() {
  const friends = await apiGet("/api/social/friends");
  const friendsList = document.getElementById("friends-list");
  friendsList.innerHTML = "";
  if (!friends.items.length) {
    friendsList.innerHTML = "<li>No friends yet</li>";
  } else {
    friends.items.forEach((friend) => {
      const li = document.createElement("li");
      const status = friend.blocked ? "blocked" : "active";
      li.textContent = `${friend.username} (${status})`;
      friendsList.appendChild(li);
    });
  }

  const groups = await apiGet("/api/social/groups");
  const groupsList = document.getElementById("groups-list");
  groupsList.innerHTML = "";
  if (!groups.items.length) {
    groupsList.innerHTML = "<li>No groups yet</li>";
  } else {
    groups.items.forEach((group) => {
      const li = document.createElement("li");
      li.textContent = `${group.name} (ID ${group.id})`;
      li.dataset.id = group.id;
      if (state.selectedGroupId === group.id) {
        li.classList.add("is-selected");
      }
      li.addEventListener("click", () => selectGroup(group.id));
      groupsList.appendChild(li);
    });
  }

  const challenges = await apiGet("/api/social/challenges");
  const challengesList = document.getElementById("challenges-list");
  challengesList.innerHTML = "";
  if (!challenges.items.length) {
    challengesList.innerHTML = "<li>No challenges yet</li>";
  } else {
    challenges.items.forEach((challenge) => {
      const li = document.createElement("li");
      li.textContent = `${challenge.title} [${challenge.status}] (ID ${challenge.id})`;
      li.dataset.id = challenge.id;
      if (state.selectedChallengeId === challenge.id) {
        li.classList.add("is-selected");
      }
      li.addEventListener("click", () => selectChallenge(challenge.id));
      challengesList.appendChild(li);
    });
  }
}

async function refreshLeaderboard() {
  const leaderboardList = document.getElementById("leaderboard-list");
  leaderboardList.innerHTML = "";
  if (!state.selectedChallengeId) {
    leaderboardList.innerHTML = "<li>Select a challenge</li>";
    return;
  }
  const leaderboard = await apiGet(
    `/api/social/challenges/leaderboard?challenge_id=${state.selectedChallengeId}`
  );
  if (!leaderboard.items.length) {
    leaderboardList.innerHTML = "<li>No scores yet</li>";
    return;
  }
  leaderboard.items.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `${row.username}: ${row.score}`;
    leaderboardList.appendChild(li);
  });
}

async function refreshWellbeing() {
  const recent = await apiGet("/api/mood/recent?limit=8");
  const recentList = document.getElementById("mood-recent");
  recentList.innerHTML = "";
  if (!recent.items.length) {
    recentList.innerHTML = "<li>No mood check-ins yet</li>";
  } else {
    recent.items.reverse().forEach((entry) => {
      const li = document.createElement("li");
      const time = entry.time ? entry.time.slice(11, 16) : "";
      const note = entry.note ? ` - ${entry.note}` : "";
      li.textContent = `${entry.date} ${time}: ${entry.mood}/10${note}`;
      recentList.appendChild(li);
    });
  }

  const insights = await apiGet("/api/wellbeing/insights");
  const trend = insights.trend;
  const trendText =
    trend.average == null
      ? "Mood trend: log a few days to see trends."
      : `Mood trend: ${trend.average.toFixed(1)} avg (${trend.trend || "no prior data"})`;
  document.getElementById("mood-trend").textContent = trendText;

  const correlation = insights.correlation;
  if (correlation.pair_count < 2) {
    document.getElementById("mood-correlation").textContent =
      "Screen time correlation: log more data to compare days.";
  } else {
    const corrValue =
      correlation.correlation == null
        ? "not enough variance"
        : `corr ${correlation.correlation.toFixed(2)}`;
    if (correlation.high_avg != null && correlation.low_avg != null) {
      document.getElementById("mood-correlation").textContent =
        `Screen time correlation: ${corrValue}, 8h+ mood ${correlation.high_avg.toFixed(
          1
        )} vs <8h mood ${correlation.low_avg.toFixed(1)}`;
    } else {
      document.getElementById("mood-correlation").textContent =
        `Screen time correlation: ${corrValue}`;
    }
  }

  const patternsText = insights.patterns.length
    ? `Patterns: ${insights.patterns.join(" | ")}`
    : "Patterns: nothing notable yet.";
  document.getElementById("mood-patterns").textContent = patternsText;

  const recList = document.getElementById("mood-recommendations");
  recList.innerHTML = "";
  insights.recommendations.forEach((tip) => {
    const li = document.createElement("li");
    li.textContent = tip;
    recList.appendChild(li);
  });
}

function loadHealthState() {
  const saved = localStorage.getItem("sg_health");
  if (saved) {
    return JSON.parse(saved);
  }
  return {
    continuousTime: 0,
    focusWindow: 50 * 60,
    recoveryDuration: 90,
    inRecovery: false,
    recoveryRemaining: 0,
    blueLightExposure: 0,
  };
}

function saveHealthState() {
  localStorage.setItem("sg_health", JSON.stringify(state.health));
}

function updateHealthUI() {
  const progress = document.getElementById("strain-progress");
  const percent = Math.min(100, (state.health.continuousTime / state.health.focusWindow) * 100);
  const focusScore = Math.max(0, Math.round(100 - percent));
  progress.style.width = `${percent}%`;
  const remaining = Math.max(0, state.health.focusWindow - state.health.continuousTime);
  document.getElementById("health-timer").textContent = state.health.inRecovery
    ? `Recovery in progress: ${state.health.recoveryRemaining}s remaining`
    : `Next recovery in: ${remaining}s`;
  document.getElementById("focus-score").textContent = `Focus score: ${focusScore}/100`;
  document.getElementById("blue-light").textContent =
    `Blue light exposure: ${state.health.blueLightExposure}s`;

  let tip = "Focus health looks good.";
  if (percent >= 100) {
    tip = "High eye load detected. Start a recovery session now.";
  } else if (percent >= 80) {
    tip = "Eye load rising. Consider recovery soon.";
  } else if (percent >= 50) {
    tip = "Steady focus. Keep blinking and adjust posture.";
  }
  document.getElementById("focus-tip").textContent = `Recovery tip: ${tip}`;
}

function tickHealth() {
  if (!state.health.inRecovery) {
    state.health.continuousTime += 1;
    state.health.blueLightExposure += 1;
    if (state.health.continuousTime >= state.health.focusWindow) {
      showToast("High eye load detected. Recovery session recommended.");
    }
  } else if (state.health.recoveryRemaining > 0) {
    state.health.recoveryRemaining -= 1;
  } else {
    state.health.inRecovery = false;
    state.health.continuousTime = Math.max(0, state.health.continuousTime - 15 * 60);
  }
  updateHealthUI();
  saveHealthState();
}

function startHealthTimer() {
  if (state.healthTimer) {
    clearInterval(state.healthTimer);
  }
  state.health = loadHealthState();
  updateHealthUI();
  state.healthTimer = setInterval(tickHealth, 1000);
}

function selectGroup(groupId) {
  state.selectedGroupId = groupId;
  refreshSocial();
  refreshMessages();
}

async function refreshMessages() {
  const messagesList = document.getElementById("messages-list");
  messagesList.innerHTML = "";
  if (!state.selectedGroupId) {
    messagesList.innerHTML = "<li>Select a group</li>";
    return;
  }
  const messages = await apiGet(`/api/social/groups/messages?group_id=${state.selectedGroupId}`);
  if (!messages.items.length) {
    messagesList.innerHTML = "<li>No messages yet</li>";
  } else {
    messages.items.forEach((msg) => {
      const li = document.createElement("li");
      li.textContent = `${msg.created_at} ${msg.sender}: ${msg.content}`;
      messagesList.appendChild(li);
    });
  }
}

function selectChallenge(challengeId) {
  state.selectedChallengeId = challengeId;
  refreshSocial();
  refreshLeaderboard();
}

async function init() {
  initNameOnboardingModal();
  state.autoLoggingEnabled = loadAutoLoggingEnabled();
  state.usageChartMode = loadUsageChartMode();
  const chartModeSelect = document.getElementById("usage-chart-mode");
  if (chartModeSelect) {
    chartModeSelect.value = state.usageChartMode;
  }
  updateTodayChip();
  startHealthTimer();
  updateAutoLogToggleUI();
  await refreshActiveAppField();
  if (state.activeAppTimer) {
    clearInterval(state.activeAppTimer);
  }
  state.activeAppTimer = setInterval(refreshActiveAppField, 3000);
  if (state.usageAutoLogTimer) {
    clearInterval(state.usageAutoLogTimer);
  }
  state.nextUsageLogAt = Date.now() + 60000;
  state.usageAutoLogTimer = setInterval(autoLogActiveUsageMinute, 60000);
  if (state.lockerLiveStatusTimer) {
    clearInterval(state.lockerLiveStatusTimer);
  }
  state.lockerLiveStatusTimer = setInterval(updateLockerLiveStatus, 1000);
  updateLockerLiveStatus();
  await autoLogActiveUsageMinute();
  if (state.moodAutoLogTimer) {
    clearInterval(state.moodAutoLogTimer);
  }
  state.moodAutoLogTimer = setInterval(autoLogMoodCheckin, 60 * 60 * 1000);
  await autoLogMoodCheckin();
  const privacy = await refreshSettings();
  await ensureFirstTimeUserName(privacy);
  setActiveView("dashboard");
  await refreshDashboard();
  await refreshReports();
  await refreshAchievements();
  await refreshSocial();
  await refreshWellbeing();
  await refreshLocker();

  // Auto-refresh locker status every 15 seconds (apps can be auto-locked by usage)
  if (state.lockerRefreshTimer) {
    clearInterval(state.lockerRefreshTimer);
  }
  state.lockerRefreshTimer = setInterval(() => {
    refreshLocker().catch(() => {});
  }, 15000);
}

navButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const view = btn.dataset.view;
    setActiveView(view);
  });
});

document.getElementById("refresh-all").addEventListener("click", async () => {
  await refreshDashboard();
  await refreshReports();
  await refreshAchievements();
  await refreshSocial();
  await refreshWellbeing();
  await refreshLocker();
  showToast("Data refreshed");
});

document.getElementById("usage-chart-mode").addEventListener("change", (event) => {
  state.usageChartMode = event.target.value === "area" ? "area" : "stacked";
  saveUsageChartMode(state.usageChartMode);
  renderUsageChart(state.weeklyUsageRows || []);
});

document.getElementById("auto-log-toggle").addEventListener("click", async () => {
  state.autoLoggingEnabled = !state.autoLoggingEnabled;
  saveAutoLoggingEnabled(state.autoLoggingEnabled);
  updateAutoLogToggleUI();
  state.nextUsageLogAt = Date.now() + 60000;
  updateLockerLiveStatus();
  await refreshActiveAppField();
});

document.getElementById("reset-data").addEventListener("click", async () => {
  await apiPost("/api/admin/reset");
  document.getElementById("usage-status").textContent = "All data cleared.";
  await refreshDashboard();
  await refreshReports();
  await refreshAchievements();
  await refreshSocial();
  await refreshWellbeing();
});

document.getElementById("save-limits").addEventListener("click", async () => {
  const daily_hours = Number(document.getElementById("daily-limit").value || 6);
  await apiPost("/api/settings/limits", { daily_hours });
  showToast("Usage limits saved");
});

document.getElementById("save-theme").addEventListener("click", async () => {
  const theme = document.getElementById("theme-select").value;
  const result = await apiPost("/api/settings/theme", { theme });
  document.documentElement.dataset.theme = result.theme;
  showToast("Theme updated");
});

document.getElementById("save-username").addEventListener("click", async () => {
  await saveLocalUserNameFromSettings();
});

document.getElementById("save-notifications").addEventListener("click", async () => {
  const channels = [];
  if (document.getElementById("notify-desktop").checked) channels.push("desktop");
  if (document.getElementById("notify-email").checked) channels.push("email");
  if (document.getElementById("notify-sms").checked) channels.push("sms");
  if (document.getElementById("notify-voice").checked) channels.push("voice");
  if (document.getElementById("notify-wallpaper").checked) channels.push("wallpaper");

  const payload = {
    channels,
    min_urgency: document.getElementById("min-urgency").value,
    quiet_start: Number(document.getElementById("quiet-start").value || 22),
    quiet_end: Number(document.getElementById("quiet-end").value || 7),
    dnd: document.getElementById("dnd").checked,
  };
  await apiPost("/api/settings/notifications", payload);
  document.getElementById("notifications-status").textContent = "Preferences saved.";
});

document.getElementById("sync-calendar").addEventListener("click", async () => {
  const enabled = document.getElementById("calendar-enabled").checked;
  const statusEl = document.getElementById("calendar-status");
  if (!enabled) {
    statusEl.textContent = "Status: calendar sync is disabled";
    return;
  }
  try {
    const payload = {
      credentials_path: document.getElementById("calendar-credentials").value.trim(),
      calendar_id: document.getElementById("calendar-id").value.trim() || "primary",
      base_daily_limit_hours: Number(document.getElementById("daily-limit").value || 6),
      exam_mode: document.getElementById("exam-mode").checked,
    };
    const result = await apiPost("/api/calendar/sync", payload);
    statusEl.textContent =
      `Status: ${result.event_count} events, ${result.busy_hours.toFixed(
        1
      )} busy hours, suggested limit ${result.suggested_limit}h`;
  } catch (error) {
    statusEl.textContent = `Status: sync failed - ${error.message}`;
  }
});

document.getElementById("start-recovery").addEventListener("click", () => {
  state.health.inRecovery = true;
  state.health.recoveryRemaining = state.health.recoveryDuration;
  updateHealthUI();
  saveHealthState();
});

document.getElementById("friend-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("friend-username").value.trim();
  if (!username) return;
  await apiPost("/api/social/friends", { username });
  document.getElementById("friend-username").value = "";
  document.getElementById("friends-status").textContent = `Added ${username}.`;
  await refreshSocial();
});

async function handleBlock(blocked) {
  const username = document.getElementById("block-username").value.trim();
  if (!username) return;
  try {
    await apiPost("/api/social/friends/block", { username, blocked });
    document.getElementById("friends-status").textContent =
      `${blocked ? "Blocked" : "Unblocked"} ${username}.`;
    await refreshSocial();
  } catch (error) {
    document.getElementById("friends-status").textContent = error.message;
  }
}

document.getElementById("block-user").addEventListener("click", () => handleBlock(true));
document.getElementById("unblock-user").addEventListener("click", () => handleBlock(false));

document.getElementById("group-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.getElementById("group-name").value.trim();
  if (!name) return;
  const is_private = document.getElementById("group-private").checked;
  await apiPost("/api/social/groups", { name, is_private });
  document.getElementById("group-name").value = "";
  document.getElementById("group-status").textContent = "Group created.";
  await refreshSocial();
});

document.getElementById("member-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("member-username").value.trim();
  if (!state.selectedGroupId || !username) {
    document.getElementById("group-status").textContent =
      "Select a group and enter a username.";
    return;
  }
  await apiPost("/api/social/groups/members", {
    group_id: state.selectedGroupId,
    username,
  });
  document.getElementById("member-username").value = "";
  document.getElementById("group-status").textContent = `Added ${username} to group.`;
});

document.getElementById("message-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = document.getElementById("group-message").value.trim();
  if (!state.selectedGroupId || !content) {
    document.getElementById("group-status").textContent =
      "Select a group and enter a message.";
    return;
  }
  await apiPost("/api/social/groups/messages", {
    group_id: state.selectedGroupId,
    content,
  });
  document.getElementById("group-message").value = "";
  await refreshMessages();
});

document.getElementById("challenge-form-2").addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = document.getElementById("challenge-title").value.trim();
  const challenge_type = document.getElementById("challenge-type").value;
  const duration_days = Number(document.getElementById("challenge-days").value || 7);
  const participants = document
    .getElementById("challenge-participants")
    .value.split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const anonymous = document.getElementById("challenge-anon").checked;

  if (!title) {
    document.getElementById("challenge-status").textContent = "Enter a challenge title.";
    return;
  }
  await apiPost("/api/social/challenges", {
    title,
    challenge_type,
    duration_days,
    participants,
    group_id: state.selectedGroupId,
    anonymous,
  });
  document.getElementById("challenge-title").value = "";
  document.getElementById("challenge-participants").value = "";
  document.getElementById("challenge-status").textContent = "Challenge created.";
  await refreshSocial();
});

document.getElementById("refresh-leaderboard").addEventListener("click", refreshLeaderboard);

document.getElementById("share-form-2").addEventListener("submit", async (event) => {
  event.preventDefault();
  const achievement_id = document.getElementById("share-achievement").value.trim();
  const message = document.getElementById("share-message").value.trim();
  const audience = document.getElementById("share-audience").value;
  const targets = document
    .getElementById("share-targets")
    .value.split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!achievement_id) {
    document.getElementById("share-status").textContent = "Enter an achievement.";
    return;
  }
  await apiPost("/api/social/shares", { achievement_id, message, audience, targets });
  document.getElementById("share-status").textContent = "Achievement shared.";
  document.getElementById("share-achievement").value = "";
  document.getElementById("share-message").value = "";
  document.getElementById("share-targets").value = "";
});

document.getElementById("save-privacy").addEventListener("click", async () => {
  const localUsername = sanitizeUserName(document.getElementById("privacy-username").value) || "you";
  const payload = {
    share_achievements: document.getElementById("privacy-achievements").checked,
    share_stats: document.getElementById("privacy-stats").checked,
    anonymous_leaderboards: document.getElementById("privacy-anon").checked,
    local_username: localUsername,
  };
  await apiPost("/api/social/privacy", payload);
  document.getElementById("privacy-username").value = localUsername;
  document.getElementById("settings-username").value = localUsername;
  state.localUsername = localUsername.toLowerCase() === "you" ? "" : localUsername;
  localStorage.setItem("sg_name_onboarded", "1");
  updateGreetingUI();
  document.getElementById("privacy-status").textContent = "Privacy settings saved.";
  await refreshSettings();
});

document.getElementById("generate-summary").addEventListener("click", async () => {
  const summary = await apiGet("/api/wellbeing/summary");
  document.getElementById("integration-status").textContent =
    `Summary: ${summary.lines.join(" | ")}`;
});

init().catch((error) => {
  showToast(error.message);
  console.error(error);
});
