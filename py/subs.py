from datetime import datetime
from struct import unpack
from time import sleep

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from opcua import Client


def load_public_key(key_path: str):
    try:
        with open(key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        return public_key
    except Exception as e:
        print(f"Error loading public key: {e}")
        return None


def verify_signature(data: bytes, signature: bytes, public_key) -> bool:
    try:
        public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        print(f"Error during signature verification: {e}")
        return False


def deserialize_signed_data(raw_data: bytes) -> tuple[bytes, bytes]:
    if len(raw_data) < 24:
        raise ValueError("Invalid data (len 24)")

    sensor_data = raw_data[:24]

    if len(raw_data) < 32:
        raise ValueError("Invalid data (len 32)")

    signature_length = unpack("<Q", raw_data[24:32])[0]

    if len(raw_data) < 32 + signature_length:
        raise ValueError(f"Invalid data (len {32 + signature_length})")

    signature = raw_data[32:32 + signature_length]

    return sensor_data, signature


def main() -> None:
    url = "opc.tcp://localhost:4840"
    client = Client(url)

    public_key = load_public_key("../.keys/sensor_public.pem")
    if not public_key:
        print("Failed to load public key")
        return

    try:
        client.connect()
        print("Connected to OPC UA server.")
        nodo = client.get_node("ns=1;s=sensor")

        while True:
            try:
                raw = nodo.get_value()
                if not raw or len(raw) == 0:
                    print("No data received")
                    sleep(0.5)
                    continue

                sensor_data, signature = deserialize_signed_data(raw)
                is_valid = verify_signature(sensor_data, signature, public_key)

                sensor_id, temperature, pressure, humidity, timestamp = unpack("<ifffQ", sensor_data)
                timestamp_string = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')

                status_text = "VALID" if is_valid else "INVALID"

                print(f"\n[sub] signature: {status_text}")
                print(f"    sensor_id        = {sensor_id}")
                print(f"    temperature      = {temperature}")
                print(f"    pressure         = {pressure}")
                print(f"    humidity         = {humidity}")
                print(f"    timestamp        = {timestamp_string}")
                print(f"    signature_length = {len(signature)}")

            except Exception as e:
                print(f"Error processing data: {e}")

            sleep(0.5)

    except Exception as e:
        print("Error when connecting/reading:", e)

    finally:
        client.disconnect()
        print("Closed connection.")


if __name__ == "__main__":
    main()
