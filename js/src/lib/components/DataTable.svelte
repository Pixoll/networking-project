<script lang="ts">
  import { alertRanges } from "$lib/config";
  import type { AlertRange, Measurement, ValueStatus } from "$lib/types";

  type Props = {
    data?: Measurement[];
  }

  let { data = [] }: Props = $props();

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

  function getValueStatus(value: number, range: AlertRange): ValueStatus {
    if (value < range.min || value > range.max) {
      return value < range.min || value > range.max * 1.1 ? "critical" : "warning";
    }
    return "normal";
  }
</script>

<div class="data-table-container">
  <h3>📋 Datos Recientes</h3>
  <div class="table-wrapper">
    <table class="data-table">
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
      <tbody>
        {#if data.length === 0}
          <tr>
            <td class="no-data" colspan="6">No hay datos disponibles</td>
          </tr>
        {:else}
          {#each data as item (`${item.id}-${item.timestamp}`)}
            {@const tempStatus = getValueStatus(item.temperature, alertRanges.temperature)}
            {@const pressureStatus = getValueStatus(item.pressure, alertRanges.pressure)}
            {@const humidityStatus = getValueStatus(item.humidity, alertRanges.humidity)}
            {@const hasAlert = tempStatus !== "normal" || pressureStatus !== "normal" || humidityStatus !== "normal"}
            <tr class:row-alert={hasAlert}>
              <td>{item.id}</td>
              <td class="status-{tempStatus}">
                {item.temperature.toFixed(1)}°C
                {#if tempStatus !== "normal"}
                  {tempStatus === "critical" ? "🚨" : "⚠️"}
                {/if}
              </td>
              <td class="status-{pressureStatus}">
                {item.pressure.toFixed(1)} hPa
                {#if pressureStatus !== "normal"}
                  {pressureStatus === "critical" ? "🚨" : "⚠️"}
                {/if}
              </td>
              <td class="status-{humidityStatus}">
                {item.humidity.toFixed(1)}%
                {#if humidityStatus !== "normal"}
                  {humidityStatus === "critical" ? "🚨" : "⚠️"}
                {/if}
              </td>
              <td>{formatTimestamp(item.timestamp)}</td>
              <td>
                {#if hasAlert}
                  <span class="alert-badge">ALERTA</span>
                {:else}
                  <span class="ok-badge">OK</span>
                {/if}
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

<style>
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

  /*noinspection CssUnusedSymbol*/
  .status-normal {
    color: #27ae60;
  }

  /*noinspection CssUnusedSymbol*/
  .status-warning {
    color: #f39c12;
    font-weight: 700;
  }

  /*noinspection CssUnusedSymbol*/
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
</style>
