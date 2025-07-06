import base64
import sqlite3
from json import dumps, loads
from time import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_sock import Server, Sock

AES_KEY_PATH = "../.keys/aes.key"
AES_KEY: bytes | None = None

app = Flask(__name__)
CORS(app)

app.config["SOCK_SERVER_OPTIONS"] = {
    "ping_interval": 25,
}
sock = Sock(app)

clients: set[Server] = set()

connection = sqlite3.connect("sensor.db", check_same_thread=False)
connection.cursor().execute(
    """
    CREATE TABLE IF NOT EXISTS measurement (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id   SMALLINT NOT NULL,
        temperature FLOAT    NOT NULL,
        pressure    FLOAT    NOT NULL,
        humidity    FLOAT    NOT NULL,
        timestamp   DATETIME NOT NULL
    );
    """,
)


def load_aes_key() -> None:
    global AES_KEY
    try:
        with open(AES_KEY_PATH, "rb") as key_file:
            AES_KEY = key_file.read()
        print("Loaded AES key")
    except Exception as e:
        print(f"Error loading AES key: {e}")
        exit(1)


def decrypt_data(encrypted_data: str, iv: str) -> str | None:
    try:
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)

        ciphertext = encrypted_bytes[:-16]
        tag = encrypted_bytes[-16:]

        cipher = Cipher(
            algorithms.AES(AES_KEY),
            modes.GCM(iv_bytes, tag),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted_data.decode("utf-8")

    except Exception as e:
        print(f"Decryption error: {e}")
        return None


def row_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "sensor_id": row[1],
        "temperature": row[2],
        "pressure": row[3],
        "humidity": row[4],
        "timestamp": row[5],
    }


@sock.route("/ws/measurements")
def connect_ws(ws: Server) -> None:
    clients.add(ws)

    try:
        while True:
            data = ws.receive()
            if data == "close":
                break
    except Exception as e:
        print(e)
    finally:
        clients.discard(ws)


@app.route("/api/ping", methods=["GET"])
def health_check() -> tuple[str, int]:
    return "", 200


@app.route("/api/measurements", methods=["POST"])
def create_sensor_data() -> tuple[Response | str, int]:
    try:
        if not request.is_json:
            return jsonify(
                {
                    "error": "Content-Type debe ser application/json",
                },
            ), 400

        encrypted_data = request.get_json()
        required_fields = ["encrypted_data", "iv"]
        for field in required_fields:
            if field not in encrypted_data:
                return jsonify(
                    {
                        "error": f"Campo requerido faltante: {field}",
                    },
                ), 400

        decrypted_json = decrypt_data(encrypted_data["encrypted_data"], encrypted_data["iv"])
        if decrypted_json is None:
            return jsonify(
                {
                    "error": "Error al descifrar los datos",
                },
            ), 400

        try:
            data = loads(decrypted_json)
        except Exception as e:
            print(e)
            return jsonify(
                {
                    "error": "Error al parsear los datos descifrados",
                },
            ), 400

        required_fields = ["sensor_id", "temperature", "pressure", "humidity", "timestamp"]
        for field in required_fields:
            if field not in data:
                return jsonify(
                    {
                        "error": f"Campo requerido faltante: {field}",
                    },
                ), 400

        try:
            sensor_id = int(data["sensor_id"])
            temperature = float(data["temperature"])
            pressure = float(data["pressure"])
            humidity = float(data["humidity"])
            timestamp = int(data["timestamp"])
        except (ValueError, TypeError):
            return jsonify(
                {
                    "error": "Los valores de temperatura, presión y humedad deben ser números",
                },
            ), 400

        if humidity < 0 or humidity > 100:
            return jsonify(
                {
                    "error": "La humedad debe estar entre 0 y 100",
                },
            ), 400

        if pressure < 800 or pressure > 1200:
            return jsonify(
                {
                    "error": "La presión debe estar entre 800 y 1200 hPa",
                },
            ), 400

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO measurement (sensor_id, temperature, pressure, humidity, timestamp)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id;
            """,
            (sensor_id, temperature, pressure, humidity, timestamp),
        )
        measurement_id = cursor.fetchone()[0]
        connection.commit()

        json_data = dumps(
            {
                "id": measurement_id,
                "sensor_id": sensor_id,
                "temperature": temperature,
                "pressure": pressure,
                "humidity": humidity,
                "timestamp": timestamp,
            },
        )

        for client in clients:
            try:
                client.send(json_data)
            except Exception as e:
                print(e)

        return "", 201

    except Exception as e:
        print(e)
        return jsonify(
            {
                "error": "Error interno del servidor",
            },
        ), 500


@app.route("/api/measurements", methods=["GET"])
def get_sensor_data() -> tuple[Response, int]:
    try:
        start_timestamp = request.args.get("start_timestamp", type=int, default=0)
        end_timestamp = request.args.get("end_timestamp", type=int, default=int(time() * 1000))
        limit = request.args.get("limit", type=int, default=-1)

        cursor = connection.cursor()
        result = cursor.execute(
            """
            SELECT id, sensor_id, temperature, pressure, humidity, timestamp
            FROM measurement
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (start_timestamp, end_timestamp, limit),
        )
        data = result.fetchall()
        measurements = [row_to_dict(row) for row in data]

        return jsonify(measurements), 200

    except Exception as e:
        print(e)
        return jsonify(
            {
                "error": "Error interno del servidor",
            },
        ), 500


@app.route("/api/sensors/<int:sensor_id>", methods=["GET"])
def get_sensor_data_by_id(sensor_id: int) -> tuple[Response, int]:
    try:
        start_timestamp = request.args.get("start_timestamp", type=int, default=0)
        end_timestamp = request.args.get("end_timestamp", type=int, default=int(time() * 1000))
        limit = request.args.get("limit", type=int, default=-1)

        cursor = connection.cursor()
        result = cursor.execute(
            """
            SELECT id, sensor_id, temperature, pressure, humidity, timestamp
            FROM measurement
            WHERE (timestamp BETWEEN ? AND ?)
              AND (sensor_id = ?)
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (start_timestamp, end_timestamp, sensor_id, limit),
        )
        data = result.fetchall()
        measurements = [row_to_dict(row) for row in data]

        return jsonify(measurements), 200

    except Exception as e:
        print(e)
        return jsonify(
            {
                "error": "Error interno del servidor",
            },
        ), 500


@app.errorhandler(404)
def not_found(_) -> tuple[Response, int]:
    return jsonify(
        {
            "error": "Endpoint no encontrado",
        },
    ), 404


@app.errorhandler(405)
def method_not_allowed(_) -> tuple[Response, int]:
    return jsonify(
        {
            "error": "Método HTTP no permitido",
        },
    ), 405


if __name__ == "__main__":
    load_aes_key()
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False,
    )
