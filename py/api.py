import sqlite3
from time import time

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
app = Flask(__name__)
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

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

@socketio.on('connect')
def handle_connect():
    emit('conectado', {'message': 'te conectaste a al api'})

@socketio.on('disconnect')
def handle_disconnect():
    emit('desconectado', {'message': f'{request.sid}'}, broadcast=True)


@socketio.on('request_latest_data')
def handle_request_latest_data(data):
    try:
        start_timestamp = data.get('start_timestamp', 0)
        end_timestamp = data.get('end_timestamp', int(time() * 1000))
        limit = data.get('limit', -1)

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
        measurements = [row_to_dict(row) for row in result.fetchall()]
        emit('latest_data', {'data': measurements})

    except Exception as e:
        print(f"Error en WebSocket request_latest_data: {e}")
        emit('error', {'message': 'Error interno del servidor'})
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
        end_timestamp = request.args.get("end_timestamp", type=int, default=time() * 1000)
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
        end_timestamp = request.args.get("end_timestamp", type=int, default=time() * 1000)
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
    app.run(debug=True, host="0.0.0.0", port=5000)
