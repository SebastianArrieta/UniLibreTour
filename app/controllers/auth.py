from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_access_cookies,
)
from marshmallow import ValidationError

from app.extensions import db
from app.models.usuario import Usuario
from app.schemas.auth import LoginSchema
from app.services import museo
from app.services import correo as correo_svc
from app.services import otp as otp_svc
from app.services import limite
from app.services.auth import verify_password
from app.services.usuario import obtener_por_email
from app.utils.response import json_error, json_ok

auth_bp = Blueprint("auth", __name__)
login_schema = LoginSchema()


def _token_de(usuario) -> str:
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )


def _respuesta_sesion(usuario):
    """Sesión completa: token en el cuerpo (API) y en cookie httpOnly (vistas)."""
    token = _token_de(usuario)
    respuesta, status = json_ok({"access_token": token, "usuario": usuario.to_dict()})
    set_access_cookies(respuesta, token)  # cookie httpOnly para navegación
    return respuesta, status


def _perfil_contrato(usuario_id: int) -> dict | None:
    """Usuario en la forma del contrato del frontend (name/points/badgeIds…)."""
    uid = str(usuario_id)
    return next((u for u in museo.usuarios() if u["id"] == uid), None)


# -----------------------------------------------------------------------------
# Segundo factor (2FA)
# -----------------------------------------------------------------------------
def _secreto() -> str:
    return current_app.config["JWT_SECRET_KEY"]


def _token_desafio(usuario, codigo: str, nonce: str, intentos: int) -> str:
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "rol": usuario.rol,
            "email": usuario.email,
            "scope": "2fa",
            "nonce": nonce,
            "otp": otp_svc.huella(_secreto(), nonce, codigo),
            "att": intentos,
        },
        expires_delta=timedelta(minutes=otp_svc.OTP_TTL_MINUTOS),
    )


def _token_desafio_desde_claims(usuario, claims: dict, intentos: int) -> str:
    """Reemite el desafío conservando nonce y huella (solo suma intentos)."""
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "rol": claims.get("rol", usuario.rol),
            "email": claims.get("email", usuario.email),
            "scope": "2fa",
            "nonce": claims.get("nonce", ""),
            "otp": claims.get("otp", ""),
            "att": intentos,
        },
        expires_delta=timedelta(minutes=otp_svc.OTP_TTL_MINUTOS),
    )


def _eco_desarrollo() -> bool:
    cfg = current_app.config
    return bool(cfg.get("OTP_DEV_ECHO") and cfg.get("DEBUG"))


def _dos_factores_disponible() -> bool:
    """El 2FA solo se exige si hay forma de entregar el código."""
    return correo_svc.correo_configurado() or _eco_desarrollo()


def _respuesta_desafio(usuario, codigo: str, nonce: str, intentos: int = 0):
    payload = {
        "requires_2fa": True,
        "pending_token": _token_desafio(usuario, codigo, nonce, intentos),
        "usuario": usuario.to_dict(),
    }
    if correo_svc.correo_configurado():
        try:
            correo_svc.enviar_codigo_2fa(usuario.email, codigo, otp_svc.OTP_TTL_MINUTOS)
        except Exception:
            current_app.logger.exception("[2FA] No se pudo enviar el código a %s", usuario.email)
            return json_error("No se pudo enviar el código de verificación. Intenta más tarde.", 503)
    if _eco_desarrollo():
        # Solo desarrollo local (DEBUG + OTP_DEV_ECHO): nunca en producción.
        payload["dev_code"] = codigo
    return json_ok(payload)


def _ip() -> str:
    return request.remote_addr or "?"


# Solo cuentan los intentos FALLIDOS (ver app/services/limite.py).
VENTANA_FALLOS = 900          # 15 minutos
MAX_FALLOS_CUENTA = 10        # por email / usuario
MAX_FALLOS_IP = 100           # por IP (alto: muchos usuarios pueden compartirla)
MAX_REENVIOS_2FA = 5          # correos de código por usuario en la ventana


def _demasiados_intentos():
    return json_error("Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.", 429)


