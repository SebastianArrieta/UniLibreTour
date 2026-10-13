"""Blueprint Web — Vistas principales de la aplicación UniLibreTour.

Sirve las vistas públicas, de autenticación y los paneles de rol
(estudiante, docente, administrador) conectadas a la base de datos real
a través del servicio app.services.museo (con respaldo de datos estáticos).
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template

from app.services import museo

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
        "collection_count": len(d.get("collections", [])),
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
        "demoAccounts": d.get("demoAccounts", []),
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


# -----------------------------------------------------------------------------
# Endpoints de datos
# -----------------------------------------------------------------------------
@web_bp.get("/api/demo-data")
@web_bp.get("/api/museo-data")
def demo_data_endpoint():
    return jsonify(dataset_actual())


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
@web_bp.get("/estudiante")
def estudiante():
    return render_template("estudiante/dashboard.html", **_ctx("est-dashboard"))


@web_bp.get("/estudiante/aportes")
def estudiante_aportes():
    return render_template("estudiante/aportes.html", **_ctx("est-aportes"))


@web_bp.get("/estudiante/favoritos")
def estudiante_favoritos():
    return render_template("estudiante/favoritos.html", **_ctx("est-favoritos"))


@web_bp.get("/estudiante/contribuir")
def estudiante_contribuir():
    return render_template("estudiante/contribuir.html", **_ctx("est-contribuir"))


# -----------------------------------------------------------------------------
# Panel Docente
# -----------------------------------------------------------------------------
@web_bp.get("/docente")
def docente():
    return render_template("docente/dashboard.html", **_ctx("doc-dashboard"))


@web_bp.get("/docente/registrar-evidencia")
def docente_evidencia():
    return render_template("docente/evidencia.html", **_ctx("doc-wizard"))


@web_bp.get("/docente/notificaciones")
def docente_notificaciones():
    return render_template("docente/notificaciones.html", **_ctx("doc-notificaciones"))


# -----------------------------------------------------------------------------
# Panel Administrador
# -----------------------------------------------------------------------------
@web_bp.get("/admin")
def admin():
    return render_template("admin/dashboard.html", **_ctx("admin-dashboard"))


@web_bp.get("/admin/anadir")
def admin_anadir():
    return render_template("admin/anadir.html", **_ctx("admin-anadir"))


@web_bp.get("/admin/usuarios")
def admin_usuarios():
    return render_template("admin/usuarios.html", **_ctx("admin-usuarios"))


@web_bp.get("/admin/cola")
def admin_cola():
    return render_template("admin/cola.html", **_ctx("admin-cola"))


@web_bp.get("/admin/validacion/<iid>")
def admin_validacion(iid):
    item = next((i for i in dataset_actual().get("contentQueue", []) if str(i.get("id")) == str(iid)), None)
    if item is None:
        abort(404)
    return render_template("admin/validacion.html", **_ctx("admin-validacion", item=item))


@web_bp.get("/admin/confirmacion/<iid>")
def admin_confirmacion(iid):
    item = next((i for i in dataset_actual().get("contentItems", []) if str(i.get("id")) == str(iid)), None)
    if item is None:
        abort(404)
    return render_template("admin/confirmacion.html", **_ctx("admin-confirmacion", item=item))


@web_bp.get("/admin/registros")
def admin_registros():
    return render_template("admin/registros.html", **_ctx("admin-registros"))


@web_bp.get("/admin/hall-registro")
def admin_hall_registro():
    return render_template("admin/hall_registro.html", **_ctx("admin-hall-registro"))
