"""Servicio de contenidos — aportes, revisión docente y cola de validación."""

from __future__ import annotations

from datetime import date, datetime

from app.extensions import db
from app.models.contenido import Coleccion, Contenido, Etiqueta
from app.models.usuario import Usuario
from app.services import notificacion as notificacion_svc

# Roles autorizados a aportar contenido (visitante es anónimo/solo lectura)
ROLES_CONTRIBUYENTES = ("estudiante", "docente", "egresado", "admin")

# Estado intermedio: el docente asignado revisa antes de la cola del admin.
ESTADO_REVISION_DOCENTE = "revision_docente"


def _obtener_o_crear_etiqueta(nombre: str) -> Etiqueta:
    et = Etiqueta.query.filter_by(nombre=nombre).first()
    if et is None:
        et = Etiqueta(nombre=nombre)
        db.session.add(et)
        db.session.flush()
    return et


def puede_aportar(usuario: Usuario) -> bool:
    return usuario.rol in ROLES_CONTRIBUYENTES


def _docente_valido(docente_id) -> Usuario | None:
    if not docente_id:
        return None
    docente = db.session.get(Usuario, int(docente_id))
    if docente and docente.rol == "docente" and docente.estado == "activo":
        return docente
    return None


def crear_contenido(data: dict, usuario: Usuario, estado: str | None = None) -> Contenido:
    """Crea una pieza. Si llega un docente asignado, nace en revisión docente;
    sin docente pasa directo a la cola del admin. El admin puede crear ya publicada."""
    docente = _docente_valido(data.get("docenteId"))
    if estado is None:
        estado = ESTADO_REVISION_DOCENTE if docente else "pendiente"

    categoria = (data.get("category") or "").strip()
    coleccion = Coleccion.query.filter_by(slug=categoria).first() if categoria else None
    publicado = estado in ("publicado", "institucional")

    contenido = Contenido(
        titulo=data["title"].strip(),
        categoria=categoria or None,
        descripcion=data["description"].strip(),
        fecha=data.get("date") or date.today().isoformat(),
        imagen=data.get("image"),
        autor=(data.get("author") or usuario.nombre).strip(),
        estado=estado,
        creador_id=usuario.id,
        docente_id=docente.id if docente else None,
        coleccion_id=coleccion.id if coleccion else None,
        validado_por=usuario.id if publicado else None,
        fecha_validacion=datetime.utcnow() if publicado else None,
    )
    db.session.add(contenido)
    db.session.flush()

    nombres = [str(t).strip() for t in data.get("tags") or [] if str(t).strip()]
    contenido.etiquetas = [_obtener_o_crear_etiqueta(n) for n in dict.fromkeys(nombres)]

    if docente and estado == ESTADO_REVISION_DOCENTE:
        notificacion_svc.crear(
            docente.id,
            f'{usuario.nombre} envió el aporte "{contenido.titulo}" para tu revisión.',
            tipo="revision",
            referencia_tipo="contenido",
            referencia_id=contenido.id,
        )

    db.session.commit()
    return contenido


def en_revision_para(docente_id: int) -> list[Contenido]:
    """Aportes que esperan el visto bueno de un docente concreto."""
    return (
        Contenido.query.filter_by(estado=ESTADO_REVISION_DOCENTE, docente_id=docente_id)
        .order_by(Contenido.id.desc())
        .all()
    )


def decision_docente(
    contenido: Contenido,
    revisor: Usuario,
    aprobar: bool,
    nota: str | None = None,
) -> Contenido | None:
    """El docente asignado aprueba (pasa a la cola del admin) o devuelve el aporte.
    Devuelve None si el revisor no corresponde o la pieza no está en revisión."""
    if contenido.estado != ESTADO_REVISION_DOCENTE:
        return None
    if revisor.rol != "admin" and contenido.docente_id != revisor.id:
        return None

    if aprobar:
        contenido.estado = "pendiente"
        contenido.observaciones = (nota or "").strip() or None
        for admin in Usuario.query.filter_by(rol="admin", estado="activo").all():
            notificacion_svc.crear(
                admin.id,
                f'{revisor.nombre} avaló el aporte "{contenido.titulo}". Queda pendiente de validación final.',
                tipo="validacion",
                referencia_tipo="contenido",
                referencia_id=contenido.id,
            )
        if contenido.creador_id:
            notificacion_svc.crear(
                contenido.creador_id,
                f'Tu aporte "{contenido.titulo}" superó la revisión docente y espera la validación del administrador.',
                tipo="aprobado",
                referencia_tipo="contenido",
                referencia_id=contenido.id,
            )
    else:
        contenido.estado = "devuelto"
        contenido.observaciones = (nota or "Devuelto por el docente revisor.").strip()
        if contenido.creador_id:
            notificacion_svc.crear(
                contenido.creador_id,
                f'Tu aporte "{contenido.titulo}" fue devuelto por el docente: {contenido.observaciones}',
                tipo="devuelto",
                referencia_tipo="contenido",
                referencia_id=contenido.id,
            )

    db.session.commit()
    return contenido
