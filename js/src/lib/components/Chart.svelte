<script lang="ts">
  import type { Measurement } from "$lib/types";
  import { generateHexColors } from "$lib/utils/randomColors";
  import type { ApexOptions } from "apexcharts";
  import ApexCharts from "apexcharts";
  import { onMount } from "svelte";

  type Props = {
    title: string;
    chartId: string;
    options: ApexOptions;
    data: Measurement[];
    dataKey: keyof Pick<Measurement, "temperature" | "pressure" | "humidity">;
    fullWidth?: boolean;
  }

  let { title, chartId, options, data, dataKey, fullWidth = false }: Props = $props();

  let chart: ApexCharts;
  let chartElement: HTMLElement;
  let sensorColorMap = new Map<number, string>();

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
    updateChart(data);
  });

  function groupDataBySensor(measurements: Measurement[]): Map<number, { x: number; y: number }[]> {
    const grouped = new Map<number, { x: number; y: number }[]>();

    measurements.forEach(measurement => {
      if (!grouped.has(measurement.sensor_id)) {
        grouped.set(measurement.sensor_id, []);
      }

      grouped.get(measurement.sensor_id)!.push({
        x: measurement.timestamp,
        y: measurement[dataKey] as number
      });
    });

    return grouped;
  }

  function updateChart(newData: Measurement[]) {
    const sortedData = [...newData].sort((a, b) => a.timestamp - b.timestamp);
    const groupedData = groupDataBySensor(sortedData);
    const sensorIds = Array.from(groupedData.keys()).sort();

    const newSensors = sensorIds.filter(id => !sensorColorMap.has(id));
    if (newSensors.length > 0) {
      const newColors = generateHexColors(newSensors.length);
      newSensors.forEach((sensorId, index) => {
        sensorColorMap.set(sensorId, newColors[index]);
      });
    }

    const series = sensorIds.map(sensorId => ({
      name: `Sensor ${sensorId}`,
      data: groupedData.get(sensorId)!.sort((a, b) => a.x - b.x),
      color: sensorColorMap.get(sensorId)!
    }));

    chart.updateSeries(series);
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
