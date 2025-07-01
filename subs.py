from opcua import Client
import time
import struct

# Dirección del servidor OPC UA
url = "opc.tcp://localhost:4840"
client = Client(url)

try:
    client.connect()
    print("Conectado al servidor OPC UA.")
    nodo = client.get_node("ns=1;s=Sensor1")

    while True:
        raw = nodo.get_value()
        id_, temp, pres, hum, ts_bytes = struct.unpack("<ifff64s", raw)
        ts = ts_bytes.rstrip(b'\x00').decode('utf-8')
        # id_ = valor[0:4]
        # temp = valor[4:8]
        # pres = valor[8:12]
        # hum = valor[12:16]
        # ts_bytes = valor[16:]
        print("\n[Subscriber] :")
        print(f"    id = {id_}")
        print(f"    temp = {temp}")
        print(f"    pes = {pres}")
        print(f"    hum = {hum}")
        print(f"    time = {ts}")

        time.sleep(0.5)

except Exception as e:
    print("Error en la conexión o lectura:", e)

finally:
    client.disconnect()
    print("Conexión cerrada.")
