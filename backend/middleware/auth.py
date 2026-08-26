from services.auth import verify_token
from utils.response import send_error
from models.usuario import UsuarioModel


class AuthMiddleware:
    @staticmethod
    def require_auth(handler):
        auth_header = handler.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            send_error(handler, 401, 'Token requerido')
            return False

        token = auth_header.split(' ', 1)[1]
        user_id = verify_token(token)
        if not user_id:
            send_error(handler, 401, 'Token inválido')
            return False

        usuario = UsuarioModel.find_by_id(user_id)
        if not usuario:
            send_error(handler, 401, 'Usuario no encontrado')
            return False

        handler.current_user = usuario
        return True

    @staticmethod
    def require_role(rol):
        def decorator(handler):
            if not AuthMiddleware.require_auth(handler):
                return False
            if handler.current_user['rol'] != rol:
                send_error(handler, 403, 'No tienes permiso')
                return False
            return True
        return decorator
