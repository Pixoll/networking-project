import { API_BASE_URL } from "./config";
import type { Datapoint } from "./types";

type ApiResponse<T> = {
  response: Response;
} & ({
  ok: true;
  data: T;
} | {
  ok: false;
  error: string;
});

export async function checkApiStatus(): Promise<ApiResponse<{
  status: "ok";
}>> {
  const response = await fetch(`${API_BASE_URL}/api/ping`);
  return await wrapResponse(response);
}

export async function getSensorData(limit: number): Promise<ApiResponse<{
  count: number;
  data: Datapoint[];
}>> {
  const response = await fetch(`${API_BASE_URL}/api/sensors/data?limit=${limit}`);
  return await wrapResponse(response);
}

async function wrapResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (response.ok) {
    return {
      ok: true,
      data: await response.json(),
      response,
    };
  }

  return {
    ok: false,
    error: await response.json().then(e => e.error),
    response,
  }
}
