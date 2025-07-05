import { SOCKET_BASE_URL } from "./config";

type WSMethods<T> = {
  onOpen: () => Promise<void> | void;
  onData: (data: T) => Promise<void> | void;
  onError?: () => Promise<void> | void;
  onClose: (event: CloseEvent) => Promise<void> | void;
};

export function openWS<T>(path: string, { onOpen, onData, onError, onClose }: WSMethods<T>): WebSocket {
  const socket = new WebSocket(`${SOCKET_BASE_URL}/${path}`);

  socket.onopen = () => {
    console.log("🟢 WebSocket is connected");
    onOpen();
  };

  socket.onmessage = (event: MessageEvent) => {
    const data = JSON.parse(event.data);
    console.log("📥 WebSocket message", data);
    onData(data);
  };

  socket.onerror = (event) => {
    console.error("WebSocket error:", event);
    onError?.();
  };

  socket.onclose = (event) => {
    console.log("WebSocket closed:", event);
    onClose(event);
  };

  return socket;
}

export function closeWS(ws: WebSocket): void {
  if (ws.readyState === WebSocket.OPEN) {
    console.log("Closing WebSocket...");
    ws.close();
  }
}
