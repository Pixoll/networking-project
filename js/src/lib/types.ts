export type AlertRange = {
  min: number;
  max: number;
};

export type ValueStatus = "critical" | "warning" | "normal";
export type AlertType = "temperature" | "pressure" | "humidity";

export type Alert = {
  type: AlertType;
  severity: ValueStatus;
  message: string;
  value: number;
  threshold: number;
  timestamp: number;
};

export type Measurement = {
  id: number;
  sensor_id: number;
  temperature: number;
  pressure: number;
  humidity: number;
  timestamp: number;
};
