import re
from controllers import usuarios
from utils.response import send_json, send_error


class Router:
    def __init__(self):
        self.routes = []

        self._add('GET', '/api/health', self._health)
        self._add('GET', '/api/usuarios', usuarios.listar)
        self._add('GET', r'/api/usuarios/(\d+)', usuarios.obtener)
        self._add('POST', '/api/usuarios', usuarios.crear)
        self._add('PUT', r'/api/usuarios/(\d+)', usuarios.actualizar)
        self._add('DELETE', r'/api/usuarios/(\d+)', usuarios.eliminar)

    def _add(self, method, path, handler):
        pattern = re.compile(r'^' + path + r'$')
        self.routes.append((method, pattern, handler))

    def resolve(self, handler):
        method = handler.request_method
        path = handler.parsed_path

        for route_method, pattern, callback in self.routes:
            if route_method != method:
                continue
            match = pattern.match(path)
            if match:
                handler.path_params = match.groups()
                callback(handler)
                return

        send_error(handler, 404, 'Ruta no encontrada')

    @staticmethod
    def _health(handler):
        send_json(handler, 200, {'status': 'ok', 'servidor': 'UniLibreTour'})
