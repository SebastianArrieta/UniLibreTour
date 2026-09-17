from flask import jsonify


def json_ok(data, status: int = 200):
    return jsonify(data), status


def json_error(mensaje, status: int = 400):
    if not isinstance(mensaje, str):
        mensaje = str(mensaje)
    return jsonify({"error": mensaje}), status
