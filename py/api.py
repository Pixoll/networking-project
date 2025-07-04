import sqlite3
from time import time
from json import dumps, loads
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app)

app.config["SOCK_SERVER_OPTIONS"] = {
    "ping_interval": 25,
}
sock = Sock(app)

clients = []

connection = sqlite3.connect("sensor.db", check_same_thread=False)
cursor = connection.cursor()
cursor.execute(
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


def row_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "sensor_id": row[1],
        "temperature": row[2],
        "pressure": row[3],
        "humidity": row[4],
        "timestamp": row[5],
    }


@sock.route("/ws")
def connect_ws(ws):
    clients.append(ws)
    result = cursor.execute(
        """
        SELECT id, sensor_id, temperature, pressure, humidity, timestamp
        FROM measurement
        ORDER BY timestamp DESC
        LIMIT 20;
        """,
    )
    initial_data = result.fetchall()
    measurements = [row_to_dict(row) for row in initial_data]

    initial_message = {
        "type": "initial_data",
        "data": measurements
    }
    ws.send(dumps(initial_message))

    try:
        while True:
            data = ws.receive()
            if data == "close":
                break
    except:
        pass
    finally:
        if ws in clients:
            clients.remove(ws)


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

        data = request.get_json()
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

        cursor.execute(
            """
            INSERT INTO measurement (sensor_id, temperature, pressure, humidity, timestamp)
            VALUES (?, ?, ?, ?, ?);
            """,
            (sensor_id, temperature, pressure, humidity, timestamp),
        )
        connection.commit()

        ws_message = {
            "type": "new_measurement",
            "data": data
        }
        json_data = dumps(ws_message)
        for client in clients:
            try:
                client.send(json_data)
            except:
                pass

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
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )