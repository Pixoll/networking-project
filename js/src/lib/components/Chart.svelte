<script lang="ts">
  import type { Datapoint } from "$lib/types";
  import type { ApexOptions } from "apexcharts";
  import ApexCharts from "apexcharts";
  import { onMount } from "svelte";

  type Props = {
    title: string;
    chartId: string;
    options: ApexOptions;
    data?: Datapoint[];
    dataKey: keyof Pick<Datapoint, "temperature" | "pressure" | "humidity">;
    fullWidth?: boolean;
  }

  let { title, chartId, options, data = [], dataKey, fullWidth = false }: Props = $props();

  let chart: ApexCharts;
  let chartElement: HTMLElement;

  onMount(() => {
    chart = new ApexCharts(chartElement, options);
    chart.render();

    return () => {
      if (chart) {
        chart.destroy();
      }
    };
  });

  $effect(() => {
    if (chart && data) {
      updateChart(data);
    }
  });

  function updateChart(newData: Datapoint[]) {
    const sortedData = [...newData].sort((a, b) => a.timestamp - b.timestamp);
    const chartData = sortedData.map(item => ({
      x: item.timestamp,
      y: item[dataKey]
    }));

    chart.updateSeries([{
      name: title,
      data: chartData
    }]);
  }
</script>

<div class="chart-container" class:full-width={fullWidth}>
  <h3>{title}</h3>
  <div bind:this={chartElement} id={chartId}></div>
</div>

<style>
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
</style>
