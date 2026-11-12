from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
jwt = JWTManager()


@jwt.token_verification_loader
def _rechazar_token_de_desafio(jwt_header, jwt_payload):
    """Un token de desafío 2FA (scope=2fa) no sirve como sesión: solo el
    endpoint de verificación puede consumirlo."""
    return jwt_payload.get("scope") != "2fa"


@jwt.token_verification_failed_loader
def _token_de_desafio_rechazado(jwt_header, jwt_payload):
    return jsonify({"ok": False, "error": "El token de verificación 2FA no es una sesión válida"}), 401


@jwt.user_lookup_loader
def _cargar_usuario_token(jwt_header, jwt_payload):
    """Usuario real del token. Si ya no existe, está inactivo o su versión de
    sesión cambió (rol/estado), la sesión deja de ser válida.

    Así un JWT viejo (cuenta eliminada, BD recreada o rol modificado) recibe
    401 en lugar de provocar errores de integridad o conservar permisos viejos.
    """
    from app.models.usuario import Usuario

    try:
        identidad = int(jwt_payload.get("sub"))
    except (TypeError, ValueError):
        return None

    usuario = db.session.get(Usuario, identidad)
    if usuario is None or usuario.estado != "activo":
        return None

    try:
        version_token = int(jwt_payload.get("ver", 0))
    except (TypeError, ValueError):
        return None
    if version_token != int(usuario.token_version or 0):
        return None
    return usuario


@jwt.user_lookup_error_loader
def _usuario_de_token_inexistente(jwt_header, jwt_payload):
    return jsonify({"ok": False, "error": "La sesión ya no es válida. Inicia sesión de nuevo."}), 401


@jwt.token_in_blocklist_loader
def _token_en_lista_de_revocados(jwt_header, jwt_payload):
    """Logout real: el jti del token se guarda hasta que expire."""
    from app.services import token as token_svc

    return token_svc.revocado(jwt_payload.get("jti"))


@jwt.unauthorized_loader
def _falta_token(reason):
    return jsonify({"ok": False, "error": "Se requiere iniciar sesión"}), 401


@jwt.expired_token_loader
def _token_expirado(jwt_header, jwt_payload):
    return jsonify({"ok": False, "error": "La sesión ha expirado. Inicia sesión de nuevo."}), 401


@jwt.invalid_token_loader
def _token_invalido(reason):
    return jsonify({"ok": False, "error": "Token de sesión inválido"}), 401


@jwt.revoked_token_loader
def _token_revocado(jwt_header, jwt_payload):
    return jsonify({"ok": False, "error": "La sesión fue cerrada. Inicia sesión de nuevo."}), 401