def _claims_desafio():
    """Lee y valida el token de desafío enviado en Authorization: Bearer."""
    encabezado = request.headers.get("Authorization", "")
    if not encabezado.startswith("Bearer "):
        return None, json_error("Token de verificación requerido", 401)

    try:
        claims = decode_token(encabezado[7:].strip())
    except Exception:
        return None, json_error("Token de verificación inválido o expirado", 401)

    if claims.get("scope") != "2fa":
        return None, json_error("Token de verificación inválido", 401)

    usuario = db.session.get(Usuario, int(claims.get("sub", 0)))
    if not usuario:
        return None, json_error("Usuario no encontrado", 401)

    return (claims, usuario), None


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    clave_cuenta = "login:" + str(data["email"]).strip().lower()
    clave_ip = "login-ip:" + _ip()
    if (limite.bloqueado(clave_cuenta, MAX_FALLOS_CUENTA, VENTANA_FALLOS)
            or limite.bloqueado(clave_ip, MAX_FALLOS_IP, VENTANA_FALLOS)):
        return _demasiados_intentos()

    usuario = obtener_por_email(data["email"])
    if not usuario or not verify_password(data["password"], usuario.password_hash):
        limite.registrar_fallo(clave_cuenta)
        limite.registrar_fallo(clave_ip)
        return json_error("Credenciales inválidas", 401)
    limite.limpiar(clave_cuenta)

    if usuario.estado != "activo":
        return json_error("Tu cuenta está pendiente de aprobación por un administrador", 403)

    if usuario.two_factor_enabled and not _dos_factores_disponible():
        current_app.logger.warning(
            "[2FA] %s tiene 2FA activo pero no hay correo configurado (MAIL_SERVER); se omite.",
            usuario.email,
        )
    elif usuario.two_factor_enabled:
        codigo = otp_svc.generar_codigo()
        return _respuesta_desafio(usuario, codigo, otp_svc.nuevo_nonce())

    return _respuesta_sesion(usuario)


@auth_bp.post("/2fa/verify")
def verificar_2fa():
    datos = request.get_json(silent=True) or {}
    codigo = str(datos.get("codigo", "")).strip()

    par, error = _claims_desafio()
    if error:
        return error
    claims, usuario = par

    clave_2fa = f"2fa:{usuario.id}"
    if limite.bloqueado(clave_2fa, MAX_FALLOS_CUENTA, VENTANA_FALLOS):
        return _demasiados_intentos()

    intentos = int(claims.get("att", 0))
    if intentos >= otp_svc.OTP_MAX_INTENTOS:
        return json_error("Demasiados intentos fallidos. Inicia sesión de nuevo.", 429)

    if not otp_svc.coincide(
        _secreto(),
        claims.get("nonce", ""),
        codigo,
        claims.get("otp", ""),
    ):
        limite.registrar_fallo(clave_2fa)
        restantes = otp_svc.OTP_MAX_INTENTOS - (intentos + 1)
        return jsonify({
            "ok": False,
            "error": "Código de verificación incorrecto",
            "pending_token": _token_desafio_desde_claims(usuario, claims, intentos + 1),
            "intentos_restantes": restantes,
        }), 401

    limite.limpiar(clave_2fa)
    return _respuesta_sesion(usuario)


@auth_bp.post("/2fa/resend")
def reenviar_2fa():
    par, error = _claims_desafio()
    if error:
        return error
    claims, usuario = par
    clave_reenvio = f"2fa-reenvio:{usuario.id}"
    if limite.bloqueado(clave_reenvio, MAX_REENVIOS_2FA, VENTANA_FALLOS):
        return json_error("Has pedido demasiados códigos. Espera unos minutos.", 429)
    limite.registrar_fallo(clave_reenvio)
    intentos = int(claims.get("att", 0))
    if intentos >= otp_svc.OTP_MAX_INTENTOS:
        return json_error("Demasiados intentos fallidos. Inicia sesión de nuevo.", 429)
    codigo = otp_svc.generar_codigo()
    # Conserva los intentos del desafío anterior: reenviar no reinicia el contador.
    return _respuesta_desafio(usuario, codigo, otp_svc.nuevo_nonce(), intentos)


@auth_bp.post("/logout")
def logout():
    respuesta, status = json_ok({"mensaje": "Sesión cerrada"})
    unset_access_cookies(respuesta)
    return respuesta, status


@auth_bp.get("/me")
@jwt_required()
def me():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    return json_ok(_perfil_contrato(usuario.id) or usuario.to_dict())
