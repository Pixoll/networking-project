<script lang="ts">
  import { checkApiStatus, getSensorData } from "$lib/api";
  import AlertPanel from "$lib/components/AlertPanel.svelte";
  import Chart from "$lib/components/Chart.svelte";
  import DataTable from "$lib/components/DataTable.svelte";
  import MetricCard from "$lib/components/MetricCard.svelte";
  import { alertRanges, humidityOptions, pressureOptions, temperatureOptions } from "$lib/config";
  import type { Alert, AlertRange, Datapoint, ValueStatus } from "$lib/types";
  import { onDestroy, onMount } from "svelte";

  let data: Datapoint[] = [];
  let isOnline = false;
  let isAutoRefreshEnabled = false;
  let currentLimit = 20;
  let refreshIntervalMs = 2000;
  let activeAlerts: Set<string> = new Set();
  let alertLog: Alert[] = [];
  let lastDataTimestamp = 0;
  let autoRefreshInterval: number | null = null;

  $: latestData = data[0];
  $: alertCount = activeAlerts.size;
  $: currentTime = latestData ? formatTimestamp(latestData.timestamp) : "--";

  $: tempStatus = latestData ? getValueStatus(latestData.temperature, alertRanges.temperature) : "normal";
  $: pressureStatus = latestData ? getValueStatus(latestData.pressure, alertRanges.pressure) : "normal";
  $: humidityStatus = latestData ? getValueStatus(latestData.humidity, alertRanges.humidity) : "normal";

  $: if (isAutoRefreshEnabled && refreshIntervalMs) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }

  $: if (latestData) {
    checkAlerts(latestData);
  }

  onMount(() => {
    loadData();
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(loadData, refreshIntervalMs);
  }

  function stopAutoRefresh() {
    if (autoRefreshInterval) {
      clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;
    }
  }

  async function loadData() {
    try {
      const statusResponse = await checkApiStatus();
      isOnline = statusResponse.ok;

      if (!isOnline) return;

      const response = await getSensorData(currentLimit);

      if (!response.ok) {
        // noinspection ExceptionCaughtLocallyJS
        throw new Error(`HTTP error! status: ${response.response.status}`);
      }

      const apiResponse = response.data;
      const latestTimestamp = apiResponse.data[0]?.timestamp || 0;
      const hasNewData = latestTimestamp > lastDataTimestamp;

      if (hasNewData) {
        lastDataTimestamp = latestTimestamp;
        showNewDataNotification(apiResponse.data[0]);
      }

      data = apiResponse.data;
    } catch (error) {
      console.error(error);
      showError("Error al cargar los datos de la API");
    }
  }

  function toggleAutoRefresh() {
    isAutoRefreshEnabled = !isAutoRefreshEnabled;
    console.log(isAutoRefreshEnabled ?
      `🟢 Auto-refresh ACTIVADO cada ${refreshIntervalMs / 1000} segundos` :
      "🔴 Auto-refresh DESACTIVADO"
    );
  }

  function clearAllAlerts() {
    activeAlerts.clear();
    alertLog = [];
    document.querySelectorAll(".floating-alert").forEach(alert => alert.remove());
  }

  function checkAlerts(latestData: Datapoint) {
    const { temperature, pressure, humidity, timestamp } = latestData;
    const alerts: Alert[] = [];

    if (temperature < alertRanges.temperature.min) {
      alerts.push({
        type: "temperature",
        severity: "warning",
        message: `🥶 Temperatura muy baja: ${temperature.toFixed(1)}°C (Mín: ${alertRanges.temperature.min}°C)`,
        value: temperature,
        threshold: alertRanges.temperature.min,
        timestamp
      });
    } else if (temperature > alertRanges.temperature.max) {
      alerts.push({
        type: "temperature",
        severity: "critical",
        message: `🔥 Temperatura muy alta: ${temperature.toFixed(1)}°C (Máx: ${alertRanges.temperature.max}°C)`,
        value: temperature,
        threshold: alertRanges.temperature.max,
        timestamp
      });
    }

    if (pressure < alertRanges.pressure.min) {
      alerts.push({
        type: "pressure",
        severity: "warning",
        message: `📉 Presión muy baja: ${pressure.toFixed(1)} hPa (Mín: ${alertRanges.pressure.min} hPa)`,
        value: pressure,
        threshold: alertRanges.pressure.min,
        timestamp
      });
    } else if (pressure > alertRanges.pressure.max) {
      alerts.push({
        type: "pressure",
        severity: "critical",
        message: `📈 Presión muy alta: ${pressure.toFixed(1)} hPa (Máx: ${alertRanges.pressure.max} hPa)`,
        value: pressure,
        threshold: alertRanges.pressure.max,
        timestamp
      });
    }

    if (humidity < alertRanges.humidity.min) {
      alerts.push({
        type: "humidity",
        severity: "warning",
        message: `🏜️ Humedad muy baja: ${humidity.toFixed(1)}% (Mín: ${alertRanges.humidity.min}%)`,
        value: humidity,
        threshold: alertRanges.humidity.min,
        timestamp
      });
    } else if (humidity > alertRanges.humidity.max) {
      alerts.push({
        type: "humidity",
        severity: "warning",
        message: `💧 Humedad muy alta: ${humidity.toFixed(1)}% (Máx: ${alertRanges.humidity.max}%)`,
        value: humidity,
        threshold: alertRanges.humidity.max,
        timestamp
      });
    }

    alerts.forEach(alert => {
      showFloatingAlert(alert);
      addAlertToLog(alert);
    });
  }

  function showFloatingAlert(alert: Alert) {
    const alertKey = `${alert.type}-${alert.timestamp}`;
    if (activeAlerts.has(alertKey)) return;

    activeAlerts.add(alertKey);
    activeAlerts = activeAlerts;

    const alertDiv = document.createElement("div");
    alertDiv.className = `floating-alert alert-${alert.severity}`;
    alertDiv.innerHTML = `
      <div class="alert-content">
        <strong>⚠️ ALERTA DE SENSOR</strong>
        <p>${alert.message}</p>
        <small>Hora: ${formatTimestamp(alert.timestamp)}</small>
        <button class="alert-close">✕</button>
      </div>
    `;

    alertDiv.style.cssText = `
      position: fixed;
      top: ${20 + (activeAlerts.size - 1) * 120}px;
      right: 20px;
      background: ${alert.severity === "critical" ? "#e74c3c" : "#f39c12"};
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1000;
      font-weight: 600;
      max-width: 350px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      border-left: 5px solid ${alert.severity === "critical" ? "#c0392b" : "#e67e22"};
      animation: slideInAlert 0.5s ease-out;
    `;

    const closeBtn = alertDiv.querySelector(".alert-close");
    closeBtn?.addEventListener("click", () => removeAlert(alertDiv, alertKey));

    document.body.appendChild(alertDiv);

    const timeout = alert.severity === "critical" ? 10000 : 7000;
    setTimeout(() => removeAlert(alertDiv, alertKey), timeout);

    playAlertSound(alert.severity);
  }

  function removeAlert(alertDiv: HTMLElement, alertKey: string) {
    if (alertDiv.parentNode) {
      alertDiv.remove();
      activeAlerts.delete(alertKey);
      activeAlerts = activeAlerts;
    }
  }

  function addAlertToLog(alert: Alert) {
    alertLog = [alert, ...alertLog.slice(0, 19)]
  }

  function showNewDataNotification(newData: Datapoint) {
    if (!newData) return;

    const notification = document.createElement("div");
    notification.className = "new-data-notification";
    notification.innerHTML = `
      <div class="notification-content">
        <strong>📡 Nuevo dato recibido</strong>
        <p>🌡️ ${newData.temperature.toFixed(1)}°C | 🔧 ${newData.pressure.toFixed(1)} hPa | 💧 ${newData.humidity.toFixed(1)}%</p>
        <small>${formatTimestamp(newData.timestamp)}</small>
      </div>
    `;

    notification.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 999;
      font-weight: 600;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      animation: slideInNotification 0.5s ease-out;
      border-left: 5px solid #fff;
    `;

    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  function showError(message: string) {
    const errorDiv = document.createElement("div");
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #e74c3c;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1000;
      font-weight: 600;
    `;

    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
  }

  function playAlertSound(severity: ValueStatus) {
    try {
      const audioContext = new AudioContext();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = severity === "critical" ? 800 : 600;
      oscillator.type = "square";

      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.log("No se pudo reproducir sonido de alerta:", error);
    }
  }

  function getValueStatus(value: number, range: AlertRange): ValueStatus {
    if (value < range.min || value > range.max) {
      return value < range.min || value > range.max * 1.1 ? "critical" : "warning";
    }
    return "normal";
  }

  function formatTimestamp(timestamp: number): string {
    return new Date(timestamp).toLocaleString("en-GB", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      fractionalSecondDigits: 3,
    });
  }

  function handleRefreshRateChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    refreshIntervalMs = parseInt(target.value);
  }

  function handleTimeRangeChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    currentLimit = parseInt(target.value);
    loadData();
  }
