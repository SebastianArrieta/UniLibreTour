"""Blueprint Web — Vistas principales de la aplicación UniLibreTour.

Sirve las vistas públicas, de autenticación y los paneles de rol
(estudiante, docente, administrador) conectadas a la base de datos real
a través del servicio app.services.museo (con respaldo de datos estáticos).
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.extensions import db
from app.middleware.auth import web_role_required
from app.models.contenido import Contenido
from app.models.usuario import Usuario
from app.services import contenido as contenido_svc
from app.services import museo
from app.services import notificacion as notificacion_svc

web_bp = Blueprint("web", __name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "static" / "data" / "demo-data.json"


@lru_cache(maxsize=1)
def _dataset_estatico() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def dataset_actual() -> dict:
    """Dataset desde la BD; fallback al JSON si no hay datos o falla la consulta."""
    try:
        d = museo.dataset()
        if not museo.dataset_vacio(d):
            return d
    except Exception:
        pass
    return _dataset_estatico()


def _ctx(page: str, **extra) -> dict:
    d = dataset_actual()
    base = {
        "current_page": page,
        "datos": d,
        "contentItems": d.get("contentItems", []),
        "contentQueue": d.get("contentQueue", []),
        "news": d.get("news", []),
        "collections": d.get("collections", []),
        "timeline": d.get("timeline", []),
        "events": d.get("events", []),
        "hallMembers": d.get("hallMembers", []),
        "badges": d.get("badges", []),
        "users": d.get("users", []),
        "kpiData": d.get("kpiData", {}),
        "researchGroups": d.get("researchGroups", []),
        "achievements": d.get("achievements", []),
        "teacherOptions": d.get("teacherOptions", []),
        "pointsPerLevel": d.get("pointsPerLevel", 500),
        "maxLevel": d.get("maxLevel", 20),
    }
    base.update(extra)
    return base


def _item(cid: str) -> dict:
    for item in dataset_actual().get("contentItems", []):
        if str(item.get("id")) == str(cid):
            return item
    abort(404)


def _usuario_actual() -> Usuario | None:
    """Usuario autenticado por la cookie de sesión (el guard ya validó el JWT)."""
    identidad = get_jwt_identity()
    if identidad is None:
        return None
    return db.session.get(Usuario, int(identidad))


# -----------------------------------------------------------------------------
# Vistas Públicas
# -----------------------------------------------------------------------------
@web_bp.get("/")
def home():
    return render_template("publico/home.html", **_ctx("home"))


@web_bp.get("/explorar")
def explorar():
    return render_template("publico/explorar.html", **_ctx("explorar"))


@web_bp.get("/buscar")
def buscar():
    return render_template("publico/buscar.html", **_ctx("buscar"))


@web_bp.get("/detalle/<cid>")
def detalle(cid):
    return render_template("publico/detalle.html", **_ctx("detalle", item=_item(cid)))


@web_bp.get("/hall-fama")
def hall_fama():
    return render_template("publico/hall_fama.html", **_ctx("hall-fama"))


@web_bp.get("/semilleros")
def semilleros():
    return render_template("publico/semilleros.html", **_ctx("semilleros"))


@web_bp.get("/calendario")
def calendario():
    return render_template("publico/calendario.html", **_ctx("calendario"))


@web_bp.get("/cronologia")
def cronologia():
    return render_template("publico/cronologia.html", **_ctx("cronologia"))


@web_bp.get("/ranking")
def ranking():
    return render_template("publico/ranking.html", **_ctx("ranking"))


@web_bp.get("/perfil")
@web_role_required()
def perfil():
    return render_template("publico/perfil.html", **_ctx("perfil"))


@web_bp.get("/egresado")
def egresado():
    return render_template("publico/egresado.html", **_ctx("egresado"))


# -----------------------------------------------------------------------------
# Vistas de Autenticación
# -----------------------------------------------------------------------------
@web_bp.get("/login")
def login():
    return render_template("auth/login.html", **_ctx("login"))


@web_bp.get("/2fa")
def two_fa():
    return render_template("auth/2fa.html", **_ctx("2fa"))


@web_bp.get("/registro")
def registro():
    return render_template("auth/registro.html", **_ctx("registro"))


# -----------------------------------------------------------------------------
# Panel Estudiante
# -----------------------------------------------------------------------------
@web_bp.get("/mi-espacio")
@web_role_required()
def mi_espacio():
    """Enlace neutro al panel principal: cada rol va a su propio dashboard."""
    claims = get_jwt()
    destinos = {"egresado": "web.egresado", "docente": "web.docente", "admin": "web.admin"}
    return redirect(url_for(destinos.get(claims.get("rol"), "web.estudiante")))


@web_bp.get("/estudiante")
@web_role_required("estudiante", "admin")
def estudiante():
    return render_template("estudiante/dashboard.html", **_ctx("est-dashboard"))


@web_bp.get("/estudiante/aportes")
@web_role_required("estudiante", "egresado", "admin")
def estudiante_aportes():
    return render_template("estudiante/aportes.html", **_ctx("est-aportes"))


@web_bp.get("/estudiante/favoritos")
@web_role_required("estudiante", "egresado", "admin")
def estudiante_favoritos():
    return render_template("estudiante/favoritos.html", **_ctx("est-favoritos"))


@web_bp.get("/estudiante/contribuir")
@web_role_required("estudiante", "egresado", "admin")
def estudiante_contribuir():
    return render_template("estudiante/contribuir.html", **_ctx("est-contribuir"))


# -----------------------------------------------------------------------------
# Panel Docente
# -----------------------------------------------------------------------------
@web_bp.get("/docente")
@web_role_required("docente", "admin")
def docente():
    usuario = _usuario_actual()
    revision = contenido_svc.en_revision_para(usuario.id) if usuario and usuario.rol == "docente" else []
    estadisticas = {
        "contribuciones": Contenido.query.filter_by(creador_id=usuario.id).count() if usuario else 0,
        "publicadas": Contenido.query.filter_by(creador_id=usuario.id, estado="publicado").count() if usuario else 0,
    }
    notifs = notificacion_svc.listar(usuario.id) if usuario else []
    mis_aportes = (
        Contenido.query.filter_by(creador_id=usuario.id).order_by(Contenido.id.desc()).all()
        if usuario else []
    )
    return render_template(
        "docente/dashboard.html",
        docente_usuario=usuario,
        revision_items=revision,
        mis_aportes=mis_aportes,
        estadisticas=estadisticas,
        notifs=notifs[:5],
        notifs_sin_leer=sum(1 for n in notifs if not n.leido),
        **_ctx("doc-dashboard"),
    )


@web_bp.get("/docente/revision")
@web_role_required("docente", "admin")
def docente_revision():
    usuario = _usuario_actual()
    if usuario and usuario.rol == "admin":
        items = (
            Contenido.query.filter_by(estado=contenido_svc.ESTADO_REVISION_DOCENTE)
            .order_by(Contenido.id.desc())
            .all()
        )
    elif usuario:
        items = contenido_svc.en_revision_para(usuario.id)
    else:
        items = []
    return render_template("docente/revision.html", items=items, **_ctx("doc-revision"))


@web_bp.get("/docente/registrar-evidencia")
@web_role_required("docente", "admin")
def docente_evidencia():
    return render_template("docente/evidencia.html", **_ctx("doc-wizard"))


@web_bp.get("/docente/notificaciones")
@web_role_required("docente", "admin")
def docente_notificaciones():
    return render_template("docente/notificaciones.html", **_ctx("doc-notificaciones"))


# -----------------------------------------------------------------------------
# Panel Administrador
# -----------------------------------------------------------------------------
@web_bp.get("/admin")
@web_role_required("admin")
def admin():
    return render_template("admin/dashboard.html", **_ctx("admin-dashboard"))


@web_bp.get("/admin/anadir")
@web_role_required("admin")
def admin_anadir():
    return render_template("admin/anadir.html", **_ctx("admin-anadir"))


@web_bp.get("/admin/usuarios")
@web_role_required("admin")
def admin_usuarios():
    return render_template("admin/usuarios.html", **_ctx("admin-usuarios"))


@web_bp.get("/admin/cola")
@web_role_required("admin")
def admin_cola():
    return render_template("admin/cola.html", **_ctx("admin-cola"))


@web_bp.get("/admin/validacion/<iid>")
@web_role_required("admin")
def admin_validacion(iid):
    item = next((i for i in dataset_actual().get("contentQueue", []) if str(i.get("id")) == str(iid)), None)
    if item is None:
        abort(404)
    return render_template("admin/validacion.html", **_ctx("admin-validacion", item=item))


@web_bp.get("/admin/confirmacion/<iid>")
@web_role_required("admin")
def admin_confirmacion(iid):
    item = next((i for i in dataset_actual().get("contentItems", []) if str(i.get("id")) == str(iid)), None)
    if item is None:
        abort(404)
    return render_template("admin/confirmacion.html", **_ctx("admin-confirmacion", item=item))


@web_bp.get("/admin/registros")
@web_role_required("admin")
def admin_registros():
    return render_template("admin/registros.html", **_ctx("admin-registros"))


@web_bp.get("/admin/hall-registro")
@web_role_required("admin")
def admin_hall_registro():
    return render_template("admin/hall_registro.html", **_ctx("admin-hall-registro"))
