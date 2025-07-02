from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

sensor_data = [
    {
        "id": 1,
        "temperature": 25.5,
        "pression": 1013.25,
        "humidity": 65.2,
        "timestamp": 1720328207
    },
    {
        "id": 2,
        "temperature": 22.3,
        "pression": 1015.80,
        "humidity": 58.7,
        "timestamp": 1720327907
    },
    {
        "id": 3,
        "temperature": 26.1,
        "pression": 1012.90,
        "humidity": 67.5,
        "timestamp": 1720327607
    },
    {
        "id": 4,
        "temperature": 24.2,
        "pression": 1014.8,
        "humidity": 68.5,
        "timestamp": 1718439015  # 15 jun 08:30:15
    },
    {
        "id": 5,
        "temperature": 29.1,
        "pression": 1011.3,
        "humidity": 55.2,
        "timestamp": 1718461522  # 15 jun 14:45:22
    },
    {
        "id": 6,
        "temperature": 26.3,
        "pression": 1013.4,
        "humidity": 64.2,
        "timestamp": 1718705733  # 18 jun 10:15:33
    },
    {
        "id": 7,
        "temperature": 31.8,
        "pression": 1009.1,
        "humidity": 47.5,
        "timestamp": 1718729845  # 18 jun 16:57:25
    },
    {
        "id": 8,
        "temperature": 21.8,
        "pression": 1016.7,
        "humidity": 74.3,
        "timestamp": 1718863330  # 20 jun 06:15:30
    },
    {
        "id": 9,
        "temperature": 34.5,
        "pression": 1006.8,
        "humidity": 39.7,
        "timestamp": 1718885218  # 20 jun 12:20:18
    },
    {
        "id": 10,
        "temperature": 28.9,
        "pression": 1010.4,
        "humidity": 58.1,
        "timestamp": 1718908512  # 20 jun 18:45:12
    },
    {
        "id": 11,
        "temperature": 37.2,
        "pression": 1004.5,
        "humidity": 32.1,
        "timestamp": 1719058818  # 22 jun 14:40:18
    },
    {
        "id": 12,
        "temperature": 30.4,
        "pression": 1008.2,
        "humidity": 44.9,
        "timestamp": 1719082935  # 22 jun 21:22:15
    },
    {
        "id": 13,
        "temperature": 24.7,
        "pression": 1014.9,
        "humidity": 69.3,
        "timestamp": 1719221145  # 24 jun 08:25:45
    },
    {
        "id": 14,
        "temperature": 32.6,
        "pression": 1007.6,
        "humidity": 43.2,
        "timestamp": 1719243422  # 24 jun 14:37:02
    },
    {
        "id": 15,
        "temperature": 25.6,
        "pression": 1013.5,
        "humidity": 66.7,
        "timestamp": 1719308445  # 25 jun 09:30:45
    },
    {
        "id": 16,
        "temperature": 33.2,
        "pression": 1007.2,
        "humidity": 42.9,
        "timestamp": 1719329233  # 25 jun 15:20:33
    },
    {
        "id": 17,
        "temperature": 23.1,
        "pression": 1015.8,
        "humidity": 71.6,
        "timestamp": 1719481230  # 27 jun 07:13:50
    },
    {
        "id": 18,
        "temperature": 35.8,
        "pression": 1005.3,
        "humidity": 36.4,
        "timestamp": 1719508522  # 27 jun 14:48:42
    },
    {
        "id": 19,
        "temperature": 27.9,
        "pression": 1011.7,
        "humidity": 59.8,
        "timestamp": 1719574845  # 28 jun 09:14:05
    },
    {
        "id": 20,
        "temperature": 19.2,
        "pression": 1018.4,
        "humidity": 83.7,
        "timestamp": 1719606330  # 28 jun 18:58:50
    },
    {
        "id": 21,
        "temperature": 29.4,
        "pression": 1011.6,
        "humidity": 56.8,
        "timestamp": 1719665415  # 29 jun 11:50:15
    },
    {
        "id": 22,
        "temperature": 26.8,
        "pression": 1013.1,
        "humidity": 62.5,
        "timestamp": 1719691822  # 29 jun 19:10:22
    },
    {
        "id": 23,
        "temperature": 23.4,
        "pression": 1015.2,
        "humidity": 71.8,
        "timestamp": 1719736522  # 30 jun 07:42:02
    },
    {
        "id": 24,
        "temperature": 30.7,
        "pression": 1009.6,
        "humidity": 51.3,
        "timestamp": 1719757215  # 30 jun 13:33:35
    },
    {
        "id": 25,
        "temperature": 24.1,
        "pression": 1014.3,
        "humidity": 73.6,
        "timestamp": 1719794730  # 30 jun 23:58:50
    },
    {
        "id": 26,
        "temperature": 18.9,
        "pression": 1018.1,
        "humidity": 85.2,
        "timestamp": 1719808245  # 01 jul 03:44:05
    },
    {
        "id": 27,
        "temperature": 25.8,
        "pression": 1013.7,
        "humidity": 65.9,
        "timestamp": 1719829522  # 01 jul 09:38:42
    },
    {
        "id": 28,
        "temperature": 32.1,
        "pression": 1008.3,
        "humidity": 46.8,
        "timestamp": 1719855045  # 01 jul 16:44:05
    },
    {
        "id": 29,
        "temperature": 26.9,
        "pression": 1013.9,
        "humidity": 67.5,
        "timestamp": 1719872122  # 01 jul 21:28:42
    },
    {
        "id": 30,
        "temperature": 22.3,
        "pression": 1015.6,
        "humidity": 75.9,
        "timestamp": 1719887415  # 02 jul 01:43:35
    },
    {
        "id": 31,
        "temperature": 21.1,
        "pression": 1016.2,
        "humidity": 78.4,
        "timestamp": 1719891930  # 02 jul 02:58:50
    },
    {
        "id": 32,
        "temperature": 20.7,
        "pression": 1016.8,
        "humidity": 80.1,
        "timestamp": 1719894045  # 02 jul 03:34:05
    },
    {
        "id": 33,
        "temperature": 20.2,
        "pression": 1017.1,
        "humidity": 82.3,
        "timestamp": 1719896430
    }
]

