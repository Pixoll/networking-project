import { API_BASE_URL } from "./config";
import type { Measurement } from "./types";

type ApiResponse<T> = {
  response: Response;
} & ({
  ok: true;
  data: T;
} | {
  ok: false;
  error: string;
});

export async function checkApiStatus(): Promise<ApiResponse<undefined>> {
  const response = await fetch(`${API_BASE_URL}/api/ping`);
  return await wrapResponse(response);
}

export async function getSensorData(limit: number): Promise<ApiResponse<Measurement[]>> {
  const response = await fetch(`${API_BASE_URL}/api/measurements?limit=${limit}`);
  return await wrapResponse(response);
}

async function wrapResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (response.ok) {
    return {
      ok: true,
      data: await response.json().catch(() => undefined),
      response,
    };
  }

  return {
    ok: false,
    error: await response.json().then(e => e.error).catch(() => undefined),
    response,
  }
}
