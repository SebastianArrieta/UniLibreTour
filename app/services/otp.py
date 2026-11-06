"""Códigos OTP del segundo factor de autenticación (2FA).

El código nunca se almacena ni se envía al cliente junto con el token de
sesión: viaja únicamente en un token de desafío firmado con los claims
``scope=2fa``, ``nonce`` y ``otp`` (huella HMAC-SHA256 calculada con el
secreto de la aplicación). Así la verificación ocurre siempre en el servidor
y el cliente no puede falsificarla.

Sin servidor de correo configurado, en desarrollo (``OTP_DEV_ECHO``) el código
se devuelve en la respuesta para poder probar el flujo. En producción debe
integrarse un proveedor de correo.
"""

import hashlib
import hmac
import secrets

OTP_LENGTH = 6
OTP_TTL_MINUTOS = 5
OTP_MAX_INTENTOS = 5


def generar_codigo() -> str:
    return f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"


def nuevo_nonce() -> str:
    return secrets.token_urlsafe(16)


def huella(secreto: str, nonce: str, codigo: str) -> str:
    return hmac.new(
        secreto.encode("utf-8"),
        f"{nonce}:{codigo}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def coincide(secreto: str, nonce: str, codigo: str, esperado: str) -> bool:
    return hmac.compare_digest(
        huella(secreto, nonce, codigo or ""),
        esperado or "",
    )
