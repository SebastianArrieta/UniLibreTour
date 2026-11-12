import os


def _database_uri() -> str:
    uri = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://unilibretour:unilibretour@localhost:3306/unilibretour_db",
    )
    if uri.startswith("mysql://"):
        uri = uri.replace("mysql://", "mysql+pymysql://", 1)
    return uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SESSION_SECRET", "dev-secret"))

    # El token viaja en el header (peticiones de la API) y en una cookie
    # httpOnly (navegación a vistas protegidas renderizadas en el servidor).
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_ACCESS_COOKIE_NAME = "museo_session"
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "0") == "1"
    # Las mutaciones de la API usan Bearer; la cookie solo interviene en
    # navegación GET. Con CSRF activo, una petición maliciosa cross-site que
    # viaje solo con cookie es rechazada (el frontend usa el header Bearer).
    JWT_COOKIE_CSRF_PROTECT = True

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    # Duración del token de sesión en segundos (por defecto 1 hora).
    # Se puede ajustar con JWT_ACCESS_TOKEN_EXPIRES en el entorno.
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))

    # Eco del código 2FA en la respuesta: SOLO para desarrollo local sin
    # servidor de correo. Nunca se aplica en producción (ver ProductionConfig).
    OTP_DEV_ECHO = os.getenv("OTP_DEV_ECHO", "0") == "1"

    # Correo saliente (código 2FA). Si MAIL_SERVER no está definido, el 2FA se
    # omite con un aviso en el log para no bloquear el acceso.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME", ""))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "0") == "1"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    OTP_DEV_ECHO = False
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "1") == "1"

    @staticmethod
    def validar() -> None:
        """Aborta el arranque si faltan secretos reales."""
        inseguros = {"", "dev-secret", "toursecretkey", "cambia-esto", "cambiar-por-un-secreto-seguro"}
        faltan = [
            nombre for nombre in ("SECRET_KEY", "JWT_SECRET_KEY")
            if (os.getenv(nombre) or "").strip() in inseguros
        ]
        if faltan:
            raise RuntimeError(
                "Configuración de producción insegura: define "
                + ", ".join(faltan)
                + " en el entorno con valores largos y aleatorios."
            )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
