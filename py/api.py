import time

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

sensor_data = []
next_id = 1


@app.route("/api/ping", methods=["GET"])
def health_check() -> tuple[str, int]:
    return "", 200


@app.route("/api/measurements", methods=["POST"])
def create_sensor_data() -> tuple[Response | str, int]:
    global next_id

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

        new_record = {
            "id": next_id,
            "sensor_id": sensor_id,
            "temperature": temperature,
            "pressure": pressure,
            "humidity": humidity,
            "timestamp": timestamp,
        }

        sensor_data.append(new_record)
        next_id += 1

        return "", 201

    except Exception:
        return jsonify(
            {
                "error": "Error interno del servidor",
            },
        ), 500


@app.route("/api/measurements", methods=["GET"])
def get_sensor_data() -> tuple[Response, int]:
    try:
        start_timestamp = request.args.get("start_timestamp", type=int)
        end_timestamp = request.args.get("end_timestamp", type=int)
        limit = request.args.get("limit", type=int)

        filtered_data = sensor_data.copy()
        if start_timestamp:
            filtered_data = [d for d in filtered_data if d["timestamp"] >= start_timestamp]

        if end_timestamp:
            filtered_data = [d for d in filtered_data if d["timestamp"] <= end_timestamp]
        filtered_data.sort(key=lambda x: x["timestamp"], reverse=True)

        if limit and limit > 0:
            filtered_data = filtered_data[:limit]

        return jsonify(filtered_data), 200

    except Exception:
        return jsonify(
            {
                "error": "Error interno del servidor",
            },
        ), 500


@app.route("/api/sensors/<int:sensor_id>", methods=["GET"])
def get_sensor_data_by_id(sensor_id: int) -> tuple[Response, int]:
    try:
        records = [d for d in sensor_data if d["sensor_id"] == sensor_id]

        if len(records) == 0:
            return jsonify(
                {
                    "error": f"No se encontró ningún registro con sensor_id {sensor_id}",
                },
            ), 404

        return jsonify(records), 200

    except Exception:
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
