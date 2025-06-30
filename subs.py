from opcua import Client
import time
import json

# Dirección del servidor OPC UA
url = "opc.tcp://localhost:4840"
client = Client(url)

try:
    client.connect()
    print("Conectado al servidor OPC UA.")

    # Obtener el nodo de publicacion
    nodo = client.get_node("ns=1;s=Publicacion")

    # Loop de lectura continua
    while True:
        valor = nodo.get_value()
        try:
            datos = json.loads(valor)
            print("\n[Subscriber] JSON recibido:")
            for clave, val in datos.items():
                print(f"  {clave}: {val}")
        except json.JSONDecodeError:
            print("[Subscriber] No se pudo decodificar como JSON:", valor)

        time.sleep(0.5)  # Espera entre lecturas

except Exception as e:
    print("Error en la conexión o lectura:", e)

finally:
    client.disconnect()
    print("Conexión cerrada.")
