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
  const response = await fetch(`${API_BASE_URL}/ping`);
  return await wrapResponse(response);
}

export async function getSensorData(limit: number): Promise<ApiResponse<Measurement[]>> {
  const response = await fetch(`${API_BASE_URL}/measurements?limit=${limit}`);
  return await wrapResponse(response, true);
}

async function wrapResponse<T>(response: Response, logError = false): Promise<ApiResponse<T>> {
  if (response.ok) {
    return {
      ok: true,
      data: await response.json().catch(error => logError && console.error(error)),
      response,
    };
  }

  return {
    ok: false,
    error: await response.json().then(e => e.error).catch(error => logError && console.error(error)),
    response,
  }
}
