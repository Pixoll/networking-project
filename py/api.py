import time

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

sensor_data = [
    {
        "id": 1,
        "sensor_id": 1,
        "temperature": 26.1,
        "pressure": 1012.90,
        "humidity": 67.5,
        "timestamp": 1718461522000,
    },
    {
        "id": 2,
        "sensor_id": 1,
        "temperature": 24.2,
        "pressure": 1014.8,
        "humidity": 68.5,
        "timestamp": 1718542658000,
    },
    {
        "id": 3,
        "sensor_id": 1,
        "temperature": 29.1,
        "pressure": 1011.3,
        "humidity": 55.2,
        "timestamp": 1718612698000,
    },
    {
        "id": 4,
        "sensor_id": 1,
        "temperature": 26.3,
        "pressure": 1013.4,
        "humidity": 64.2,
        "timestamp": 1718705733000,
    },
    {
        "id": 5,
        "sensor_id": 1,
        "temperature": 31.8,
        "pressure": 1009.1,
        "humidity": 47.5,
        "timestamp": 1718729845000,
    },
    {
        "id": 6,
        "sensor_id": 1,
        "temperature": 21.8,
        "pressure": 1016.7,
        "humidity": 74.3,
        "timestamp": 1718863330000,
    },
    {
        "id": 7,
        "sensor_id": 1,
        "temperature": 34.5,
        "pressure": 1006.8,
        "humidity": 39.7,
        "timestamp": 1718885218000,
    },
    {
        "id": 8,
        "sensor_id": 1,
        "temperature": 28.9,
        "pressure": 1010.4,
        "humidity": 58.1,
        "timestamp": 1718908512000,
    },
    {
        "id": 9,
        "sensor_id": 1,
        "temperature": 37.2,
        "pressure": 1004.5,
        "humidity": 32.1,
        "timestamp": 1719058818000,
    },
    {
        "id": 10,
        "sensor_id": 1,
        "temperature": 30.4,
        "pressure": 1008.2,
        "humidity": 44.9,
        "timestamp": 1719082935000,
    },
    {
        "id": 11,
        "sensor_id": 1,
        "temperature": 24.7,
        "pressure": 1014.9,
        "humidity": 69.3,
        "timestamp": 1719221145000,
    },
    {
        "id": 12,
        "sensor_id": 1,
        "temperature": 32.6,
        "pressure": 1007.6,
        "humidity": 43.2,
        "timestamp": 1719243422000,
    },
    {
        "id": 13,
        "sensor_id": 1,
        "temperature": 25.6,
        "pressure": 1013.5,
        "humidity": 66.7,
        "timestamp": 1719308445000,
    },
    {
        "id": 14,
        "sensor_id": 1,
        "temperature": 33.2,
        "pressure": 1007.2,
        "humidity": 42.9,
        "timestamp": 1719329233000,
    },
    {
        "id": 15,
        "sensor_id": 1,
        "temperature": 23.1,
        "pressure": 1015.8,
        "humidity": 71.6,
        "timestamp": 1719481230000,
    },
    {
        "id": 16,
        "sensor_id": 1,
        "temperature": 35.8,
        "pressure": 1005.3,
        "humidity": 36.4,
        "timestamp": 1719508522000,
    },
    {
        "id": 17,
        "sensor_id": 1,
        "temperature": 27.9,
        "pressure": 1011.7,
        "humidity": 59.8,
        "timestamp": 1719574845000,
    },
    {
        "id": 18,
        "sensor_id": 1,
        "temperature": 19.2,
        "pressure": 1018.4,
        "humidity": 83.7,
        "timestamp": 1719606330000,
    },
    {
        "id": 19,
        "sensor_id": 1,
        "temperature": 29.4,
        "pressure": 1011.6,
        "humidity": 56.8,
        "timestamp": 1719665415000,
    },
    {
        "id": 20,
        "sensor_id": 1,
        "temperature": 26.8,
        "pressure": 1013.1,
        "humidity": 62.5,
        "timestamp": 1719691822000,
    },
    {
        "id": 21,
        "sensor_id": 1,
        "temperature": 23.4,
        "pressure": 1015.2,
        "humidity": 71.8,
        "timestamp": 1719736522000,
    },
    {
        "id": 22,
        "sensor_id": 1,
        "temperature": 30.7,
        "pressure": 1009.6,
        "humidity": 51.3,
        "timestamp": 1719757215000,
    },
    {
        "id": 23,
        "sensor_id": 1,
        "temperature": 24.1,
        "pressure": 1014.3,
        "humidity": 73.6,
        "timestamp": 1719794730000,
    },
    {
        "id": 24,
        "sensor_id": 1,
        "temperature": 18.9,
        "pressure": 1018.1,
        "humidity": 85.2,
        "timestamp": 1719808245000,
    },
    {
        "id": 25,
        "sensor_id": 1,
        "temperature": 25.8,
        "pressure": 1013.7,
        "humidity": 65.9,
        "timestamp": 1719829522000,
    },
    {
        "id": 26,
        "sensor_id": 1,
        "temperature": 32.1,
        "pressure": 1008.3,
        "humidity": 46.8,
        "timestamp": 1719855045000,
    },
    {
        "id": 27,
        "sensor_id": 1,
        "temperature": 26.9,
        "pressure": 1013.9,
        "humidity": 67.5,
        "timestamp": 1719872122000,
    },
    {
        "id": 28,
        "sensor_id": 1,
        "temperature": 22.3,
        "pressure": 1015.6,
        "humidity": 75.9,
        "timestamp": 1719887415000,
    },
    {
        "id": 29,
        "sensor_id": 1,
        "temperature": 21.1,
        "pressure": 1016.2,
        "humidity": 78.4,
        "timestamp": 1719906330000,
    },
    {
        "id": 30,
        "sensor_id": 1,
        "temperature": 20.7,
        "pressure": 1016.8,
        "humidity": 80.1,
        "timestamp": 1719922845000,
    },
    {
        "id": 31,
        "sensor_id": 1,
        "temperature": 2,
        "pressure": 953.25,
        "humidity": 6,
        "timestamp": 1719946607000,
    },
    {
        "id": 32,
        "sensor_id": 1,
        "temperature": 52.3,
        "pressure": 1055.80,
        "humidity": 100,
        "timestamp": 1719957107000,
    },
]

next_id = 33


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
