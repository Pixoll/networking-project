from opcua import Client
import time
import struct

url = "opc.tcp://localhost:4840"
client = Client(url)

try:
    client.connect()
    print("Connected to OPC UA server.")
    nodo = client.get_node("ns=1;s=sensor")

    while True:
        raw = nodo.get_value()
        id_, temp, pres, hum, ts_bytes = struct.unpack("<ifff21s", raw)
        ts = ts_bytes.rstrip(b'\x00').decode("utf-8")
        print("\n[sub]:")
        print(f"    id = {id_}")
        print(f"    temp = {temp}")
        print(f"    pes = {pres}")
        print(f"    hum = {hum}")
        print(f"    time = {ts}")

        time.sleep(0.5)

except Exception as e:
    print("Error when connecting/reading:", e)

finally:
    client.disconnect()
    print("Closed connection.")
