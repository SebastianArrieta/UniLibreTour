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
