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
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hora

    # Sembrar datos demo (cuentas con contraseña conocida). Desactivado por
    # defecto en producción; activar explícitamente con SEED_DEMO=1.
    SEED_DEMO = os.getenv("SEED_DEMO", "1") == "1"

    # Sin servidor de correo configurado: en desarrollo se devuelve el código
    # 2FA en la respuesta para poder probar el flujo. Apagarlo en producción.
    OTP_DEV_ECHO = os.getenv("OTP_DEV_ECHO", "1") == "1"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # No sembrar credenciales de demostración en producción salvo petición explícita.
    SEED_DEMO = os.getenv("SEED_DEMO", "0") == "1"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
