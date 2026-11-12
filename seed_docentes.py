"""Seed de docentes para UniLibreTour.

Uso (con los contenedores levantados):
    docker compose cp seed_docentes.py server:/app/seed_docentes.py
    docker compose exec server python seed_docentes.py

Es idempotente: si el email ya existe, actualiza nombre, rol y estado
(sin tocar la contraseña de la cuenta); si no existe, lo crea con la
contraseña temporal DOCENTE_PASSWORD. Las contraseñas se guardan con el
mismo hash de Werkzeug que usa la aplicación.
"""

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.services.auth import hash_password

# Contraseña temporal para las cuentas nuevas. Cámbiala si este seed se
# ejecuta en un entorno real.
DOCENTE_PASSWORD = "docente123"

DOCENTES = [
    ("Adalberto Álvarez Martínez", "adalberto.alvarez@unilibre.edu.co"),
    ("Alexander Elías Parody Muñoz", "alexander.parody@unilibre.edu.co"),
    ("Andrea Coronado Echeverri", "andrea.coronado@unilibre.edu.co"),
    ("Anibal Verbel Castellar", "anibal.verbel@unilibre.edu.co"),
    ("Arnaldo Arce Peña", "arnaldo.arce@unilibre.edu.co"),
    ("Astrid Isidora Barrios Barraza", "astrid.barrios@unilibre.edu.co"),
    ("Augusto César De Arco Chiquillo", "augusto.dearco@unilibre.edu.co"),
    ("Boris Martín Arias Cabrera", "boris.arias@unilibre.edu.co"),
    ("Carlos Arturo Consuegra Ospino", "carlos.consuegra@unilibre.edu.co"),
    ("Dairon Jesús Torrado Castro", "dairon.torrado@unilibre.edu.co"),
    ("Danna Vanessa Betancourt Martínez", "danna.betancourt@unilibre.edu.co"),
    ("David Ovallos", "david.ovallos@unilibre.edu.co"),
    ("Deiber Enrique Puello Cabarcas", "deiber.puello@unilibre.edu.co"),
    ("Diana Milena Suárez López", "diana.suarez@unilibre.edu.co"),
    ("Diego Fernando Suero Pérez", "diego.suero@unilibre.edu.co"),
    ("Edgar Morillo Vergel", "edgar.morillo@unilibre.edu.co"),
    ("Edgardo Manuel Buelvas Castro", "edgardo.buelvas@unilibre.edu.co"),
    ("Eduardo Antonio Espinosa Fuentes", "eduardo.espinosa@unilibre.edu.co"),
    ("Emeldo Rogelio Caballero Brochado", "emeldo.caballero@unilibre.edu.co"),
    ("Emiro Berrío Rodríguez", "emiro.berrio@unilibre.edu.co"),
    ("Erick Jassir Ufre", "erick.ufre@unilibre.edu.co"),
    ("Franklin Enrique Barrios Barraza", "franklin.barrios@unilibre.edu.co"),
    ("Hernando Javier Peña Mercado", "hernando.pena@unilibre.edu.co"),
    ("Ingrid Helga Erika Steffanell De León", "ingrid.steffanell@unilibre.edu.co"),
    ("Iván Enrique Quintero Hoyos", "ivan.quintero@unilibre.edu.co"),
    ("Janeth Rozo Nader", "janeth.rozo@unilibre.edu.co"),
    ("José William Penagos Vargas", "jose.penagos@unilibre.edu.co"),
    ("Juan Carlos Carrasco Garcia", "juan.carrasco@unilibre.edu.co"),
    ("Juan Carlos Velilla Arrieta", "juan.velilla@unilibre.edu.co"),
    ("Luis Carlos Acosta Fontalvo", "luis.acosta@unilibre.edu.co"),
    ("Manlio Calderón", "manlio.calderon@unilibre.edu.co"),
    ("Martha Milagro del Carmen Arteta Charris", "martha.arteta@unilibre.edu.co"),
    ("Marvin Enrique Molina Cárdenas", "marvin.molina@unilibre.edu.co"),
    ("Medardo Virgilio González Conde", "medardo.gonzalez@unilibre.edu.co"),
    ("Obeth Hernán Romero Ocampo", "obeth.romero@unilibre.edu.co"),
    ("Patty Pedroza Barrios", "patty.pedroza@unilibre.edu.co"),
    ("Paul Adolfo Sanmartín Mendoza", "paul.sanmartin@unilibre.edu.co"),
    ("Ricardo Antonio De La Hoz Lara", "ricardo.delahoz@unilibre.edu.co"),
    ("Roberto Carlos Osio Ospino", "roberto.osio@unilibre.edu.co"),
    ("Saúl Olivos Aarón", "saul.olivos@unilibre.edu.co"),
    ("William Ricardo Insignares Conde", "william.insignares@unilibre.edu.co"),
    ("Yessy Lorena Coronel Montaguth", "yessy.coronel@unilibre.edu.co"),
]


def main() -> None:
    app = create_app()
    with app.app_context():
        creados = 0
        actualizados = 0
        for nombre, email in DOCENTES:
            email = email.strip().lower()
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario is None:
                usuario = Usuario(
                    nombre=nombre,
                    email=email,
                    password_hash=hash_password(DOCENTE_PASSWORD),
                    rol="docente",
                    estado="activo",
                )
                db.session.add(usuario)
                creados += 1
                print(f"[creado]      {email}")
            else:
                cambio_permisos = usuario.rol != "docente" or usuario.estado != "activo"
                usuario.nombre = nombre
                usuario.rol = "docente"
                usuario.estado = "activo"
                if cambio_permisos:
                    usuario.token_version = (usuario.token_version or 0) + 1
                actualizados += 1
                print(f"[actualizado] {email}")
        db.session.commit()
        print(f"\nListo: {creados} creados, {actualizados} actualizados.")
        print(f"Contraseña temporal de las cuentas nuevas: {DOCENTE_PASSWORD}")


if __name__ == "__main__":
    main()
