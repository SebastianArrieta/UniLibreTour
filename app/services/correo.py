"""Envío de correo saliente (SMTP de la librería estándar, sin dependencias)."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def correo_configurado() -> bool:
    cfg = current_app.config
    return bool(cfg.get("MAIL_SERVER") and cfg.get("MAIL_FROM"))


def enviar(destinatario: str, asunto: str, cuerpo: str) -> None:
    """Envía un correo de texto plano. Lanza excepción si falla."""
    cfg = current_app.config
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = destinatario
    msg.set_content(cuerpo)

    servidor, puerto = cfg["MAIL_SERVER"], int(cfg.get("MAIL_PORT", 587))
    contexto = ssl.create_default_context()
    if cfg.get("MAIL_USE_SSL"):
        smtp = smtplib.SMTP_SSL(servidor, puerto, context=contexto, timeout=15)
    else:
        smtp = smtplib.SMTP(servidor, puerto, timeout=15)
    with smtp:
        if not cfg.get("MAIL_USE_SSL") and cfg.get("MAIL_USE_TLS"):
            smtp.starttls(context=contexto)
        if cfg.get("MAIL_USERNAME"):
            smtp.login(cfg["MAIL_USERNAME"], cfg.get("MAIL_PASSWORD", ""))
        smtp.send_message(msg)


def enviar_codigo_2fa(destinatario: str, codigo: str, minutos: int) -> None:
    enviar(
        destinatario,
        "Tu código de verificación — Museo UniLibre",
        f"Tu código de verificación es: {codigo}\n\n"
        f"Caduca en {minutos} minutos. Si no intentaste iniciar sesión, ignora este mensaje.",
    )
