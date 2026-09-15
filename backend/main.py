import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config.database import init_db
from router.routes import Router
from middleware.auth import AuthMiddleware
from utils.response import send_json, send_error


class MuseoHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.router = Router()
        self.auth = AuthMiddleware()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self._handle_request('GET')

    def do_POST(self):
        self._handle_request('POST')

    def do_PUT(self):
        self._handle_request('PUT')

    def do_DELETE(self):
        self._handle_request('DELETE')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _handle_request(self, method):
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            self.parsed_path = parsed.path
            self.query_params = query
            self.request_method = method

            self._set_cors_headers()

            body = None
            if method in ('POST', 'PUT'):
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    raw = self.rfile.read(content_length)
                    body = json.loads(raw.decode('utf-8'))
            self.body = body

            self.router.resolve(self)

        except json.JSONDecodeError:
            send_error(self, 400, 'JSON inválido')
        except Exception as e:
            send_error(self, 500, str(e))

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def log_message(self, format, *args):
        print(f"[{self.request_method}] {self.path} - {args[0]}")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    host = os.getenv('HOST', '0.0.0.0')

    # Intentar inicializar la tabla MySQL
    try:
        init_db()
    except Exception as e:
        print(f"Warning: No se pudo conectar a la base de datos al inicio: {e}")

    server = HTTPServer((host, port), MuseoHandler)
    print(f"Servidor corriendo en http://{host}:{port}")
    server.serve_forever()

