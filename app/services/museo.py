"""Servicio de lectura del Museo — integra y expone el dataset institucional desde la BD.

Cada función consulta las tablas reales y devuelve dicts estructurados
con las entidades del museo (colecciones, noticias, cronología, eventos,
investigación, insignias y aportes).
"""

from __future__ import annotations

from app.models.contenido import Coleccion, Contenido
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

# KPIs que aún no tienen tabla de origen (visitas requiere módulo de analítica)
_KPI_ESTATICOS = {
    "visitors": 24780,
    "newThisMonth": 47,
    "monthlyVisits": [
        {"month": "Ene", "visits": 1820},
        {"month": "Feb", "visits": 2140},
        {"month": "Mar", "visits": 1980},
        {"month": "Abr", "visits": 2560},
        {"month": "May", "visits": 3100},
        {"month": "Jun", "visits": 2890},
        {"month": "Jul", "visits": 3340},
    ],
}

# Cuentas que se muestran en la pantalla de login (credenciales sembradas en BD)
_DEMO_ACCOUNTS = [
    {"email": "estudiante@unilibre.edu.co", "password": "123456", "role": "estudiante", "label": "Estudiante"},
    {"email": "docente@unilibre.edu.co", "password": "123456", "role": "docente", "label": "Docente"},
    {"email": "admin@unilibre.edu.co", "password": "123456", "role": "admin", "label": "Admin"},
    {"email": "egresado@unilibre.edu.co", "password": "123456", "role": "egresado", "label": "Egresado"},
]


def colecciones() -> list[dict]:
    out = []
    for c in Coleccion.query.order_by(Coleccion.id.asc()).all():
        out.append({
            "id": c.slug or str(c.id),
            "title": c.titulo,
            "description": c.descripcion,
            "count": len(c.contenidos),
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
    return d


def contenidos() -> list[dict]:
    """contentItems: todo el contenido que no fue devuelto por validación."""
    q = (
        Contenido.query.filter(Contenido.estado != "devuelto")
        .order_by(Contenido.id.asc())
        .all()
    )
    return [_contenido_dict(c) for c in q]


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


def hall_fama() -> list[dict]:
    q = HallFama.query.order_by(HallFama.id.asc()).all()
    return [
        {"id": str(h.id), "name": h.nombre, "title": h.titulo, "year": h.anio,
         "achievement": h.logro, "image": h.imagen, "category": h.categoria}
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
    return {
        "totalContent": total,
        "published": publicados,
        "pending": pendientes,
        "activeUsers": activos,
        **_KPI_ESTATICOS,
    }


def opciones_docentes() -> list[dict]:
    q = Usuario.query.filter_by(rol="docente").order_by(Usuario.nombre.asc()).all()
    return [{"name": d.nombre, "email": d.email} for d in q]


def cuentas_demo() -> list[dict]:
    return [dict(a) for a in _DEMO_ACCOUNTS]


def dataset() -> dict:
    """Dataset completo con el mismo contrato que demo-data.json."""
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
        "demoAccounts": cuentas_demo(),
        "pointsPerLevel": POINTS_PER_LEVEL,
        "maxLevel": MAX_LEVEL,
    }


def dataset_vacio(d: dict) -> bool:
    return not d.get("collections") and not d.get("contentItems")
