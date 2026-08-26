import json


def send_json(handler, status_code, data):
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps(data, default=str).encode('utf-8'))


def send_error(handler, status_code, mensaje):
    send_json(handler, status_code, {'error': mensaje})
