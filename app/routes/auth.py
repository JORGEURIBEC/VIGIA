from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app import db
from app.models import Usuario, RecuperacionPassword
from app.services.email_service import EmailService


# ============================================================
# BLUEPRINT DE AUTENTICACIÓN
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtener_fecha_utc():
    """
    Obtiene la fecha y hora actual en UTC sin zona horaria
    para mantener compatibilidad con DATETIME de MySQL.
    """

    return datetime.now(
        timezone.utc
    ).replace(tzinfo=None)


def generar_hash_token(token):
    """
    Genera un hash SHA-256 del token de recuperación.

    El token original nunca se almacena en la base de datos.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ============================================================
# LOGIN
# ============================================================

@auth_bp.post("/login")
def login():
    """
    Autentica a un usuario mediante correo y contraseña.

    Si las credenciales son correctas:
    - verifica que la cuenta esté activa;
    - actualiza la fecha del último acceso;
    - genera un token JWT;
    - incorpora el rol del usuario en el token.
    """

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar los datos en formato JSON."
        }), 400

    correo = str(
        datos.get("correo", "")
    ).strip().lower()

    password = str(
        datos.get("password", "")
    )

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
        # Buscar usuario
        # ----------------------------------------------------

        usuario = Usuario.query.filter_by(
            correo=correo
        ).first()

        # ----------------------------------------------------
        # Validar credenciales
        # ----------------------------------------------------

        if (
            not usuario
            or not usuario.verificar_password(password)
        ):
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
                "mensaje": (
                    "El usuario no tiene un rol válido asignado."
                )
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

        usuario.ultimo_acceso = obtener_fecha_utc()

        db.session.commit()

        # ----------------------------------------------------
        # Respuesta
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
            "mensaje": (
                "No fue posible completar la autenticación."
            )
        }), 500


# ============================================================
# PERFIL DEL USUARIO AUTENTICADO
# ============================================================

@auth_bp.get("/me")
@jwt_required()
def perfil_actual():
    """
    Valida el JWT y devuelve los datos del usuario
    actualmente autenticado.
    """

    try:

        # ----------------------------------------------------
        # Obtener ID del usuario autenticado
        # ----------------------------------------------------

        usuario_id = get_jwt_identity()

        # ----------------------------------------------------
        # Obtener información adicional del JWT
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
        # Validar estado de la cuenta
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
            "mensaje": (
                "No fue posible consultar el usuario autenticado."
            )
        }), 500


# ============================================================
# SOLICITAR RECUPERACIÓN DE CONTRASEÑA
# ============================================================

@auth_bp.post("/recuperar-password")
def recuperar_password():
    """
    Genera un token criptográficamente seguro para permitir
    la recuperación de una contraseña.

    En la base de datos solamente se almacena el hash SHA-256
    del token y nunca el token original.

    El token original es enviado al correo electrónico
    registrado del usuario mediante el servicio SMTP de VIGIA.
    """

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar los datos en formato JSON."
        }), 400

    correo = str(
        datos.get("correo", "")
    ).strip().lower()

    if not correo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El correo es obligatorio."
        }), 400

    try:

        # ----------------------------------------------------
        # Buscar usuario
        # ----------------------------------------------------

        usuario = Usuario.query.filter_by(
            correo=correo
        ).first()

        # ----------------------------------------------------
        # Mensaje genérico
        #
        # Evita revelar si una cuenta existe o no.
        # ----------------------------------------------------

        mensaje_generico = (
            "Si el correo se encuentra registrado y activo, "
            "se generarán las instrucciones de recuperación."
        )

        # ----------------------------------------------------
        # No revelar existencia o estado de una cuenta
        # ----------------------------------------------------

        if not usuario or not usuario.estado:
            return jsonify({
                "estado": "OK",
                "mensaje": mensaje_generico
            }), 200

        # ----------------------------------------------------
        # Invalidar tokens anteriores sin utilizar
        # ----------------------------------------------------

        solicitudes_anteriores = (
            RecuperacionPassword.query
            .filter(
                RecuperacionPassword.id_usuario
                == usuario.id_usuario,
                RecuperacionPassword.utilizado.is_(False)
            )
            .all()
        )

        for solicitud in solicitudes_anteriores:
            solicitud.utilizado = True

        # ----------------------------------------------------
        # Crear token criptográficamente seguro
        # ----------------------------------------------------

        token = secrets.token_urlsafe(48)

        # ----------------------------------------------------
        # Generar hash SHA-256
        # ----------------------------------------------------

        token_hash = generar_hash_token(token)

        # ----------------------------------------------------
        # Calcular expiración
        # ----------------------------------------------------

        ahora = obtener_fecha_utc()

        minutos = current_app.config.get(
            "RECOVERY_TOKEN_TTL_MINUTES",
            30
        )

        fecha_expiracion = (
            ahora + timedelta(minutes=minutos)
        )

        # ----------------------------------------------------
        # Registrar solicitud de recuperación
        # ----------------------------------------------------

        recuperacion = RecuperacionPassword(
            id_usuario=usuario.id_usuario,
            token_hash=token_hash,
            fecha_expiracion=fecha_expiracion,
            utilizado=False
        )

        db.session.add(recuperacion)

        # ----------------------------------------------------
        # Guardar solicitud en la base de datos
        # ----------------------------------------------------

        db.session.commit()

        # ----------------------------------------------------
        # Enviar token mediante correo electrónico
        # ----------------------------------------------------

        try:

            EmailService.enviar_recuperacion_password(
                destinatario=usuario.correo,
                nombre_usuario=(
                    f"{usuario.nombre} "
                    f"{usuario.apellido}"
                ).strip(),
                token=token,
                minutos_expiracion=minutos
            )

        except Exception:

            # ------------------------------------------------
            # Si el correo no pudo enviarse, el token generado
            # queda invalidado para evitar que permanezca activo.
            # ------------------------------------------------

            recuperacion.utilizado = True
            db.session.commit()

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible enviar las instrucciones "
                    "de recuperación por correo electrónico."
                )
            }), 500

        # ----------------------------------------------------
        # Preparar respuesta
        # ----------------------------------------------------

        respuesta = {
            "estado": "OK",
            "mensaje": mensaje_generico,
            "expira_en_minutos": minutos
        }

        # ----------------------------------------------------
        # SOLO PARA DESARROLLO
        #
        # Mientras se realizan las pruebas se puede mostrar
        # temporalmente el token en la respuesta.
        #
        # Para la versión final:
        # RECOVERY_DEBUG_TOKEN=false
        # ----------------------------------------------------

        if current_app.config.get(
            "RECOVERY_DEBUG_TOKEN",
            False
        ):
            respuesta["token_recuperacion"] = token

        return jsonify(respuesta), 200

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible procesar "
                "la recuperación de contraseña."
            )
        }), 500


# ============================================================
# RESTABLECER CONTRASEÑA
# ============================================================

@auth_bp.post("/restablecer-password")
def restablecer_password():
    """
    Valida un token de recuperación y permite establecer
    una nueva contraseña.
    """

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar los datos en formato JSON."
        }), 400

    token = str(
        datos.get("token", "")
    ).strip()

    nueva_password = str(
        datos.get("nueva_password", "")
    )

    # --------------------------------------------------------
    # Validar token
    # --------------------------------------------------------

    if not token:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El token de recuperación es obligatorio."
            )
        }), 400

    # --------------------------------------------------------
    # Validar contraseña
    # --------------------------------------------------------

    if not nueva_password:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "La nueva contraseña es obligatoria."
        }), 400

    if len(nueva_password) < 8:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La contraseña debe contener "
                "al menos 8 caracteres."
            )
        }), 400

    try:

        # ----------------------------------------------------
        # Convertir token recibido a SHA-256
        # ----------------------------------------------------

        token_hash = generar_hash_token(token)

        # ----------------------------------------------------
        # Buscar token almacenado
        # ----------------------------------------------------

        recuperacion = (
            RecuperacionPassword.query
            .filter_by(
                token_hash=token_hash
            )
            .first()
        )

        if not recuperacion:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El token de recuperación no es válido."
                )
            }), 400

        # ----------------------------------------------------
        # Verificar si el token ya fue utilizado
        # ----------------------------------------------------

        if recuperacion.utilizado:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El token de recuperación "
                    "ya fue utilizado."
                )
            }), 400

        # ----------------------------------------------------
        # Verificar expiración
        # ----------------------------------------------------

        ahora = obtener_fecha_utc()

        if recuperacion.fecha_expiracion < ahora:

            recuperacion.utilizado = True

            db.session.commit()

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El token de recuperación ha expirado."
                )
            }), 400

        # ----------------------------------------------------
        # Obtener usuario asociado
        # ----------------------------------------------------

        usuario = db.session.get(
            Usuario,
            recuperacion.id_usuario
        )

        if not usuario:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Usuario no encontrado."
            }), 404

        # ----------------------------------------------------
        # Verificar que la cuenta continúe activa
        # ----------------------------------------------------

        if not usuario.estado:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "La cuenta se encuentra desactivada."
            }), 403

        # ----------------------------------------------------
        # Establecer nueva contraseña
        #
        # Utiliza establecer_password() del modelo Usuario,
        # por lo que se almacena mediante hash seguro.
        # ----------------------------------------------------

        usuario.establecer_password(
            nueva_password
        )

        # ----------------------------------------------------
        # Marcar token actual como utilizado
        # ----------------------------------------------------

        recuperacion.utilizado = True

        # ----------------------------------------------------
        # Invalidar cualquier otro token pendiente
        # ----------------------------------------------------

        otras_solicitudes = (
            RecuperacionPassword.query
            .filter(
                RecuperacionPassword.id_usuario
                == usuario.id_usuario,
                RecuperacionPassword.utilizado.is_(False),
                RecuperacionPassword.id_recuperacion
                != recuperacion.id_recuperacion
            )
            .all()
        )

        for solicitud in otras_solicitudes:
            solicitud.utilizado = True

        # ----------------------------------------------------
        # Guardar cambios
        # ----------------------------------------------------

        db.session.commit()

        # ----------------------------------------------------
        # Respuesta exitosa
        # ----------------------------------------------------

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "La contraseña fue restablecida "
                "correctamente."
            )
        }), 200

    except ValueError as error:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": str(error)
        }), 400

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible restablecer "
                "la contraseña."
            )
        }), 500