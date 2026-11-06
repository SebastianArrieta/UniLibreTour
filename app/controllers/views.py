from flask import Blueprint, render_template

from app.middleware.auth import web_role_required
from app.services.usuario import listar_usuarios

views_bp = Blueprint("views", __name__)


@views_bp.get("/usuarios")
@web_role_required("admin")
def usuarios():
    try:
        lista_usuarios = listar_usuarios()
    except Exception:
        lista_usuarios = []
    return render_template("usuarios.html", usuarios=lista_usuarios)
