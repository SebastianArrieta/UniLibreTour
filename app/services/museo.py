"""Servicio de lectura del Museo — integra y expone el dataset institucional desde la BD.

Cada función consulta las tablas reales y devuelve dicts estructurados
con las entidades del museo (colecciones, noticias, cronología, eventos,
investigación, insignias y aportes).
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func

from app.extensions import db

from app.models.contenido import Coleccion, Contenido, ContenidoEtiqueta, Etiqueta
from app.models.cronologia import CronologiaHito, Evento
from app.models.insignia import Insignia
from app.models.premio import Premio
from app.models.publicacion import HallFama, Noticia
from app.models.semillero import Semillero
from app.models.usuario import Usuario

POINTS_PER_LEVEL = 500
MAX_LEVEL = 20

ESTADOS_PUBLICADOS = ("publicado", "institucional")
ESTADOS_COLA = ("pendiente", "devuelto")

def colecciones() -> list[dict]:
    out = []
    for c in Coleccion.query.order_by(Coleccion.id.asc()).all():
        out.append({
            "id": c.slug or str(c.id),
            "title": c.titulo,
            "description": c.descripcion,
            "count": sum(1 for x in c.contenidos if x.estado in ESTADOS_PUBLICADOS),
            "icon": c.icono,
            "image": c.imagen,
        })
    return out


def noticias() -> list[dict]:
    q = Noticia.query.order_by(Noticia.fecha.desc()).all()
    return [
        {"id": f"n{n.id}", "title": n.titulo, "excerpt": n.resumen,
         "date": n.fecha, "category": n.categoria, "image": n.imagen}
        for n in q
    ]


def linea_tiempo() -> list[dict]:
    out = []
    for h in CronologiaHito.query.order_by(CronologiaHito.anio.asc()).all():
        item = {"year": h.anio, "title": h.titulo, "description": h.descripcion, "type": h.tipo}
        if h.contenido_id:
            item["itemId"] = str(h.contenido_id)
        out.append(item)
    return out


def eventos() -> list[dict]:
    q = Evento.query.order_by(Evento.fecha.asc()).all()
    return [
        {"id": f"e{e.id}", "title": e.titulo, "date": e.fecha, "time": e.hora,
         "location": e.ubicacion, "type": e.tipo, "description": e.descripcion}
        for e in q
    ]


def _contenido_dict(c: Contenido) -> dict:
    d = {
        "id": str(c.id),
        "title": c.titulo,
        "category": c.categoria,
        "author": c.autor,
        "date": c.fecha,
        "status": c.estado,
        "description": c.descripcion,
        "image": c.imagen,
        "tags": [e.nombre for e in c.etiquetas],
    }
    if c.creador is not None:
        d["submittedBy"] = c.creador.nombre
    if c.observaciones:
        d["reviewNote"] = c.observaciones
    return d


def contenido_dict(c: Contenido) -> dict:
    """Forma del contrato para una pieza concreta (incluye devueltas)."""
    return _contenido_dict(c)


def contenidos() -> list[dict]:
    """contentItems: todo el contenido que no fue devuelto por validación."""
    q = (
        Contenido.query.filter(Contenido.estado != "devuelto")
        .order_by(Contenido.id.asc())
        .all()
    )
    return [_contenido_dict(c) for c in q]


def contenidos_publicados() -> list[dict]:
    """Solo piezas publicadas/institucionales (lo único apto para el público)."""
    q = (
        Contenido.query.filter(Contenido.estado.in_(ESTADOS_PUBLICADOS))
        .order_by(Contenido.id.asc())
        .all()
    )
    return [_contenido_dict(c) for c in q]


def opciones_docentes_publicas() -> list[dict]:
    return [{"id": d["id"], "name": d["name"]} for d in opciones_docentes()]


def cola_contenidos() -> list[dict]:
    """contentQueue: pendientes y devueltos (flujo de validación)."""
    q = (
        Contenido.query.filter(Contenido.estado.in_(ESTADOS_COLA))
        .order_by(Contenido.id.asc())
        .all()
    )
    out = []
    for c in q:
        d = _contenido_dict(c)
        if c.observaciones:
            d["reviewNote"] = c.observaciones
        out.append(d)
    return out


def _meta_hall(h: HallFama) -> dict:
    """Biografía e insignias guardadas como JSON en ``observaciones``."""
    try:
        meta = json.loads(h.observaciones or "{}")
        return meta if isinstance(meta, dict) else {}
    except (TypeError, ValueError):
        return {}


def hall_fama() -> list[dict]:
    q = HallFama.query.order_by(HallFama.id.asc()).all()
    return [
        {"id": str(h.id), "name": h.nombre, "title": h.titulo, "year": h.anio,
         "achievement": h.logro, "image": h.imagen, "category": h.categoria,
         "bio": (_meta_hall(h).get("bio") or "").strip()}
        for h in q
    ]


def insignias() -> list[dict]:
    q = Insignia.query.order_by(Insignia.id.asc()).all()
    return [{"id": b.slug or str(b.id), "name": b.nombre, "icon": b.icono} for b in q]


def usuarios() -> list[dict]:
    out = []
    for u in Usuario.query.order_by(Usuario.id.asc()).all():
        contrib = (
            Contenido.query.filter(
                (Contenido.autor == u.nombre) | (Contenido.creador_id == u.id)
            )
            .count()
        )
        d = {
            "id": str(u.id),
            "name": u.nombre,
            "email": u.email,
            "role": u.rol,
            "status": u.estado,
            "joinDate": u.created_at.strftime("%Y-%m-%d") if u.created_at else None,
            "contributions": contrib,
            "points": u.puntos,
            "badgeIds": [
                ui.insignia.slug or str(ui.insignia_id)
                for ui in u.insignias
                if ui.insignia is not None
            ],
        }
        if u.semillero_id:
            d["researchGroupId"] = str(u.semillero_id)
        if u.anio_grado:
            d["graduationYear"] = u.anio_grado
        if u.cargo_actual:
            d["currentPosition"] = u.cargo_actual
        out.append(d)
    return out


def grupos_investigacion() -> list[dict]:
    out = []
    for s in Semillero.query.order_by(Semillero.id.asc()).all():
        miembros = Usuario.query.filter_by(semillero_id=s.id).count()
        out.append({
            "id": str(s.id),
            "name": s.nombre,
            "category": s.categoria,
            "lead": s.lider.nombre if s.lider else "Sin líder asignado",
            "members": miembros,
            "description": s.descripcion,
            "image": s.imagen,
        })
    return out


def logros() -> list[dict]:
    q = Premio.query.order_by(Premio.id.asc()).all()
    return [
        {"id": str(p.id), "title": p.nombre, "year": p.anio, "category": p.categoria,
         "institution": p.lugar, "description": p.descripcion, "image": p.imagen}
        for p in q
    ]


def kpis() -> dict:
    total = Contenido.query.count()
    publicados = Contenido.query.filter(Contenido.estado.in_(ESTADOS_PUBLICADOS)).count()
    pendientes = Contenido.query.filter(Contenido.estado == "pendiente").count()
    activos = Usuario.query.filter_by(estado="activo").count()
    hoy = datetime.now()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    nuevos_mes = Usuario.query.filter(Usuario.created_at >= inicio_mes).count()

    # Contenido publicado por colección (para la gráfica del panel admin).
    filas = (
        db.session.query(Coleccion.slug, Coleccion.titulo, func.count(Contenido.id))
        .outerjoin(
            Contenido,
            (Contenido.coleccion_id == Coleccion.id)
            & Contenido.estado.in_(ESTADOS_PUBLICADOS),
        )
        .group_by(Coleccion.id, Coleccion.slug, Coleccion.titulo)
        .order_by(Coleccion.id.asc())
        .all()
    )
    por_categoria = [
        {"id": slug, "label": titulo, "count": int(n),
         "pct": round(int(n) * 100 / publicados) if publicados else 0}
        for slug, titulo, n in filas
    ]
    return {
        "totalContent": total,
        "published": publicados,
        "pending": pendientes,
        "activeUsers": activos,
        "newThisMonth": nuevos_mes,
        "porCategoria": por_categoria,
    }


def etiquetas_populares(limite: int = 8) -> list[str]:
    """Etiquetas más usadas en contenido publicado (sugerencias de búsqueda)."""
    filas = (
        db.session.query(Etiqueta.nombre, func.count(ContenidoEtiqueta.contenido_id))
        .join(ContenidoEtiqueta, ContenidoEtiqueta.etiqueta_id == Etiqueta.id)
        .join(Contenido, Contenido.id == ContenidoEtiqueta.contenido_id)
        .filter(Contenido.estado.in_(ESTADOS_PUBLICADOS))
        .group_by(Etiqueta.id, Etiqueta.nombre)
        .order_by(func.count(ContenidoEtiqueta.contenido_id).desc())
        .limit(limite)
        .all()
    )
    return [nombre for nombre, _ in filas]


def opciones_docentes() -> list[dict]:
    q = Usuario.query.filter_by(rol="docente").order_by(Usuario.nombre.asc()).all()
    return [{"id": d.id, "name": d.nombre, "email": d.email} for d in q]


def dataset() -> dict:
    """Dataset completo del museo (contrato que consumen las vistas y el JS)."""
    return {
        "collections": colecciones(),
        "news": noticias(),
        "timeline": linea_tiempo(),
        "events": eventos(),
        "contentItems": contenidos(),
        "hallMembers": hall_fama(),
        "badges": insignias(),
        "users": usuarios(),
        "contentQueue": cola_contenidos(),
        "kpiData": kpis(),
        "researchGroups": grupos_investigacion(),
        "achievements": logros(),
        "teacherOptions": opciones_docentes(),
        "tags": etiquetas_populares(),
        "pointsPerLevel": POINTS_PER_LEVEL,
        "maxLevel": MAX_LEVEL,
    }


def usuarios_publicos() -> list[dict]:
    """Usuarios sin datos de contacto (para endpoints públicos)."""
    return [
        {clave: valor for clave, valor in u.items() if clave != "email"}
        for u in usuarios()
    ]


def dataset_publico() -> dict:
    """Dataset apto para el navegador: sin cola interna ni emails de usuarios."""
    d = dataset()
    d.pop("contentQueue", None)
    d["contentItems"] = [
        c for c in d.get("contentItems", []) if c.get("status") in ESTADOS_PUBLICADOS
    ]
    d["users"] = [
        {clave: valor for clave, valor in u.items() if clave != "email"}
        for u in d.get("users", [])
    ]
    d["teacherOptions"] = [
        {"id": t.get("id"), "name": t.get("name")}
        for t in d.get("teacherOptions", [])
    ]
    return d