next_id = 34


def get_current_timestamp():
    return int(time.time())


def timestamp_to_iso(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).isoformat() + "Z"
    except:
        return "Invalid timestamp"


@app.route('/api/ping', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",}), 200


@app.route('/api/sensors/data', methods=['POST'])
def create_sensor_data():
    global next_id

    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type debe ser application/json"
            }), 400

        data = request.get_json()
        required_fields = ['temperature', 'pression', 'humidity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Campo requerido faltante: {field}"
                }), 400

        try:
            temperature = float(data['temperature'])
            pression = float(data['pression'])
            humidity = float(data['humidity'])
        except (ValueError, TypeError):
            return jsonify({
                "error": "Los valores de temperatura, presión y humedad deben ser números"
            }), 400

        if humidity < 0 or humidity > 100:
            return jsonify({
                "error": "La humedad debe estar entre 0 y 100"
            }), 400

        if pression < 800 or pression > 1200:
            return jsonify({
                "error": "La presión debe estar entre 800 y 1200 hPa"
            }), 400

        timestamp = data.get('timestamp')
        if timestamp is not None:
            try:
                timestamp = int(timestamp)
            except (ValueError, TypeError):
                return jsonify({
                    "error": "El timestamp debe ser un número entero"
                }), 400
        else:
            timestamp = get_current_timestamp()

        new_record = {
            "id": next_id,
            "temperature": temperature,
            "pression": pression,
            "humidity": humidity,
            "timestamp": timestamp
        }

        sensor_data.append(new_record)
        next_id += 1

        return jsonify({
            "message": "Datos de sensor almacenados exitosamente",
            "data": new_record
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor"
        }), 500


@app.route('/api/sensors/data', methods=['GET'])
def get_sensor_data():
    try:
        start_timestamp = request.args.get('start_timestamp', type=int)
        end_timestamp = request.args.get('end_timestamp', type=int)
        limit = request.args.get('limit', type=int)

        filtered_data = sensor_data.copy()
        if start_timestamp:
            filtered_data = [d for d in filtered_data if d['timestamp'] >= start_timestamp]

        if end_timestamp:
            filtered_data = [d for d in filtered_data if d['timestamp'] <= end_timestamp]
        filtered_data.sort(key=lambda x: x['timestamp'], reverse=True)

        if limit and limit > 0:
            filtered_data = filtered_data[:limit]

        return jsonify({
            "count": len(filtered_data),
            "data": filtered_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor"
        }), 500


@app.route('/api/sensors/data/<int:data_id>', methods=['GET'])
def get_sensor_data_by_id(data_id):
    try:
        record = next((d for d in sensor_data if d['id'] == data_id), None)

        if not record:
            return jsonify({
                "error": f"No se encontró registro con ID {data_id}"
            }), 404

        return jsonify({
            "data": record
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint no encontrado"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Método HTTP no permitido"
    }), 405


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)