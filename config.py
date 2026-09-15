import os

from datetime import timedelta
from urllib.parse import quote_plus

from dotenv import load_dotenv


# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

load_dotenv()


# ============================================================
# DIRECTORIO BASE DEL PROYECTO
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)


# ============================================================
# FUNCIÓN AUXILIAR PARA VARIABLES BOOLEANAS
# ============================================================

def env_bool(nombre, valor_por_defecto=False):
    """
    Convierte una variable de entorno a booleano.

    Valores considerados verdaderos:
    true, 1, yes, si, sí, on
    """

    valor = os.getenv(nombre)

    if valor is None:
        return valor_por_defecto

    return valor.strip().lower() in {
        "true",
        "1",
        "yes",
        "si",
        "sí",
        "on",
    }


# ============================================================
# CONFIGURACIÓN GENERAL DE VIGIA
# ============================================================

class Config:

    # ========================================================
    # SEGURIDAD GENERAL
    # ========================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "clave-desarrollo"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "jwt-desarrollo"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=30
    )

    # ========================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ========================================================

    RECOVERY_TOKEN_TTL_MINUTES = int(
        os.getenv(
            "RECOVERY_TOKEN_TTL_MINUTES",
            "30"
        )
    )

    RECOVERY_DEBUG_TOKEN = env_bool(
        "RECOVERY_DEBUG_TOKEN",
        True
    )

    # ========================================================
    # CONFIGURACIÓN DE CORREO SMTP
    # ========================================================

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        ""
    )

    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            "587"
        )
    )

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        ""
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD",
        ""
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME
    )

    MAIL_USE_TLS = env_bool(
        "MAIL_USE_TLS",
        True
    )

    # ========================================================
    # BASE DE DATOS MYSQL / AIVEN
    # ========================================================

    DB_HOST = os.getenv(
        "DB_HOST",
        "localhost"
    )

    DB_PORT = os.getenv(
        "DB_PORT",
        "3306"
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "vigia"
    )

    DB_USER = os.getenv(
        "DB_USER",
        ""
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        ""
    )

    DB_SSL_CA = os.getenv(
        "DB_SSL_CA",
        ""
    )

    # ========================================================
    # URI DE SQLALCHEMY
    # ========================================================

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{quote_plus(DB_USER)}:"
        f"{quote_plus(DB_PASSWORD)}@"
        f"{DB_HOST}:"
        f"{DB_PORT}/"
        f"{DB_NAME}"
        f"?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ========================================================
    # CONFIGURACIÓN DEL MOTOR SQLALCHEMY
    # ========================================================

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # ========================================================
    # SSL DE AIVEN
    # ========================================================

    if DB_SSL_CA:

        ssl_ca_path = (
            DB_SSL_CA
            if os.path.isabs(DB_SSL_CA)
            else os.path.join(
                BASE_DIR,
                DB_SSL_CA
            )
        )

        SQLALCHEMY_ENGINE_OPTIONS[
            "connect_args"
        ] = {
            "ssl": {
                "ca": ssl_ca_path
            }
        }