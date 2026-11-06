"""Cuentas de demostración: única fuente de verdad.

Tanto el sembrador de usuarios como el del dataset demo leen de aquí, de modo
que nunca vuelven a aparecer credenciales contradictorias. Son cuentas de
demostración con contraseña conocida: en producción los seeds se desactivan
por defecto (``SEED_DEMO`` en la configuración).
"""

PASSWORD_DEMO = "123456"

CUENTAS_DEMO = [
    {"email": "estudiante@unilibre.edu.co", "password": PASSWORD_DEMO, "rol": "estudiante", "etiqueta": "Estudiante"},
    {"email": "docente@unilibre.edu.co", "password": PASSWORD_DEMO, "rol": "docente", "etiqueta": "Docente"},
    {"email": "admin@unilibre.edu.co", "password": PASSWORD_DEMO, "rol": "admin", "etiqueta": "Admin"},
    {"email": "egresado@unilibre.edu.co", "password": PASSWORD_DEMO, "rol": "egresado", "etiqueta": "Egresado"},
]
