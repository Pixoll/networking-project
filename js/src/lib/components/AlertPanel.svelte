<script lang="ts">
  import type { Alert } from "$lib/types";

  type Props = {
    alerts: Alert[];
  }

  let { alerts }: Props = $props();

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
</script>

<div class="alert-panel">
  <h3>🚨 Registro de Alertas</h3>
  <div class="alert-log">
    {#if alerts.length === 0}
      <p class="no-alerts">No hay alertas registradas</p>
    {:else}
      {#each alerts as alert (alert.timestamp + alert.type)}
        <div class="alert-log-entry alert-{alert.severity}">
          <div class="log-timestamp">{formatTimestamp(alert.timestamp)}</div>
          <div class="log-message">{alert.message}</div>
          <div class="log-value">Valor: {alert.value.toFixed(1)} | Límite: {alert.threshold}</div>
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
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
</style>
