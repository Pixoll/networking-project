import type { ApexOptions } from "apexcharts";
import type { AlertRange, AlertType } from "./types";

export const API_BASE_URL = "http://localhost:5000/api";
export const SOCKET_BASE_URL = "ws://localhost:5000/ws";

export const alertRanges: Record<AlertType, AlertRange> = {
  temperature: { min: 10, max: 40 },
  pressure: { min: 990, max: 1040 },
  humidity: { min: 20, max: 90 },
};

const commonOptions: ApexOptions = {
  chart: {
    type: "line",
    height: 300,
    animations: {
      enabled: true,
      speed: 800,
    },
    toolbar: {
      show: false,
    },
    zoom: {
      enabled: false,
    },
  },
  stroke: {
    curve: "smooth",
    width: 3,
  },
  markers: {
    size: 6,
    strokeWidth: 2,
    fillOpacity: 1,
    strokeOpacity: 1,
  },
  grid: {
    borderColor: "#e7e7e7",
    row: {
      colors: ["#f3f3f3", "transparent"],
      opacity: 0.5,
    },
  },
  xaxis: {
    type: "datetime",
    labels: {
      format: "HH:mm:ss",
    },
  },
  tooltip: {
    x: {
      format: "dd/MM/yy HH:mm:ss",
    },
  },
  annotations: {
    yaxis: [],
  },
};

export const temperatureOptions: ApexOptions = {
  ...commonOptions,
  series: [{
    name: "Temperatura (°C)",
    data: [],
  }],
  colors: ["#ff6b6b"],
  yaxis: {
    title: {
      text: "Temperatura (°C)",
    },
    labels: {
      formatter: (value: number) => `${value.toFixed(1)}°C`,
    },
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
          style: { color: "#e74c3c", background: "#ffffff" },
        },
      },
      {
        y: alertRanges.temperature.min,
        borderColor: "#3498db",
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: `Mín: ${alertRanges.temperature.min}°C`,
          style: { color: "#3498db", background: "#ffffff" },
        },
      },
    ],
  },
};

export const pressureOptions: ApexOptions = {
  ...commonOptions,
  series: [{
    name: "Presión (hPa)",
    data: [],
  }],
  colors: ["#4ecdc4"],
  yaxis: {
    title: {
      text: "Presión (hPa)",
    },
    labels: {
      formatter: (value: number) => `${value.toFixed(1)} hPa`,
    },
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
          style: { color: "#e74c3c", background: "#ffffff" },
        },
      },
      {
        y: alertRanges.pressure.min,
        borderColor: "#3498db",
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: `Mín: ${alertRanges.pressure.min} hPa`,
          style: { color: "#3498db", background: "#ffffff" },
        },
      },
    ],
  },
};

export const humidityOptions: ApexOptions = {
  ...commonOptions,
  series: [{
    name: "Humedad (%)",
    data: [],
  }],
  colors: ["#45b7d1"],
  yaxis: {
    title: {
      text: "Humedad (%)",
    },
    labels: {
      formatter: (value: number) => `${value.toFixed(1)}%`,
    },
    min: 0,
    max: 100,
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
          style: { color: "#e74c3c", background: "#ffffff" },
        },
      },
      {
        y: alertRanges.humidity.min,
        borderColor: "#3498db",
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: `Mín: ${alertRanges.humidity.min}%`,
          style: { color: "#3498db", background: "#ffffff" },
        },
      },
    ],
  },
};
