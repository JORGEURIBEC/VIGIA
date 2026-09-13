from flask import Blueprint, jsonify, request

from app import db
from app.models import Usuario, Rol
from app.decorators import roles_required


# ==========================================================
# BLUEPRINT DE USUARIOS
# ==========================================================

usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/api/v1/usuarios"
)


# ==========================================================
# GET - LISTAR TODOS LOS USUARIOS
# ==========================================================

@usuarios_bp.get("")
@roles_required("ADMINISTRADOR")
def listar_usuarios():
    """
    Lista todos los usuarios registrados en VIGIA.

    Acceso exclusivo para ADMINISTRADOR.
    """

    usuarios = Usuario.query.order_by(
        Usuario.id_usuario
    ).all()

    return jsonify({
        "estado": "OK",
        "total": len(usuarios),
        "data": [
            usuario.to_dict()
            for usuario in usuarios
        ]
    }), 200


# ==========================================================
# GET - OBTENER USUARIO POR ID
# ==========================================================

@usuarios_bp.get("/<int:id_usuario>")
@roles_required("ADMINISTRADOR")
def obtener_usuario(id_usuario):
    """
    Obtiene la información de un usuario específico
    mediante su identificador.

    Acceso exclusivo para ADMINISTRADOR.
    """

    usuario = Usuario.query.filter_by(
        id_usuario=id_usuario
    ).first()

    if not usuario:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Usuario no encontrado."
        }), 404

    return jsonify({
        "estado": "OK",
        "data": usuario.to_dict()
    }), 200


# ==========================================================
# POST - CREAR NUEVO USUARIO
# ==========================================================

@usuarios_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_usuario():
    """
    Registra un nuevo usuario en VIGIA.

    Acceso exclusivo para ADMINISTRADOR.
    """

    datos = request.get_json(silent=True) or {}

    # ------------------------------------------------------
    # Obtener y normalizar datos
    # ------------------------------------------------------

    nombre = str(
        datos.get("nombre", "")
    ).strip()

    apellido = str(
        datos.get("apellido", "")
    ).strip()

    correo = str(
        datos.get("correo", "")
    ).strip().lower()

    password = str(
        datos.get("password", "")
    )

    id_rol = datos.get("id_rol")

    # ------------------------------------------------------
    # Validar campos obligatorios
    # ------------------------------------------------------

    if not nombre:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El nombre es obligatorio."
        }), 400

    if not apellido:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El apellido es obligatorio."
        }), 400

    if not correo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El correo es obligatorio."
        }), 400

    if not password:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "La contraseña es obligatoria."
        }), 400

    if id_rol is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El rol es obligatorio."
        }), 400

    # ------------------------------------------------------
    # Validar longitud mínima de contraseña
    # ------------------------------------------------------

    if len(password) < 8:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La contraseña debe contener "
                "al menos 8 caracteres."
            )
        }), 400

    # ------------------------------------------------------
    # Validar identificador del rol
    # ------------------------------------------------------

    try:
        id_rol = int(id_rol)

    except (TypeError, ValueError):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El identificador del rol no es válido."
        }), 400

    # ------------------------------------------------------
    # Verificar existencia del rol
    # ------------------------------------------------------

    rol = Rol.query.filter_by(
        id_rol=id_rol
    ).first()

    if not rol:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El rol indicado no existe."
        }), 400

    # ------------------------------------------------------
    # Verificar correo duplicado
    # ------------------------------------------------------

    usuario_existente = Usuario.query.filter_by(
        correo=correo
    ).first()

    if usuario_existente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe un usuario registrado "
                "con ese correo."
            )
        }), 409

    # ------------------------------------------------------
    # Crear usuario
    # ------------------------------------------------------

    try:

        usuario = Usuario(
            id_rol=rol.id_rol,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            estado=True
        )

        # La contraseña nunca se almacena en texto plano.
        usuario.establecer_password(password)

        db.session.add(usuario)
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Usuario creado correctamente.",
            "data": usuario.to_dict()
        }), 201

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al crear el usuario."
            )
        }), 500


# ==========================================================
# PUT - ACTUALIZAR USUARIO
# ==========================================================

