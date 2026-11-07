"""Altas directas del administrador y acciones del flujo de validación."""

from __future__ import annotations

import json
from datetime import datetime

from app.extensions import db
from app.models.contenido import Contenido
from app.models.cronologia import CronologiaHito, Evento
from app.models.premio import Premio
from app.models.publicacion import HallFama, Noticia
from app.models.semillero import Semillero
from app.models.usuario import Usuario
from app.services import contenido as contenido_svc
from app.services import notificacion as notificacion_svc
from app.services.usuario import validar_cambio_admin


def _meta_hall(data: dict) -> str:
    return json.dumps(
        {"bio": (data.get("bio") or "").strip(), "badges": data.get("badges") or []},
        ensure_ascii=False,
    )


def _publicado_por(admin: Usuario) -> dict:
    return {"validado_por": admin.id, "fecha_validacion": datetime.utcnow()}


def crear_hito(data: dict, admin: Usuario) -> CronologiaHito:
    hito = CronologiaHito(
        anio=data["year"],
        titulo=data["title"].strip(),
        descripcion=data["description"].strip(),
        tipo=data["type"],
        media=json.dumps(data.get("media") or []),
        estado="publicado",
        creador_id=admin.id,
        **_publicado_por(admin),
    )
    db.session.add(hito)
    db.session.commit()
    return hito


def crear_premio(data: dict, admin: Usuario) -> Premio:
    premio = Premio(
        nombre=data["title"].strip(),
        anio=data["year"],
        lugar=data["institution"].strip(),
        descripcion=data["description"].strip(),
        categoria=data.get("category") or "premio",
        imagen=data.get("image"),
        estado="publicado",
        creador_id=admin.id,
        **_publicado_por(admin),
    )
    db.session.add(premio)
    db.session.commit()
    return premio


def crear_proyecto(data: dict, admin: Usuario) -> Contenido:
    payload = {
        "title": data["title"],
        "category": data["category"],
        "description": data["description"],
        "date": data.get("date"),
        "image": data.get("image"),
        "author": data["author"],
        "tags": data.get("tags") or [],
    }
    return contenido_svc.crear_contenido(payload, admin, estado="publicado")


def crear_hall(data: dict, admin: Usuario) -> HallFama:
    miembro = HallFama(
        nombre=data["name"].strip(),
        titulo=data["title"].strip(),
        anio=data["year"],
        logro=data["achievement"].strip(),
        categoria=data["category"].strip(),
        imagen=data.get("image"),
        estado="publicado",
        observaciones=_meta_hall(data),
        creador_id=admin.id,
        **_publicado_por(admin),
    )
    db.session.add(miembro)
    db.session.commit()
    return miembro


def crear_evento(data: dict, admin: Usuario) -> Evento:
    evento = Evento(
        titulo=data["title"].strip(),
        fecha=data["date"],
        hora=data["time"],
        ubicacion=data["location"].strip(),
        tipo=data["type"],
        descripcion=(data.get("description") or "").strip() or None,
        estado="publicado",
        creador_id=admin.id,
        **_publicado_por(admin),
    )
    db.session.add(evento)
    db.session.commit()
    return evento


def crear_noticia(data: dict, admin: Usuario) -> Noticia:
    noticia = Noticia(
        titulo=data["title"].strip(),
        resumen=data["excerpt"].strip(),
        fecha=data["date"],
        categoria=data["category"],
        imagen=data.get("image"),
        estado="publicado",
        creador_id=admin.id,
        **_publicado_por(admin),
    )
    db.session.add(noticia)
    db.session.commit()
    return noticia


def crear_semillero(data: dict, admin: Usuario) -> Semillero | None:
    lider_id = data.get("leadId")
    if lider_id is not None:
        lider = db.session.get(Usuario, lider_id)
        if lider is None or lider.rol != "docente":
            return None
    semillero = Semillero(
        nombre=data["name"].strip(),
        categoria=data["category"],
        lider_id=lider_id,
        descripcion=data["description"].strip(),
        imagen=data.get("image"),
    )
    db.session.add(semillero)
    db.session.commit()
    return semillero


def validar_contenido(contenido_id: int, data: dict, admin: Usuario) -> Contenido | None:
    contenido = db.session.get(Contenido, contenido_id)
    if contenido is None:
        return None

    accion = data["accion"]
    if accion == "devolver":
        contenido.estado = "devuelto"
        contenido.observaciones = (data.get("nota") or "Devuelto por el administrador").strip()
        tipo_notificacion = "devuelto"
        mensaje = f'Tu contribución "{contenido.titulo}" fue devuelta: {contenido.observaciones}'
    else:
        contenido.estado = (
            "institucional"
            if accion == "institucional" or data.get("tipo") == "institucional"
            else "publicado"
        )
        contenido.observaciones = (data.get("nota") or "").strip() or None
        contenido.validado_por = admin.id
        contenido.fecha_validacion = datetime.utcnow()
        if data.get("fecha_publicacion"):
            contenido.fecha = data["fecha_publicacion"]
        tipo_notificacion = "aprobado"
        mensaje = f'Tu contribución "{contenido.titulo}" fue aprobada y publicada.'
        if data.get("mensaje"):
            mensaje = f"{mensaje} {data['mensaje'].strip()}"

    if contenido.creador_id:
        notificacion_svc.crear(
            contenido.creador_id,
            mensaje,
            tipo=tipo_notificacion,
            referencia_tipo="contenido",
            referencia_id=contenido.id,
        )

    db.session.commit()
    return contenido


def actualizar_usuario(usuario: Usuario, data: dict) -> Usuario:
    validar_cambio_admin(
        usuario,
        nuevo_rol=data.get("rol"),
        nuevo_estado=data.get("estado"),
    )
    cambios_de_sesion = False
    for campo in ("nombre", "email", "rol", "estado"):
        valor = data.get(campo)
        if valor is not None and valor != getattr(usuario, campo):
            if campo in ("rol", "estado"):
                cambios_de_sesion = True
            setattr(usuario, campo, valor)
    if cambios_de_sesion:
        # Un rol/estado nuevo aplica de inmediato: invalida los JWT anteriores.
        usuario.token_version = (usuario.token_version or 0) + 1
    db.session.commit()
    return usuario


def aprobar_usuario(usuario: Usuario) -> Usuario:
    usuario.estado = "activo"
    notificacion_svc.crear(
        usuario.id,
        "Tu cuenta fue aprobada. Ya puedes iniciar sesión y aportar contenido.",
        tipo="sistema",
        referencia_tipo="usuario",
        referencia_id=usuario.id,
    )
    db.session.commit()
    return usuario
