from opcua import Client
from time import sleep
from struct import unpack
from datetime import datetime

def main() -> None:
    url = "opc.tcp://localhost:4840"
    client = Client(url)

    try:
        client.connect()
        print("Connected to OPC UA server.")
        nodo = client.get_node("ns=1;s=sensor")

        while True:
            raw = nodo.get_value()
            id_, temp, pres, hum, ts = unpack("<ifffq", raw)
            timestamp = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
            print("\n[sub]:")
            print(f"    id = {id_}")
            print(f"    temp = {temp}")
            print(f"    pes = {pres}")
            print(f"    hum = {hum}")
            print(f"    time = {timestamp}")

            sleep(0.5)

    except Exception as e:
        print("Error when connecting/reading:", e)

    finally:
        client.disconnect()
        print("Closed connection.")

if __name__ == "__main__":
    main()