@usuarios_bp.put("/<int:id_usuario>")
@roles_required("ADMINISTRADOR")
def actualizar_usuario(id_usuario):
    """
    Actualiza la información de un usuario existente.

    Permite modificar:
    - nombre
    - apellido
    - correo
    - rol
    - estado
    - contraseña

    Acceso exclusivo para ADMINISTRADOR.
    """

    # ------------------------------------------------------
    # Buscar usuario
    # ------------------------------------------------------

    usuario = Usuario.query.filter_by(
        id_usuario=id_usuario
    ).first()

    if not usuario:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Usuario no encontrado."
        }), 404

    # ------------------------------------------------------
    # Obtener JSON enviado
    # ------------------------------------------------------

    datos = request.get_json(silent=True) or {}

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Debe proporcionar datos para actualizar."
            )
        }), 400

    try:

        # ==================================================
        # NOMBRE
        # ==================================================

        if "nombre" in datos:

            nombre = str(
                datos.get("nombre", "")
            ).strip()

            if not nombre:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El nombre no puede estar vacío."
                    )
                }), 400

            usuario.nombre = nombre

        # ==================================================
        # APELLIDO
        # ==================================================

        if "apellido" in datos:

            apellido = str(
                datos.get("apellido", "")
            ).strip()

            if not apellido:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El apellido no puede estar vacío."
                    )
                }), 400

            usuario.apellido = apellido

        # ==================================================
        # CORREO
        # ==================================================

        if "correo" in datos:

            correo = str(
                datos.get("correo", "")
            ).strip().lower()

            if not correo:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El correo no puede estar vacío."
                    )
                }), 400

            # Verifica que el nuevo correo no esté siendo
            # utilizado por otro usuario.
            correo_existente = Usuario.query.filter(
                Usuario.correo == correo,
                Usuario.id_usuario != id_usuario
            ).first()

            if correo_existente:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "Ya existe otro usuario registrado "
                        "con ese correo."
                    )
                }), 409

            usuario.correo = correo

        # ==================================================
        # ROL
        # ==================================================

        if "id_rol" in datos:

            try:
                id_rol = int(
                    datos["id_rol"]
                )

            except (TypeError, ValueError):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El identificador del rol "
                        "no es válido."
                    )
                }), 400

            rol = Rol.query.filter_by(
                id_rol=id_rol
            ).first()

            if not rol:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El rol indicado no existe."
                    )
                }), 400

            usuario.id_rol = rol.id_rol

        # ==================================================
        # ESTADO
        # ==================================================

        if "estado" in datos:

            estado = datos["estado"]

            if not isinstance(estado, bool):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El estado debe enviarse "
                        "como true o false."
                    )
                }), 400

            usuario.estado = estado

        # ==================================================
        # CONTRASEÑA
        # ==================================================

        if "password" in datos:

            password = str(
                datos.get("password", "")
            )

            if len(password) < 8:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "La contraseña debe contener "
                        "al menos 8 caracteres."
                    )
                }), 400

            # Genera nuevamente un hash seguro.
            usuario.establecer_password(password)

        # ==================================================
        # GUARDAR CAMBIOS
        # ==================================================

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Usuario actualizado correctamente."
            ),
            "data": usuario.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "el usuario."
            )
        }), 500


    # ============================================================
# DESACTIVAR USUARIO
# ============================================================

@usuarios_bp.delete("/<int:id_usuario>")
@roles_required("ADMINISTRADOR")
def desactivar_usuario(id_usuario):
    """
    Desactiva lógicamente un usuario de VIGIA.

    El registro no se elimina físicamente de la base de datos.
    Únicamente se modifica su estado a False.

    Acceso exclusivo para ADMINISTRADOR.
    """

    usuario = Usuario.query.filter_by(
        id_usuario=id_usuario
    ).first()

    # --------------------------------------------------------
    # Validar existencia
    # --------------------------------------------------------

    if not usuario:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Usuario no encontrado."
        }), 404

    # --------------------------------------------------------
    # Evitar desactivación repetida
    # --------------------------------------------------------

    if not usuario.estado:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El usuario ya se encuentra desactivado."
        }), 409

    try:
        # ----------------------------------------------------
        # Desactivación lógica
        # ----------------------------------------------------

        usuario.estado = False

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Usuario desactivado correctamente.",
            "data": usuario.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible desactivar el usuario."
        }), 500