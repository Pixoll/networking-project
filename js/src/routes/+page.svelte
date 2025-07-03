<script lang="ts">
  import ApexCharts from "apexcharts";
  import { onMount } from "svelte";

  type AlertRange = {
    min: number;
    max: number;
  };

  type ValueStatus = "critical" | "warning" | "normal";

  type Alert = {
    type: string;
    severity: ValueStatus;
    message: string;
    value: number;
    threshold: number;
    timestamp: number;
  };

  type Datapoint = {
    id: number;
    temperature: number;
    pressure: number;
    humidity: number;
    timestamp: number;
  };

  type AlertType = "temperature" | "pressure" | "humidity";

  const API_BASE_URL = "http://localhost:5000";

  const alertRanges: Record<AlertType, AlertRange> = {
    temperature: { min: 10, max: 40 },
    pressure: { min: 990, max: 1040 },
    humidity: { min: 20, max: 90 }
  };

  class IoTDashboard {
    private temperatureChart: ApexCharts;
    private pressureChart: ApexCharts;
    private humidityChart: ApexCharts;
    private autoRefreshInterval: number | null;
    private isAutoRefreshEnabled: boolean;
    private currentLimit: number;
    private lastDataTimestamp: number;
    private refreshIntervalMs: number;
    private activeAlerts: Set<string>;

    constructor() {
      this.autoRefreshInterval = null;
      this.isAutoRefreshEnabled = false;
      this.currentLimit = 20;
      this.lastDataTimestamp = 0;
      this.refreshIntervalMs = 2000;

      this.activeAlerts = new Set();

      const commonOptions = {
        chart: {
          type: "line",
          height: 300,
          animations: {
            enabled: true,
            easing: "easeinout",
            speed: 800
          },
          toolbar: {
            show: false
          },
          zoom: {
            enabled: false
          }
        },
        stroke: {
          curve: "smooth",
          width: 3
        },
        markers: {
          size: 6,
          strokeWidth: 2,
          fillOpacity: 1,
          strokeOpacity: 1
        },
        grid: {
          borderColor: "#e7e7e7",
          row: {
            colors: ["#f3f3f3", "transparent"],
            opacity: 0.5
          }
        },
        xaxis: {
          type: "datetime",
          labels: {
            format: "HH:mm:ss"
          }
        },
        tooltip: {
          x: {
            format: "dd/MM/yy HH:mm:ss"
          }
        },
        annotations: {
          yaxis: []
        }
      };

      const temperatureOptions = {
        ...commonOptions,
        series: [{
          name: "Temperatura (°C)",
          data: []
        }],
        colors: ["#ff6b6b"],
        yaxis: {
          title: {
            text: "Temperatura (°C)"
          },
          labels: {
            formatter: (value: number) => `${value.toFixed(1)}°C`
          }
        },
        annotations: {
          yaxis: [
            {
              y: alertRanges.temperature.max,
              borderColor: "#e74c3c",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Máx: ${alertRanges.temperature.max}°C`,
                style: { color: "#e74c3c", background: "#ffffff" }
              }
            },
            {
              y: alertRanges.temperature.min,
              borderColor: "#3498db",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Mín: ${alertRanges.temperature.min}°C`,
                style: { color: "#3498db", background: "#ffffff" }
              }
            }
          ]
        }
      };

      const pressureOptions = {
        ...commonOptions,
        series: [{
          name: "Presión (hPa)",
          data: []
        }],
        colors: ["#4ecdc4"],
        yaxis: {
          title: {
            text: "Presión (hPa)"
          },
          labels: {
            formatter: (value: number) => `${value.toFixed(1)} hPa`
          }
        },
        annotations: {
          yaxis: [
            {
              y: alertRanges.pressure.max,
              borderColor: "#e74c3c",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Máx: ${alertRanges.pressure.max} hPa`,
                style: { color: "#e74c3c", background: "#ffffff" }
              }
            },
            {
              y: alertRanges.pressure.min,
              borderColor: "#3498db",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Mín: ${alertRanges.pressure.min} hPa`,
                style: { color: "#3498db", background: "#ffffff" }
              }
            }
          ]
        }
      };

      const humidityOptions = {
        ...commonOptions,
        series: [{
          name: "Humedad (%)",
          data: []
        }],
        colors: ["#45b7d1"],
        yaxis: {
          title: {
            text: "Humedad (%)"
          },
          labels: {
            formatter: (value: number) => `${value.toFixed(1)}%`
          },
          min: 0,
          max: 100
        },
        annotations: {
          yaxis: [
            {
              y: alertRanges.humidity.max,
              borderColor: "#e74c3c",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Máx: ${alertRanges.humidity.max}%`,
                style: { color: "#e74c3c", background: "#ffffff" }
              }
            },
            {
              y: alertRanges.humidity.min,
              borderColor: "#3498db",
              borderWidth: 2,
              strokeDashArray: 5,
              label: {
                text: `Mín: ${alertRanges.humidity.min}%`,
                style: { color: "#3498db", background: "#ffffff" }
              }
            }
          ]
        }
      };

      this.temperatureChart = new ApexCharts(
        document.querySelector("#temperatureChart"),
        temperatureOptions
      );
      this.temperatureChart.render();

      this.pressureChart = new ApexCharts(
        document.querySelector("#pressureChart"),
        pressureOptions
      );
      this.pressureChart.render();

      this.humidityChart = new ApexCharts(
        document.querySelector("#humidityChart"),
        humidityOptions
      );
      this.humidityChart.render();

      document.getElementById("refreshBtn")?.addEventListener("click", () => {
        this.loadData();
      });

      document.getElementById("autoRefreshBtn")?.addEventListener("click", () => {
        this.toggleAutoRefresh();
      });

      document.getElementById("timeRange")?.addEventListener("change", (e) => {
        this.currentLimit = parseInt((e.target as HTMLSelectElement).value);
        this.loadData();
      });

      document.getElementById("clearAlertsBtn")?.addEventListener("click", () => {
        this.clearAllAlerts();
      });

      document.getElementById("refreshRate")?.addEventListener("change", (e) => {
        this.refreshIntervalMs = parseInt((e.target as HTMLSelectElement).value);
        if (this.isAutoRefreshEnabled) {
          this.toggleAutoRefresh();
          this.toggleAutoRefresh();
        }
      });

      this.loadData();
    }

    async checkApiStatus(): Promise<boolean> {
      try {
        const response = await fetch(`${API_BASE_URL}/api/ping`);
        const statusElement = document.getElementById("connectionStatus");

        if (response.ok) {
          statusElement?.classList.remove("offline");
          statusElement?.classList.add("online");
        } else {
          // noinspection ExceptionCaughtLocallyJS
          throw new Error("API not responding");
        }

        return true;
      } catch (error) {
        console.error(error);
        const statusElement = document.getElementById("connectionStatus");
        statusElement?.classList.remove("online");
        statusElement?.classList.add("offline");
        return false;
      }
    }

    async loadData(): Promise<void> {
      const isOnline = await this.checkApiStatus();
      if (!isOnline) {
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/sensors/data?limit=${this.currentLimit}`);

        if (!response.ok) {
          // noinspection ExceptionCaughtLocallyJS
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const apiResponse = await response.json() as { data: Datapoint[] };

        const latestTimestamp = apiResponse.data[0]?.timestamp || 0;
        const hasNewData = latestTimestamp > this.lastDataTimestamp;

        if (hasNewData) {
          this.lastDataTimestamp = latestTimestamp;
          this.showNewDataNotification(apiResponse.data[0]);
        }

        this.updateCharts(apiResponse.data);
        this.updateMetrics(apiResponse.data);
        this.updateTable(apiResponse.data);

        if (apiResponse.data.length > 0) {
          this.checkAlerts(apiResponse.data[0]);
        }
      } catch (error) {
        this.showError("Error al cargar los datos de la API");
      }
    }

    showNewDataNotification(newData: Datapoint): void {
      if (!newData) {
        return;
      }

      const notification = document.createElement("div");
      notification.className = "new-data-notification";
      notification.innerHTML = `
        <div class="notification-content">
          <strong>📡 Nuevo dato recibido</strong>
          <p>🌡️ ${newData.temperature.toFixed(1)}°C | 🔧 ${newData.pressure.toFixed(1)} hPa | 💧 ${newData.humidity.toFixed(1)}%</p>
          <small>${this.formatTimestamp(newData.timestamp)}</small>
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
      `;

      if (!document.getElementById("notificationStyles")) {
        const style = document.createElement("style");
        style.id = "notificationStyles";
        style.textContent = `
          @keyframes slideInNotification {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
          .new-data-notification {
            border-left: 5px solid #fff;
          }
        `;
        document.head.appendChild(style);
      }

      document.body.appendChild(notification);

      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 3000);
    }

    checkAlerts(latestData: Datapoint): void {
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
        this.showAlert(alert);
        this.addAlertToLog(alert);
      });

      this.updateAlertCounter();
    }

    showAlert(alert: Alert): void {
      const alertKey = `${alert.type}-${alert.timestamp}`;

      if (this.activeAlerts.has(alertKey)) return;

      this.activeAlerts.add(alertKey);

      const alertDiv = document.createElement("div");
      alertDiv.className = `alert alert-${alert.severity}`;
      alertDiv.innerHTML = `
        <div class="alert-content">
          <strong>⚠️ ALERTA DE SENSOR</strong>
          <p>${alert.message}</p>
          <small>Hora: ${this.formatTimestamp(alert.timestamp)}</small>
          <button class="alert-close" onclick="this.parentElement.parentElement.remove()">✕</button>
        </div>
      `;

      alertDiv.style.cssText = `
        position: fixed;
        top: ${20 + (this.activeAlerts.size - 1) * 120}px;
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

      if (!document.getElementById("alertStyles")) {
        const style = document.createElement("style");
        style.id = "alertStyles";
        style.textContent = `
          @keyframes slideInAlert {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
          .alert-content {
            position: relative;
          }
          .alert-close {
            position: absolute;
            top: -5px;
            right: -5px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 14px;
          }
          .alert-close:hover {
            background: rgba(255,255,255,0.3);
          }
        `;
        document.head.appendChild(style);
      }

      document.body.appendChild(alertDiv);

      const timeout = alert.severity === "critical" ? 10000 : 7000;
      setTimeout(() => {
        if (alertDiv.parentNode) {
          alertDiv.remove();
          this.activeAlerts.delete(alertKey);
          this.updateAlertCounter();
        }
      }, timeout);

      this.playAlertSound(alert.severity);
    }

    addAlertToLog(alert: Alert): void {
      const alertLog = document.getElementById("alertLog");
      if (!alertLog) return;

      const logEntry = document.createElement("div");
      logEntry.className = `alert-log-entry alert-${alert.severity}`;
      logEntry.innerHTML = `
        <div class="log-timestamp">${this.formatTimestamp(alert.timestamp)}</div>
        <div class="log-message">${alert.message}</div>
        <div class="log-value">Valor: ${alert.value.toFixed(1)} | Límite: ${alert.threshold}</div>
      `;

      alertLog.insertBefore(logEntry, alertLog.firstChild);

      while (alertLog.children.length > 20) {
        if (alertLog.lastChild) {
          alertLog.removeChild(alertLog.lastChild);
        }
      }
    }

    playAlertSound(severity: ValueStatus): void {
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

    updateAlertCounter(): void {
      const counter = document.getElementById("alertCounter");
      if (counter) {
        const count = this.activeAlerts.size;
        counter.textContent = count > 0 ? count.toString() : "";
        counter.style.display = count > 0 ? "block" : "none";
      }
    }

    clearAllAlerts(): void {
      document.querySelectorAll(".alert").forEach(alert => alert.remove());
      this.activeAlerts.clear();
      this.updateAlertCounter();
      const alertLog = document.getElementById("alertLog");
      if (alertLog) {
        alertLog.innerHTML = "<p class=\"no-alerts\">No hay alertas registradas</p>";
      }
    }

    updateCharts(data: Datapoint[]): void {
      const sortedData = [...data].sort((a, b) => a.timestamp - b.timestamp);

      const temperatureData = sortedData.map(item => ({
        x: item.timestamp,
        y: item.temperature
      }));

      const pressureData = sortedData.map(item => ({
        x: item.timestamp,
        y: item.pressure
      }));

      const humidityData = sortedData.map(item => ({
        x: item.timestamp,
        y: item.humidity
      }));

      this.temperatureChart.updateSeries([{
        name: "Temperatura (°C)",
        data: temperatureData
      }]);

      this.pressureChart.updateSeries([{
        name: "Presión (hPa)",
        data: pressureData
      }]);

      this.humidityChart.updateSeries([{
        name: "Humedad (%)",
        data: humidityData
      }]);
    }

    updateMetrics(data: Datapoint[]): void {
      if (data.length === 0) {
        this.clearMetrics();
        return;
      }

      const latest = data[0];
      const latestTime = this.formatTimestamp(latest.timestamp);

      const tempStatus = this.getValueStatus(latest.temperature, alertRanges.temperature);
      const pressureStatus = this.getValueStatus(latest.pressure, alertRanges.pressure);
      const humidityStatus = this.getValueStatus(latest.humidity, alertRanges.humidity);

      this.updateElementWithStatus("currentTemp", `${latest.temperature.toFixed(1)}°C`, tempStatus);
      this.updateElement("tempTime", latestTime);

      this.updateElementWithStatus("currentPressure", `${latest.pressure.toFixed(1)} hPa`, pressureStatus);
      this.updateElement("pressureTime", latestTime);

      this.updateElementWithStatus("currentHumidity", `${latest.humidity.toFixed(1)}%`, humidityStatus);
      this.updateElement("humidityTime", latestTime);

      this.updateElement("totalReadings", data.length.toString());
      this.updateElement("lastUpdate", `Actualizado: ${new Date().toLocaleTimeString()}`);
    }

    getValueStatus(value: number, range: AlertRange): ValueStatus {
      if (value < range.min || value > range.max) {
        return value < range.min || value > range.max * 1.1 ? "critical" : "warning";
      }
      return "normal";
    }

    updateElementWithStatus(id: string, content: string, status: ValueStatus): void {
      const element = document.getElementById(id);
      if (element) {
        element.textContent = content;
        element.classList.remove("status-normal", "status-warning", "status-critical");
        element.classList.add(`status-${status}`);
        const indicator = status === "normal" ? "✅" : status === "warning" ? "⚠️" : "🚨";
        element.setAttribute("data-status", indicator);
      }
    }

    updateTable(data: Datapoint[]): void {
      const tbody = document.getElementById("dataTableBody");
      if (!tbody) return;

      if (data.length === 0) {
        tbody.innerHTML = "<tr><td colspan=\"6\" class=\"no-data\">No hay datos disponibles</td></tr>";
        return;
      }

      tbody.innerHTML = data.map(item => {
        const tempStatus = this.getValueStatus(item.temperature, alertRanges.temperature);
        const pressureStatus = this.getValueStatus(item.pressure, alertRanges.pressure);
        const humidityStatus = this.getValueStatus(item.humidity, alertRanges.humidity);

        const hasAlert = tempStatus !== "normal" || pressureStatus !== "normal" || humidityStatus !== "normal";

        return `
          <tr class="${hasAlert ? "row-alert" : ""}">
            <td>${item.id}</td>
            <td class="status-${tempStatus}">${item.temperature.toFixed(1)}°C ${tempStatus !== "normal" ? (tempStatus === "critical" ? "🚨" : "⚠️") : ""}</td>
            <td class="status-${pressureStatus}">${item.pressure.toFixed(1)} hPa ${pressureStatus !== "normal" ? (pressureStatus === "critical" ? "🚨" : "⚠️") : ""}</td>
            <td class="status-${humidityStatus}">${item.humidity.toFixed(1)}% ${humidityStatus !== "normal" ? (humidityStatus === "critical" ? "🚨" : "⚠️") : ""}</td>
            <td>${this.formatTimestamp(item.timestamp)}</td>
            <td>${hasAlert ? "<span class=\"alert-badge\">ALERTA</span>" : "<span class=\"ok-badge\">OK</span>"}</td>
          </tr>
        `;
      }).join("");
    }

    updateElement(id: string, content: string): void {
      const element = document.getElementById(id);
      if (element) {
        element.textContent = content;
      }
    }

    clearMetrics(): void {
      this.updateElement("currentTemp", "--°C");
      this.updateElement("tempTime", "--");
      this.updateElement("currentPressure", "-- hPa");
      this.updateElement("pressureTime", "--");
      this.updateElement("currentHumidity", "--%");
      this.updateElement("humidityTime", "--");
      this.updateElement("totalReadings", "--");
      this.updateElement("lastUpdate", "--");
    }

    formatTimestamp(timestamp: number): string {
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

    toggleAutoRefresh(): void {
      const button = document.getElementById("autoRefreshBtn");

      if (this.isAutoRefreshEnabled) {
        if (this.autoRefreshInterval) {
          clearInterval(this.autoRefreshInterval);
          this.autoRefreshInterval = null;
        }
        this.isAutoRefreshEnabled = false;
        if (button) button.textContent = "⏱️ Auto: OFF";
        button?.classList.remove("primary");
        button?.classList.add("secondary");

        console.log("🔴 Auto-refresh DESACTIVADO");
      } else {
        this.autoRefreshInterval = setInterval(() => {
          this.loadData();
        }, this.refreshIntervalMs);

        this.isAutoRefreshEnabled = true;
        if (button) button.textContent = `⏱️ Auto: ON (${this.refreshIntervalMs / 1000}s)`;
        button?.classList.remove("secondary");
        button?.classList.add("primary");

        console.log(`🟢 Auto-refresh ACTIVADO cada ${this.refreshIntervalMs / 1000} segundos`);
      }
    }

    showError(message: string): void {
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

      setTimeout(() => {
        if (errorDiv.parentNode) {
          document.body.removeChild(errorDiv);
        }
      }, 5000);
    }
  }

  onMount(() => {
    new IoTDashboard();
  });
</script>

<div class="container">
  <header class="header">
    <h1>🏭 IoT Industrial Dashboard</h1>
    <div class="header-controls">
      <div class="status-indicator">
        <span class="status-dot offline" id="connectionStatus"></span>
        <span>API Status</span>
      </div>
      <div class="alert-indicator">
        <span>🚨 Alertas Activas</span>
        <span class="alert-counter" id="alertCounter">0</span>
      </div>
    </div>
  </header>

  <div class="dashboard">
    <div class="metrics-cards">
      <div class="metric-card temperature">
        <div class="metric-icon">🌡️</div>
        <div class="metric-content">
          <h3>Temperatura</h3>
          <span class="metric-value" id="currentTemp">--°C</span>
          <small class="metric-time" id="tempTime">--</small>
          <small class="metric-range">Rango: 10°C - 40°C</small>
        </div>
      </div>

      <div class="metric-card pressure">
        <div class="metric-icon">🔧</div>
        <div class="metric-content">
          <h3>Presión</h3>
          <span class="metric-value" id="currentPressure">-- hPa</span>
          <small class="metric-time" id="pressureTime">--</small>
          <small class="metric-range">Rango: 990 - 1040 hPa</small>
        </div>
      </div>

      <div class="metric-card humidity">
        <div class="metric-icon">💧</div>
        <div class="metric-content">
          <h3>Humedad</h3>
          <span class="metric-value" id="currentHumidity">--%</span>
          <small class="metric-time" id="humidityTime">--</small>
          <small class="metric-range">Rango: 20% - 90%</small>
        </div>
      </div>

      <div class="metric-card total">
        <div class="metric-icon">📊</div>
        <div class="metric-content">
          <h3>Total Lecturas</h3>
          <span class="metric-value" id="totalReadings">--</span>
          <small class="metric-time" id="lastUpdate">--</small>
        </div>
      </div>
    </div>

    <div class="controls">
      <button class="btn primary" id="refreshBtn">🔄 Actualizar</button>
      <button class="btn secondary" id="autoRefreshBtn">⏱️ Auto: OFF</button>
      <button class="btn warning" id="clearAlertsBtn">🗑️ Limpiar Alertas</button>
      <select class="select" id="timeRange">
        <option value="10">Últimos 10 datos</option>
        <option selected value="20">Últimos 20 datos</option>
        <option value="50">Últimos 50 datos</option>
      </select>
    </div>

    <div class="charts-grid">
      <div class="chart-container">
        <h3>📈 Temperatura en Tiempo Real</h3>
        <div id="temperatureChart"></div>
      </div>

      <div class="chart-container">
        <h3>📊 Presión en Tiempo Real</h3>
        <div id="pressureChart"></div>
      </div>

      <div class="chart-container full-width">
        <h3>💧 Humedad en Tiempo Real</h3>
        <div id="humidityChart"></div>
      </div>
    </div>

    <div class="alert-panel">
      <h3>🚨 Registro de Alertas</h3>
      <div class="alert-log" id="alertLog">
        <p class="no-alerts">No hay alertas registradas</p>
      </div>
    </div>

    <div class="data-table-container">
      <h3>📋 Datos Recientes</h3>
      <div class="table-wrapper">
        <table class="data-table" id="dataTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Temperatura (°C)</th>
              <th>Presión (hPa)</th>
              <th>Humedad (%)</th>
              <th>Timestamp</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody id="dataTableBody">
            <tr>
              <td class="no-data" colspan="6">Cargando datos...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<style>
  .container {
    margin: 0 auto;
    max-width: 1400px;
    padding: 20px;
  }

  .header-controls {
    align-items: center;
    display: flex;
    gap: 20px;
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

  .metric-range {
    color: #888888;
    display: block;
    font-size: 0.7rem;
    margin-top: 4px;
  }

  .status-normal {
    color: #27ae60;
  }

  .status-warning {
    color: #f39c12;
    font-weight: 700;
  }

  .status-critical {
    animation: blink 1s infinite;
    color: #e74c3c;
    font-weight: 700;
  }

  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0.5;
    }
  }

  .alert-panel {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 25px;
  }

  .alert-log {
    background: #f8f9fa;
    border: 1px solid #dddddd;
    border-radius: 8px;
    max-height: 300px;
    overflow-y: auto;
    padding: 15px;
  }

  .alert-log-entry {
    border-left: 4px solid;
    border-radius: 6px;
    margin-bottom: 10px;
    padding: 10px;
  }

  .alert-log-entry.alert-warning {
    background: #fff3cd;
    border-left-color: #f39c12;
  }

  .alert-log-entry.alert-critical {
    background: #f8d7da;
    border-left-color: #e74c3c;
  }

  .log-timestamp {
    color: #666666;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .log-message {
    font-weight: 600;
    margin: 5px 0;
  }

  .log-value {
    color: #555555;
    font-size: 0.8rem;
  }

  .no-alerts {
    color: #666666;
    font-style: italic;
    margin: 20px 0;
    text-align: center;
  }

  .row-alert {
    background-color: #fff5f5 !important;
    border-left: 4px solid #e74c3c;
  }

  .alert-badge {
    background: #e74c3c;
    border-radius: 4px;
    color: white;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 6px;
  }

  .ok-badge {
    background: #27ae60;
    border-radius: 4px;
    color: white;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 6px;
  }

  .btn.warning {
    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    color: white;
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

  .metric-card {
    align-items: center;
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    display: flex;
    gap: 20px;
    padding: 25px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }

  .metric-card:hover {
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
    transform: translateY(-5px);
  }

  .metric-icon {
    align-items: center;
    border-radius: 12px;
    display: flex;
    font-size: 2.5rem;
    height: 60px;
    justify-content: center;
    width: 60px;
  }

  .temperature .metric-icon {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  }

  .pressure .metric-icon {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  }

  .humidity .metric-icon {
    background: linear-gradient(135deg, #abdcff 0%, #0396ff 100%);
  }

  .total .metric-icon {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  }

  .metric-content h3 {
    color: #666666;
    font-size: 1rem;
    margin-bottom: 8px;
  }

  .metric-value {
    color: #2c3e50;
    display: block;
    font-size: 1.8rem;
    font-weight: 700;
  }

  .metric-time {
    color: #888888;
    font-size: 0.8rem;
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

  .chart-container {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 25px;
  }

  .chart-container.full-width {
    grid-column: 1 / -1;
  }

  .chart-container h3 {
    color: #2c3e50;
    font-size: 1.2rem;
    margin-bottom: 20px;
  }

  .data-table-container {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 25px;
  }

  .data-table-container h3 {
    color: #2c3e50;
    font-size: 1.2rem;
    margin-bottom: 20px;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  .data-table {
    background: white;
    border-collapse: collapse;
    border-radius: 8px;
    overflow: hidden;
    width: 100%;
  }

  .data-table th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 15px;
    text-align: left;
  }

  .data-table td {
    border-bottom: 1px solid #eeeeee;
    padding: 12px 15px;
  }

  .data-table tbody tr:hover {
    background: #f8f9fa;
  }

  .no-data {
    color: #666666;
    font-style: italic;
    text-align: center;
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

    .metric-card {
      padding: 20px;
    }
  }
</style>
