<script lang="ts">
  import type { ValueStatus } from "$lib/types";

  export let title: string;
  export let icon: string;
  export let value: string;
  export let time: string;
  export let range: string;
  export let status: ValueStatus = "normal";
  export let bgClass: string;
</script>

<div class="metric-card {bgClass}">
  <div class="metric-icon">
    {icon}
  </div>
  <div class="metric-content">
    <h3>{title}</h3>
    <span
      class="metric-value status-{status}"
      data-status={status === "normal" ? "✅" : status === "warning" ? "⚠️" : "🚨"}
    >
      {value}
    </span>
    <small class="metric-time">{time}</small>
    <small class="metric-range">{range}</small>
  </div>
</div>

<style>
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
</style>
