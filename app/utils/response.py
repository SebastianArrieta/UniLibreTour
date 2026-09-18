from flask import jsonify


def json_ok(data=None, status: int = 200):
    return jsonify({"ok": True, "data": data}), status


def json_error(mensaje, status: int = 400):
    if not isinstance(mensaje, (str, dict, list)):
        mensaje = str(mensaje)
    return jsonify({"ok": False, "error": mensaje}), status
