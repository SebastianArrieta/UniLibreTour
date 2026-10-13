"""Utilidad de desarrollo: reinicia el esquema y siembra el dataset demo.

Uso:  python reset_demo.py
¡Destruye TODOS los datos! Solo para entorno de desarrollo.
"""

from sqlalchemy import text

from app import create_app
from app.extensions import db


def _dropar_tablas() -> None:
    """DROP manual (con FK checks apagados): evita el ciclo usuarios↔semilleros."""
    engine = db.engine
    with engine.connect() as conn:
        tablas = [r[0] for r in conn.execute(text("SHOW TABLES"))]
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for t in tablas:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()


def main() -> None:
    app = create_app()
    with app.app_context():
        print("→ Eliminando esquema existente…")
        _dropar_tablas()
        print("→ Creando esquema actualizado…")
        db.create_all()

        from app.services.usuario import seed_usuarios
        from app.services.seed_demo import seed_desde_demo

        seed_usuarios()
        sembrado = seed_desde_demo()
        print(f"→ Siembra demo: {'OK' if sembrado else 'omitida (ya había datos)'}")

        from sqlalchemy import func, select

        from app.models.contenido import Coleccion, Contenido
        from app.models.cronologia import CronologiaHito, Evento
        from app.models.premio import Premio
        from app.models.publicacion import HallFama, Noticia
        from app.models.semillero import Semillero
        from app.models.usuario import Usuario

        for modelo in (
            Usuario, Coleccion, Contenido, Semillero, Noticia,
            CronologiaHito, Evento, HallFama, Premio,
        ):
            n = db.session.scalar(select(func.count()).select_from(modelo))
            print(f"   {modelo.__tablename__}: {n}")


if __name__ == "__main__":
    main()