</script>

<svelte:head>
  <style>
    @keyframes slideInNotification {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes slideInAlert {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .alert-content {
      position: relative;
    }

    .alert-close {
      position: absolute;
      top: -5px;
      right: -5px;
      background: rgba(255, 255, 255, 0.2);
      border: none;
      color: white;
      width: 25px;
      height: 25px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 14px;
    }

    .alert-close:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  </style>
</svelte:head>

<div class="container">
  <header class="header">
    <h1>🏭 IoT Industrial Dashboard</h1>
    <div class="header-controls">
      <div class="status-indicator">
        <span class="status-dot" class:online={isOnline} class:offline={!isOnline}></span>
        <span>API Status</span>
      </div>
      <div class="alert-indicator">
        <span>🚨 Alertas Activas</span>
        <span class="alert-counter" class:visible={alertCount > 0}>
          {alertCount || ""}
        </span>
      </div>
    </div>
  </header>

  <div class="dashboard">
    <div class="metrics-cards">
      <MetricCard
        title="Temperatura"
        icon="🌡️"
        value={latestData ? `${latestData.temperature.toFixed(1)}°C` : "--°C"}
        time={currentTime}
        range="Rango: 10°C - 40°C"
        status={tempStatus}
        bgClass="temperature"
      />

      <MetricCard
        title="Presión"
        icon="🔧"
        value={latestData ? `${latestData.pressure.toFixed(1)} hPa` : "-- hPa"}
        time={currentTime}
        range="Rango: 990 - 1040 hPa"
        status={pressureStatus}
        bgClass="pressure"
      />

      <MetricCard
        title="Humedad"
        icon="💧"
        value={latestData ? `${latestData.humidity.toFixed(1)}%` : "--%"}
        time={currentTime}
        range="Rango: 20% - 90%"
        status={humidityStatus}
        bgClass="humidity"
      />

      <MetricCard
        title="Total Lecturas"
        icon="📊"
        value={data.length.toString()}
        time={`Actualizado: ${new Date().toLocaleTimeString()}`}
        range=""
        status="normal"
        bgClass="total"
      />
    </div>

    <div class="controls">
      <button class="btn primary" on:click={loadData}>
        🔄 Actualizar
      </button>

      <button
        class="btn"
        class:primary={isAutoRefreshEnabled}
        class:secondary={!isAutoRefreshEnabled}
        on:click={toggleAutoRefresh}
      >
        ⏱️ Auto: {isAutoRefreshEnabled ? `ON (${refreshIntervalMs / 1000}s)` : "OFF"}
      </button>

      <button class="btn warning" on:click={clearAllAlerts}>
        🗑️ Limpiar Alertas
      </button>

      <select class="select" bind:value={currentLimit} on:change={handleTimeRangeChange}>
        <option value={10}>Últimos 10 datos</option>
        <option value={20}>Últimos 20 datos</option>
        <option value={50}>Últimos 50 datos</option>
      </select>

      <select class="select" bind:value={refreshIntervalMs} on:change={handleRefreshRateChange}>
        <option value={1000}>1 segundo</option>
        <option value={2000}>2 segundos</option>
        <option value={5000}>5 segundos</option>
        <option value={10000}>10 segundos</option>
      </select>
    </div>

    <div class="charts-grid">
      <Chart
        title="📈 Temperatura en Tiempo Real"
        chartId="temperatureChart"
        options={temperatureOptions}
        {data}
        dataKey="temperature"
      />

      <Chart
        title="📊 Presión en Tiempo Real"
        chartId="pressureChart"
        options={pressureOptions}
        {data}
        dataKey="pressure"
      />

      <Chart
        title="💧 Humedad en Tiempo Real"
        chartId="humidityChart"
        options={humidityOptions}
        {data}
        dataKey="humidity"
        fullWidth={true}
      />
    </div>

    <AlertPanel alerts={alertLog}/>

    <DataTable {data}/>
  </div>
</div>

<style>
  .container {
    margin: 0 auto;
    max-width: 1400px;
    padding: 20px;
  }

  .header {
    align-items: center;
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
    padding: 20px 30px;
  }

  .header h1 {
    color: #2c3e50;
    font-size: 2rem;
    font-weight: 700;
  }

  .header-controls {
    align-items: center;
    display: flex;
    gap: 20px;
  }

  .status-indicator {
    align-items: center;
    display: flex;
    font-weight: 600;
    gap: 10px;
  }

  .status-dot {
    animation: pulse 2s infinite;
    border-radius: 50%;
    display: inline-block;
    height: 12px;
    width: 12px;
  }

  .status-dot.online {
    background: #27ae60;
  }

  .status-dot.offline {
    background: #e74c3c;
  }

  .alert-indicator {
    align-items: center;
    display: flex;
    font-weight: 600;
    gap: 10px;
  }

  .alert-counter {
    animation: pulse 1s infinite;
    background: #e74c3c;
    border-radius: 50%;
    color: white;
    display: none;
    font-size: 0.8rem;
    font-weight: 700;
    min-width: 24px;
    padding: 4px 8px;
    text-align: center;
  }

  .alert-counter.visible {
    display: block;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .metrics-cards {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }

  .controls {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
  }

  .btn {
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 12px 24px;
    transition: all 0.3s ease;
  }

  .btn.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .btn.secondary {
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid #dddddd;
    color: #333333;
  }

  .btn.warning {
    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    color: white;
  }

  .btn:hover {
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
  }

  .select {
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid #dddddd;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    padding: 12px 20px;
  }

  .charts-grid {
    display: grid;
    gap: 25px;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  }

  @media (max-width: 768px) {
    .container {
      padding: 15px;
    }

    .header {
      flex-direction: column;
      gap: 15px;
      text-align: center;
    }

    .controls {
      justify-content: center;
    }

    .charts-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
