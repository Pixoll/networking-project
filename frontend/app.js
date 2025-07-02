class IoTDashboard {
    constructor() {
        this.temperatureChart = null;
        this.pressureChart = null;
        this.humidityChart = null;
        this.autoRefreshInterval = null;
        this.isAutoRefreshEnabled = false;
        this.currentLimit = 20;
        this.API_BASE_URL = 'http://localhost:5000';
        this.lastDataTimestamp = 0;
        this.refreshIntervalMs = 2000;

        this.alertRanges = {
            temperature: { min: 10, max: 40 },
            pressure: { min: 990, max: 1040 },
            humidity: { min: 20, max: 90 }
        };

        this.activeAlerts = new Set();

        this.initializeCharts();
        this.setupEventListeners();
        this.loadInitialData();
    }

    initializeCharts() {
        const commonOptions = {
            chart: {
                type: 'line',
                height: 300,
                animations: {
                    enabled: true,
                    easing: 'easeinout',
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
                curve: 'smooth',
                width: 3
            },
            markers: {
                size: 6,
                strokeWidth: 2,
                fillOpacity: 1,
                strokeOpacity: 1
            },
            grid: {
                borderColor: '#e7e7e7',
                row: {
                    colors: ['#f3f3f3', 'transparent'],
                    opacity: 0.5
                }
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    format: 'HH:mm:ss'
                }
            },
            tooltip: {
                x: {
                    format: 'dd/MM/yy HH:mm:ss'
                }
            },
            annotations: {
                yaxis: []
            }
        };

        const temperatureOptions = {
            ...commonOptions,
            series: [{
                name: 'Temperatura (°C)',
                data: []
            }],
            colors: ['#ff6b6b'],
            yaxis: {
                title: {
                    text: 'Temperatura (°C)'
                },
                labels: {
                    formatter: (value) => `${value.toFixed(1)}°C`
                }
            },
            annotations: {
                yaxis: [
                    {
                        y: this.alertRanges.temperature.max,
                        borderColor: '#e74c3c',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Máx: ${this.alertRanges.temperature.max}°C`,
                            style: { color: '#e74c3c', background: '#fff' }
                        }
                    },
                    {
                        y: this.alertRanges.temperature.min,
                        borderColor: '#3498db',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Mín: ${this.alertRanges.temperature.min}°C`,
                            style: { color: '#3498db', background: '#fff' }
                        }
                    }
                ]
            }
        };

        const pressureOptions = {
            ...commonOptions,
            series: [{
                name: 'Presión (hPa)',
                data: []
            }],
            colors: ['#4ecdc4'],
            yaxis: {
                title: {
                    text: 'Presión (hPa)'
                },
                labels: {
                    formatter: (value) => `${value.toFixed(1)} hPa`
                }
            },
            annotations: {
                yaxis: [
                    {
                        y: this.alertRanges.pressure.max,
                        borderColor: '#e74c3c',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Máx: ${this.alertRanges.pressure.max} hPa`,
                            style: { color: '#e74c3c', background: '#fff' }
                        }
                    },
                    {
                        y: this.alertRanges.pressure.min,
                        borderColor: '#3498db',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Mín: ${this.alertRanges.pressure.min} hPa`,
                            style: { color: '#3498db', background: '#fff' }
                        }
                    }
                ]
            }
        };

        const humidityOptions = {
            ...commonOptions,
            series: [{
                name: 'Humedad (%)',
                data: []
            }],
            colors: ['#45b7d1'],
            yaxis: {
                title: {
                    text: 'Humedad (%)'
                },
                labels: {
                    formatter: (value) => `${value.toFixed(1)}%`
                },
                min: 0,
                max: 100
            },
            annotations: {
                yaxis: [
                    {
                        y: this.alertRanges.humidity.max,
                        borderColor: '#e74c3c',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Máx: ${this.alertRanges.humidity.max}%`,
                            style: { color: '#e74c3c', background: '#fff' }
                        }
                    },
                    {
                        y: this.alertRanges.humidity.min,
                        borderColor: '#3498db',
                        borderWidth: 2,
                        strokeDashArray: 5,
                        label: {
                            text: `Mín: ${this.alertRanges.humidity.min}%`,
                            style: { color: '#3498db', background: '#fff' }
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
    }

    setupEventListeners() {
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadData();
        });

        document.getElementById('autoRefreshBtn')?.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });

        document.getElementById('timeRange')?.addEventListener('change', (e) => {
            this.currentLimit = parseInt(e.target.value);
            this.loadData();
        });

        document.getElementById('clearAlertsBtn')?.addEventListener('click', () => {
            this.clearAllAlerts();
        });

        document.getElementById('refreshRate')?.addEventListener('change', (e) => {
            this.refreshIntervalMs = parseInt(e.target.value);
            if (this.isAutoRefreshEnabled) {
                this.toggleAutoRefresh();
                this.toggleAutoRefresh();
            }
        });
    }

    async loadInitialData() {
        await this.checkApiStatus();
        await this.loadData();
    }

    async checkApiStatus() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/ping`);
            const statusElement = document.getElementById('connectionStatus');

            if (response.ok) {
                statusElement?.classList.remove('offline');
                statusElement?.classList.add('online');
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            console.error(error);
            const statusElement = document.getElementById('connectionStatus');
            statusElement?.classList.remove('online');
            statusElement?.classList.add('offline');
        }
    }

    async loadData() {
        try {
            await this.checkApiStatus();

            const response = await fetch(`${this.API_BASE_URL}/api/sensors/data?limit=${this.currentLimit}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const apiResponse = await response.json();

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
            this.showError('Error al cargar los datos de la API');
        }
    }

    showNewDataNotification(newData) {
        if (!newData) return;

        const notification = document.createElement('div');
        notification.className = 'new-data-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <strong>📡 Nuevo dato recibido</strong>
                <p>🌡️ ${newData.temperature.toFixed(1)}°C | 🔧 ${newData.pression.toFixed(1)} hPa | 💧 ${newData.humidity.toFixed(1)}%</p>
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

        if (!document.getElementById('notificationStyles')) {
            const style = document.createElement('style');
            style.id = 'notificationStyles';
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
    checkAlerts(latestData) {
        const { temperature, pression, humidity, timestamp } = latestData;
        const alerts = [];

        if (temperature < this.alertRanges.temperature.min) {
            alerts.push({
                type: 'temperature',
                severity: 'warning',
                message: `🥶 Temperatura muy baja: ${temperature.toFixed(1)}°C (Mín: ${this.alertRanges.temperature.min}°C)`,
                value: temperature,
                threshold: this.alertRanges.temperature.min,
                timestamp
            });
        } else if (temperature > this.alertRanges.temperature.max) {
            alerts.push({
                type: 'temperature',
                severity: 'critical',
                message: `🔥 Temperatura muy alta: ${temperature.toFixed(1)}°C (Máx: ${this.alertRanges.temperature.max}°C)`,
                value: temperature,
                threshold: this.alertRanges.temperature.max,
                timestamp
            });
        }
        if (pression < this.alertRanges.pressure.min) {
            alerts.push({
                type: 'pressure',
                severity: 'warning',
                message: `📉 Presión muy baja: ${pression.toFixed(1)} hPa (Mín: ${this.alertRanges.pressure.min} hPa)`,
                value: pression,
                threshold: this.alertRanges.pressure.min,
                timestamp
            });
        } else if (pression > this.alertRanges.pressure.max) {
            alerts.push({
                type: 'pressure',
                severity: 'critical',
                message: `📈 Presión muy alta: ${pression.toFixed(1)} hPa (Máx: ${this.alertRanges.pressure.max} hPa)`,
                value: pression,
                threshold: this.alertRanges.pressure.max,
                timestamp
            });
        }
        if (humidity < this.alertRanges.humidity.min) {
            alerts.push({
                type: 'humidity',
                severity: 'warning',
                message: `🏜️ Humedad muy baja: ${humidity.toFixed(1)}% (Mín: ${this.alertRanges.humidity.min}%)`,
                value: humidity,
                threshold: this.alertRanges.humidity.min,
                timestamp
            });
        } else if (humidity > this.alertRanges.humidity.max) {
            alerts.push({
                type: 'humidity',
                severity: 'warning',
                message: `💧 Humedad muy alta: ${humidity.toFixed(1)}% (Máx: ${this.alertRanges.humidity.max}%)`,
                value: humidity,
                threshold: this.alertRanges.humidity.max,
                timestamp
            });
        }
        alerts.forEach(alert => {
            this.showAlert(alert);
            this.addAlertToLog(alert);
        });

        this.updateAlertCounter();
    }

    showAlert(alert) {
        const alertKey = `${alert.type}-${alert.timestamp}`;

        if (this.activeAlerts.has(alertKey)) return;

        this.activeAlerts.add(alertKey);

        const alertDiv = document.createElement('div');
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
            background: ${alert.severity === 'critical' ? '#e74c3c' : '#f39c12'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 1000;
            font-weight: 600;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-left: 5px solid ${alert.severity === 'critical' ? '#c0392b' : '#e67e22'};
            animation: slideInAlert 0.5s ease-out;
        `;

        if (!document.getElementById('alertStyles')) {
            const style = document.createElement('style');
            style.id = 'alertStyles';
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

        const timeout = alert.severity === 'critical' ? 10000 : 7000;
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
                this.activeAlerts.delete(alertKey);
                this.updateAlertCounter();
            }
        }, timeout);

        this.playAlertSound(alert.severity);

    }

    addAlertToLog(alert) {
        const alertLog = document.getElementById('alertLog');
        if (!alertLog) return;

        const logEntry = document.createElement('div');
        logEntry.className = `alert-log-entry alert-${alert.severity}`;
        logEntry.innerHTML = `
            <div class="log-timestamp">${this.formatTimestamp(alert.timestamp)}</div>
            <div class="log-message">${alert.message}</div>
            <div class="log-value">Valor: ${alert.value.toFixed(1)} | Límite: ${alert.threshold}</div>
        `;

        alertLog.insertBefore(logEntry, alertLog.firstChild);

        while (alertLog.children.length > 20) {
            alertLog.removeChild(alertLog.lastChild);
        }
    }

    playAlertSound(severity) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = severity === 'critical' ? 800 : 600;
            oscillator.type = 'square';

            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('No se pudo reproducir sonido de alerta:', error);
        }
    }

    updateAlertCounter() {
        const counter = document.getElementById('alertCounter');
        if (counter) {
            const count = this.activeAlerts.size;
            counter.textContent = count > 0 ? count : '';
            counter.style.display = count > 0 ? 'block' : 'none';
        }
    }
    clearAllAlerts() {
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
        this.activeAlerts.clear();
        this.updateAlertCounter();
        const alertLog = document.getElementById('alertLog');
        if (alertLog) {
            alertLog.innerHTML = '<p class="no-alerts">No hay alertas registradas</p>';
        }
    }

    updateCharts(data) {
        const sortedData = [...data].sort((a, b) => a.timestamp - b.timestamp);

        const temperatureData = sortedData.map(item => ({
            x: item.timestamp * 1000,
            y: item.temperature
        }));

        const pressureData = sortedData.map(item => ({
            x: item.timestamp * 1000,
            y: item.pression
        }));

        const humidityData = sortedData.map(item => ({
            x: item.timestamp * 1000,
            y: item.humidity
        }));

        this.temperatureChart?.updateSeries([{
            name: 'Temperatura (°C)',
            data: temperatureData
        }]);

        this.pressureChart?.updateSeries([{
            name: 'Presión (hPa)',
            data: pressureData
        }]);

        this.humidityChart?.updateSeries([{
            name: 'Humedad (%)',
            data: humidityData
        }]);
    }

    updateMetrics(data) {
        if (data.length === 0) {
            this.clearMetrics();
            return;
        }

        const latest = data[0];
        const latestTime = this.formatTimestamp(latest.timestamp);

        const tempStatus = this.getValueStatus(latest.temperature, this.alertRanges.temperature);
        const pressureStatus = this.getValueStatus(latest.pression, this.alertRanges.pressure);
        const humidityStatus = this.getValueStatus(latest.humidity, this.alertRanges.humidity);

        this.updateElementWithStatus('currentTemp', `${latest.temperature.toFixed(1)}°C`, tempStatus);
        this.updateElement('tempTime', latestTime);

        this.updateElementWithStatus('currentPressure', `${latest.pression.toFixed(1)} hPa`, pressureStatus);
        this.updateElement('pressureTime', latestTime);

        this.updateElementWithStatus('currentHumidity', `${latest.humidity.toFixed(1)}%`, humidityStatus);
        this.updateElement('humidityTime', latestTime);

        this.updateElement('totalReadings', data.length.toString());
        this.updateElement('lastUpdate', `Actualizado: ${new Date().toLocaleTimeString()}`);
    }

    getValueStatus(value, range) {
        if (value < range.min || value > range.max) {
            return value < range.min || value > range.max * 1.1 ? 'critical' : 'warning';
        }
        return 'normal';
    }

    updateElementWithStatus(id, content, status) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
            element.classList.remove('status-normal', 'status-warning', 'status-critical');
            element.classList.add(`status-${status}`);
            const indicator = status === 'normal' ? '✅' : status === 'warning' ? '⚠️' : '🚨';
            element.setAttribute('data-status', indicator);
        }
    }

    updateTable(data) {
        const tbody = document.getElementById('dataTableBody');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No hay datos disponibles</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(item => {
            const tempStatus = this.getValueStatus(item.temperature, this.alertRanges.temperature);
            const pressureStatus = this.getValueStatus(item.pression, this.alertRanges.pressure);
            const humidityStatus = this.getValueStatus(item.humidity, this.alertRanges.humidity);

            const hasAlert = tempStatus !== 'normal' || pressureStatus !== 'normal' || humidityStatus !== 'normal';

            return `
                <tr class="${hasAlert ? 'row-alert' : ''}">
                    <td>${item.id}</td>
                    <td class="status-${tempStatus}">${item.temperature.toFixed(1)}°C ${tempStatus !== 'normal' ? (tempStatus === 'critical' ? '🚨' : '⚠️') : ''}</td>
                    <td class="status-${pressureStatus}">${item.pression.toFixed(1)} hPa ${pressureStatus !== 'normal' ? (pressureStatus === 'critical' ? '🚨' : '⚠️') : ''}</td>
                    <td class="status-${humidityStatus}">${item.humidity.toFixed(1)}% ${humidityStatus !== 'normal' ? (humidityStatus === 'critical' ? '🚨' : '⚠️') : ''}</td>
                    <td>${this.formatTimestamp(item.timestamp)}</td>
                    <td>${hasAlert ? '<span class="alert-badge">ALERTA</span>' : '<span class="ok-badge">OK</span>'}</td>
                </tr>
            `;
        }).join('');
    }

    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }

    clearMetrics() {
        this.updateElement('currentTemp', '--°C');
        this.updateElement('tempTime', '--');
        this.updateElement('currentPressure', '-- hPa');
        this.updateElement('pressureTime', '--');
        this.updateElement('currentHumidity', '--%');
        this.updateElement('humidityTime', '--');
        this.updateElement('totalReadings', '--');
        this.updateElement('lastUpdate', '--');
    }

    formatTimestamp(timestamp) {
        return new Date(timestamp * 1000).toLocaleString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    toggleAutoRefresh() {
        const button = document.getElementById('autoRefreshBtn');

        if (this.isAutoRefreshEnabled) {
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
            this.isAutoRefreshEnabled = false;
            if (button) button.textContent = '⏱️ Auto: OFF';
            button?.classList.remove('primary');
            button?.classList.add('secondary');

            console.log('🔴 Auto-refresh DESACTIVADO');
        } else {
            this.autoRefreshInterval = setInterval(() => {
                this.loadData();
            }, this.refreshIntervalMs);

            this.isAutoRefreshEnabled = true;
            if (button) button.textContent = `⏱️ Auto: ON (${this.refreshIntervalMs/1000}s)`;
            button?.classList.remove('secondary');
            button?.classList.add('primary');

            console.log(`🟢 Auto-refresh ACTIVADO cada ${this.refreshIntervalMs/1000} segundos`);
        }
    }


    showError(message) {
        const errorDiv = document.createElement('div');
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

document.addEventListener('DOMContentLoaded', () => {
    new IoTDashboard();
});
