from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app import db
from app.models import Usuario


# ============================================================
# BLUEPRINT DE AUTENTICACIÓN
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)


# ============================================================
# LOGIN
# ============================================================

@auth_bp.post("/login")
def login():
    """
    Autentica a un usuario mediante correo y contraseña.

    Si las credenciales son correctas:
    - verifica que la cuenta se encuentre activa;
    - actualiza la fecha del último acceso;
    - genera un token JWT;
    - incorpora el rol del usuario dentro del token.
    """

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar los datos en formato JSON."
        }), 400

    correo = str(datos.get("correo", "")).strip().lower()
    password = str(datos.get("password", ""))

    # --------------------------------------------------------
    # Validar campos obligatorios
    # --------------------------------------------------------

    if not correo or not password:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Correo y contraseña son obligatorios."
        }), 400

    try:
        # ----------------------------------------------------
        # Buscar usuario por correo
        # ----------------------------------------------------

        usuario = Usuario.query.filter_by(correo=correo).first()

        # ----------------------------------------------------
        # Validar usuario y contraseña
        # ----------------------------------------------------

        if not usuario or not usuario.verificar_password(password):
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Credenciales inválidas."
            }), 401

        # ----------------------------------------------------
        # Validar estado de la cuenta
        # ----------------------------------------------------

        if not usuario.estado:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "La cuenta se encuentra desactivada."
            }), 403

        # ----------------------------------------------------
        # Obtener rol
        # ----------------------------------------------------

        nombre_rol = (
            usuario.rol.nombre_rol
            if usuario.rol
            else None
        )

        if not nombre_rol:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "El usuario no tiene un rol válido asignado."
            }), 403

        # ----------------------------------------------------
        # Generar token JWT
        # ----------------------------------------------------

        access_token = create_access_token(
            identity=str(usuario.id_usuario),
            additional_claims={
                "rol": nombre_rol
            }
        )

        # ----------------------------------------------------
        # Registrar último acceso
        # ----------------------------------------------------

        usuario.ultimo_acceso = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

        db.session.commit()

        # ----------------------------------------------------
        # Respuesta exitosa
        # ----------------------------------------------------

        return jsonify({
            "estado": "OK",
            "mensaje": "Autenticación correcta.",
            "access_token": access_token,
            "usuario": usuario.to_dict()
        }), 200

    except Exception:
        db.session.rollback()
    

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible completar la autenticación."
        }), 500


# ============================================================
# PERFIL DEL USUARIO AUTENTICADO
# ============================================================

@auth_bp.get("/me")
@jwt_required()
def perfil_actual():
    """
    Valida el token JWT recibido y devuelve los datos
    del usuario actualmente autenticado.
    """

    try:
        # ----------------------------------------------------
        # Obtener ID almacenado en el JWT
        # ----------------------------------------------------

        usuario_id = get_jwt_identity()

        # ----------------------------------------------------
        # Obtener claims adicionales del token
        # ----------------------------------------------------

        claims = get_jwt()

        # ----------------------------------------------------
        # Buscar usuario
        # ----------------------------------------------------

        usuario = db.session.get(
            Usuario,
            int(usuario_id)
        )

        if not usuario:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Usuario no encontrado."
            }), 404

        # ----------------------------------------------------
        # Verificar que continúe activo
        # ----------------------------------------------------

        if not usuario.estado:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "La cuenta se encuentra desactivada."
            }), 403

        # ----------------------------------------------------
        # Respuesta
        # ----------------------------------------------------

        return jsonify({
            "estado": "OK",
            "mensaje": "Token JWT válido.",
            "usuario": usuario.to_dict(),
            "rol_token": claims.get("rol")
        }), 200

    except (TypeError, ValueError):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Identificador de usuario inválido."
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible consultar el usuario autenticado."
        }), 500