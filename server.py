from opcua import Server, ua
import time, struct

server = Server()
server.set_endpoint("opc.tcp://localhost:4840")
server.set_server_name("ServidorPythonOpcUa")

idx = server.register_namespace("urn:sensors")
objects = server.get_objects_node()

# Variable de tipo ByteString
sensor_node = objects.add_variable(
    idx, "Sensor1",
    ua.Variant(b"", ua.VariantType.ByteString) # Valor inicial vacío
)

# Hacemos el nodo escribible usando set_writable()
# Este método debería ser compatible con tu versión de la librería.
sensor_node.set_writable()

print("Servidor iniciado en opc.tcp://127.0.0.1:4840")
print(f"Nodo: ns={idx};s=Sensor1 (ByteString)")

server.start()
try:
    while True:
        time.sleep(1)
        raw = sensor_node.get_value()
        if raw:
            try:
                # Deserializar la estructura Sensor
                id_, temp, pres, hum, ts_bytes = struct.unpack("<ifff64s", raw)
                ts = ts_bytes.rstrip(b'\x00').decode('utf-8')
                print(f"id={id_}  T={temp:.2f}°C  P={pres:.1f} hPa  H={hum:.1f}%  ts={ts}")
            except struct.error as e:
                print(f"Error al desempaquetar los datos del sensor: {e}")
                print(f"Tamaño de datos recibidos: {len(raw)} bytes")
                print(f"Raw data (hex): {raw.hex()}")
        else:
            print("Sensor1 vacío o no se han recibido datos.")
except KeyboardInterrupt:
    pass
finally:
    server.stop()
    print("Servidor detenido.")