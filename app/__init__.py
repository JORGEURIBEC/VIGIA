# ============================================================
# VIGIA
# Plataforma Web de Monitoreo, Análisis y Gestión
# de Eventos de Seguridad Informática
#
# Archivo:
# app/__init__.py
# ============================================================

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from config import Config


# ============================================================
# EXTENSIONES
# ============================================================

db = SQLAlchemy()
jwt = JWTManager()


# ============================================================
# FACTORY DE LA APLICACIÓN
# ============================================================

def create_app():

    # --------------------------------------------------------
    # Crear aplicación Flask
    # --------------------------------------------------------

    app = Flask(__name__)

    # --------------------------------------------------------
    # Cargar configuración
    # --------------------------------------------------------

    app.config.from_object(Config)

    # Permite mostrar correctamente tildes,
    # ñ y otros caracteres especiales en JSON
    app.json.ensure_ascii = False

    # --------------------------------------------------------
    # Inicializar extensiones
    # --------------------------------------------------------

    db.init_app(app)
    jwt.init_app(app)

    # ========================================================
    # IMPORTAR BLUEPRINTS
    # ========================================================

    from app.routes import (
        roles_bp,
        auth_bp,
        usuarios_bp,
        fuentes_bp,
        reglas_bp,
        tipos_eventos_bp,
        eventos_bp,
        alertas_bp,
        incidentes_bp,
        dashboard_bp,
        auditoria_bp,
        web_bp
    )

    # ========================================================
    # REGISTRAR BLUEPRINTS
    # ========================================================

    app.register_blueprint(roles_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(fuentes_bp)
    app.register_blueprint(reglas_bp)
    app.register_blueprint(tipos_eventos_bp)
    app.register_blueprint(eventos_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(incidentes_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auditoria_bp)

    # Interfaz gráfica web de VIGIA
    app.register_blueprint(web_bp)

    # ========================================================
    # INFORMACIÓN GENERAL DE LA API
    # ========================================================
    #
    # IMPORTANTE:
    # La ruta "/" queda reservada para la interfaz web.
    #
    # Por eso el estado general de la API ahora se encuentra en:
    #
    # http://127.0.0.1:5000/api/v1
    #
    # ========================================================

    @app.get("/api/v1")
    def estado_api():

        return jsonify({
            "aplicacion": "VIGIA",
            "descripcion": (
                "Plataforma Web de Monitoreo, Análisis y Gestión "
                "de Eventos de Seguridad Informática"
            ),
            "estado": "API funcionando correctamente",
            "version": "v1"
        }), 200

    # ========================================================
    # HEALTH CHECK DE BASE DE DATOS
    # ========================================================

    @app.get("/api/v1/health/db")
    def verificar_base_datos():

        try:

            # ------------------------------------------------
            # Verificar conexión con MySQL
            # ------------------------------------------------

            db.session.execute(
                text("SELECT 1")
            )

            # ------------------------------------------------
            # Obtener cantidad de tablas de la BD actual
            # ------------------------------------------------

            total_tablas = db.session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                """)
            ).scalar()

            return jsonify({
                "estado": "OK",
                "mensaje": "Conexión con la base de datos correcta.",
                "base_datos": "vigia",
                "total_tablas": total_tablas
            }), 200

        except Exception as e:

            # Limpiar cualquier transacción pendiente
            db.session.rollback()

            return jsonify({
                "estado": "ERROR",
                "mensaje": "No fue posible conectar con la base de datos.",
                "detalle": str(e)
            }), 500

    # ========================================================
    # MANEJO DE ERRORES JWT
    # ========================================================

    @jwt.expired_token_loader
    def token_expirado(jwt_header, jwt_payload):

        return jsonify({
            "msg": "Token has expired"
        }), 401

    @jwt.invalid_token_loader
    def token_invalido(error):

        return jsonify({
            "msg": "Invalid token"
        }), 422

    @jwt.unauthorized_loader
    def token_faltante(error):

        return jsonify({
            "msg": "Missing Authorization Header"
        }), 401

    # ========================================================
    # RETORNAR APLICACIÓN
    # ========================================================

    return app