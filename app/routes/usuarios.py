import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import Usuario, Rol
from app.decorators import roles_required
from app.services.auditoria_service import registrar_auditoria


# ============================================================
# BLUEPRINT DE USUARIOS
# ============================================================

usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/api/v1/usuarios"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def normalizar_correo(valor):
    return normalizar_texto(valor).lower()


def correo_valido(correo):
    return bool(EMAIL_REGEX.fullmatch(correo or ""))


def obtener_id_usuario_actual():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def contar_administradores_activos():
    return (
        Usuario.query
        .join(Rol, Usuario.id_rol == Rol.id_rol)
        .filter(
            Rol.nombre_rol == "ADMINISTRADOR",
            Usuario.estado.is_(True)
        )
        .count()
    )


def es_administrador(usuario):
    return bool(
        usuario
        and usuario.rol
        and usuario.rol.nombre_rol == "ADMINISTRADOR"
    )


def validar_longitudes(nombre, apellido, correo):
    if len(nombre) > 80:
        return "El nombre no puede superar los 80 caracteres."

    if len(apellido) > 80:
        return "El apellido no puede superar los 80 caracteres."

    if len(correo) > 150:
        return "El correo no puede superar los 150 caracteres."

    return None


# ============================================================
# GET - LISTAR TODOS LOS USUARIOS
# ============================================================

@usuarios_bp.get("")
@roles_required("ADMINISTRADOR")
def listar_usuarios():
    """
    Lista todos los usuarios registrados en VIGIA.
    Acceso exclusivo para ADMINISTRADOR.
    """

    try:
        usuarios = (
            Usuario.query
            .order_by(Usuario.id_usuario.asc())
            .all()
        )

        return jsonify({
            "estado": "OK",
            "total": len(usuarios),
            "data": [
                usuario.to_dict()
                for usuario in usuarios
            ]
        }), 200

    except Exception as error:
        print(
            "ERROR AL LISTAR USUARIOS:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error al consultar los usuarios."
        }), 500


# ============================================================
# GET - OBTENER USUARIO POR ID
# ============================================================

@usuarios_bp.get("/<int:id_usuario>")
@roles_required("ADMINISTRADOR")
def obtener_usuario(id_usuario):
    """
    Obtiene la información de un usuario específico.
    Acceso exclusivo para ADMINISTRADOR.
    """

    try:
        usuario = db.session.get(
            Usuario,
            id_usuario
        )

        if usuario is None:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Usuario no encontrado."
            }), 404

        return jsonify({
            "estado": "OK",
            "data": usuario.to_dict()
        }), 200

    except Exception as error:
        print(
            "ERROR AL OBTENER USUARIO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error al consultar el usuario."
        }), 500


# ============================================================
# POST - CREAR NUEVO USUARIO
# ============================================================

@usuarios_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_usuario():
    """
    Registra un nuevo usuario en VIGIA.
    Acceso exclusivo para ADMINISTRADOR.
    """

    datos = request.get_json(silent=True) or {}

    nombre = normalizar_texto(
        datos.get("nombre")
    )

    apellido = normalizar_texto(
        datos.get("apellido")
    )

    correo = normalizar_correo(
        datos.get("correo")
    )

    password = str(
        datos.get("password", "")
    )

    id_rol = datos.get("id_rol")

    # --------------------------------------------------------
    # CAMPOS OBLIGATORIOS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # LONGITUD Y FORMATO
    # --------------------------------------------------------

    error_longitud = validar_longitudes(
        nombre,
        apellido,
        correo
    )

    if error_longitud:
        return jsonify({
            "estado": "ERROR",
            "mensaje": error_longitud
        }), 400

    if not correo_valido(correo):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El correo electrónico no posee un formato válido."
        }), 400

    if len(password) < 8:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La contraseña debe contener "
                "al menos 8 caracteres."
            )
        }), 400

    # --------------------------------------------------------
    # ROL
    # --------------------------------------------------------

    try:
        id_rol = int(id_rol)
    except (TypeError, ValueError):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El identificador del rol no es válido."
        }), 400

    rol = db.session.get(
        Rol,
        id_rol
    )

    if rol is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El rol indicado no existe."
        }), 400

    # --------------------------------------------------------
    # CORREO DUPLICADO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CREAR Y AUDITAR
    # --------------------------------------------------------

    try:
        usuario = Usuario(
            id_rol=rol.id_rol,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            estado=True
        )

        usuario.establecer_password(
            password
        )

        db.session.add(usuario)
        db.session.flush()

        auditoria_registrada = registrar_auditoria(
            accion="CREAR_USUARIO",
            entidad_afectada="USUARIO",
            id_registro_afectado=usuario.id_usuario,
            resultado="OK",
            detalle=(
                f"Se creó el usuario '{usuario.correo}' "
                f"con ID {usuario.id_usuario} y rol "
                f"'{rol.nombre_rol}'."
            ),
            confirmar=False
        )

        if not auditoria_registrada:
            db.session.rollback()
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la creación."
                )
            }), 500

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Usuario creado correctamente.",
            "data": usuario.to_dict()
        }), 201

    except ValueError as error:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": str(error)
        }), 400

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL CREAR USUARIO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error al crear el usuario."
        }), 500


# ============================================================
# PUT - ACTUALIZAR USUARIO
# ============================================================

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

    usuario = db.session.get(
        Usuario,
        id_usuario
    )

    if usuario is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Usuario no encontrado."
        }), 404

    datos = request.get_json(
        silent=True
    ) or {}

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe proporcionar datos para actualizar."
        }), 400

    id_usuario_actual = obtener_id_usuario_actual()

    estado_anterior = bool(
        usuario.estado
    )

    rol_anterior = (
        usuario.rol.nombre_rol
        if usuario.rol
        else None
    )

    valores_anteriores = {
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "correo": usuario.correo,
        "id_rol": usuario.id_rol,
        "rol": rol_anterior,
        "estado": estado_anterior
    }

    password_actualizada = False

    try:
        # ----------------------------------------------------
        # NOMBRE
        # ----------------------------------------------------

        if "nombre" in datos:
            nombre = normalizar_texto(
                datos.get("nombre")
            )

            if not nombre:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El nombre no puede estar vacío."
                }), 400

            if len(nombre) > 80:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El nombre no puede superar "
                        "los 80 caracteres."
                    )
                }), 400

            usuario.nombre = nombre

        # ----------------------------------------------------
        # APELLIDO
        # ----------------------------------------------------

        if "apellido" in datos:
            apellido = normalizar_texto(
                datos.get("apellido")
            )

            if not apellido:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El apellido no puede estar vacío."
                }), 400

            if len(apellido) > 80:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El apellido no puede superar "
                        "los 80 caracteres."
                    )
                }), 400

            usuario.apellido = apellido

        # ----------------------------------------------------
        # CORREO
        # ----------------------------------------------------

        if "correo" in datos:
            correo = normalizar_correo(
                datos.get("correo")
            )

            if not correo:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El correo no puede estar vacío."
                }), 400

            if len(correo) > 150:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El correo no puede superar "
                        "los 150 caracteres."
                    )
                }), 400

            if not correo_valido(correo):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El correo electrónico no posee "
                        "un formato válido."
                    )
                }), 400

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

        # ----------------------------------------------------
        # ROL
        # ----------------------------------------------------

        if "id_rol" in datos:
            try:
                id_rol_nuevo = int(
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

            rol_nuevo = db.session.get(
                Rol,
                id_rol_nuevo
            )

            if rol_nuevo is None:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El rol indicado no existe."
                }), 400

            if (
                id_usuario_actual == usuario.id_usuario
                and rol_nuevo.nombre_rol != "ADMINISTRADOR"
            ):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El Administrador autenticado no puede "
                        "retirar su propio rol administrativo."
                    )
                }), 409

            if (
                es_administrador(usuario)
                and rol_nuevo.nombre_rol != "ADMINISTRADOR"
                and usuario.estado
                and contar_administradores_activos() <= 1
            ):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "No es posible retirar el rol al último "
                        "Administrador activo del sistema."
                    )
                }), 409

            usuario.id_rol = rol_nuevo.id_rol
            usuario.rol = rol_nuevo

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        if "estado" in datos:
            estado_nuevo = datos["estado"]

            if not isinstance(estado_nuevo, bool):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El estado debe enviarse "
                        "como true o false."
                    )
                }), 400

            if (
                id_usuario_actual == usuario.id_usuario
                and estado_nuevo is False
            ):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El Administrador autenticado no puede "
                        "desactivar su propia cuenta."
                    )
                }), 409

            if (
                usuario.estado is True
                and estado_nuevo is False
                and es_administrador(usuario)
                and contar_administradores_activos() <= 1
            ):
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "No es posible desactivar al último "
                        "Administrador activo del sistema."
                    )
                }), 409

            usuario.estado = estado_nuevo

        # ----------------------------------------------------
        # CONTRASEÑA
        # ----------------------------------------------------

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

            usuario.establecer_password(
                password
            )

            password_actualizada = True

        # ----------------------------------------------------
        # DETERMINAR ACCIÓN DE AUDITORÍA
        # ----------------------------------------------------

        estado_nuevo = bool(
            usuario.estado
        )

        if (
            estado_anterior is False
            and estado_nuevo is True
        ):
            accion_auditoria = "ACTIVAR_USUARIO"

        elif (
            estado_anterior is True
            and estado_nuevo is False
        ):
            accion_auditoria = "DESACTIVAR_USUARIO"

        else:
            accion_auditoria = "ACTUALIZAR_USUARIO"

        # ----------------------------------------------------
        # DETALLE DE CAMBIOS
        # ----------------------------------------------------

        cambios = []

        if valores_anteriores["nombre"] != usuario.nombre:
            cambios.append(
                f"nombre: '{valores_anteriores['nombre']}' "
                f"-> '{usuario.nombre}'"
            )

        if valores_anteriores["apellido"] != usuario.apellido:
            cambios.append(
                f"apellido: '{valores_anteriores['apellido']}' "
                f"-> '{usuario.apellido}'"
            )

        if valores_anteriores["correo"] != usuario.correo:
            cambios.append(
                f"correo: '{valores_anteriores['correo']}' "
                f"-> '{usuario.correo}'"
            )

        rol_nuevo_nombre = (
            usuario.rol.nombre_rol
            if usuario.rol
            else None
        )

        if valores_anteriores["id_rol"] != usuario.id_rol:
            cambios.append(
                f"rol: '{valores_anteriores['rol']}' "
                f"-> '{rol_nuevo_nombre}'"
            )

        if valores_anteriores["estado"] != bool(usuario.estado):
            cambios.append(
                f"estado: {valores_anteriores['estado']} "
                f"-> {bool(usuario.estado)}"
            )

        if password_actualizada:
            cambios.append(
                "contraseña: actualizada"
            )

        if not cambios:
            db.session.rollback()
            return jsonify({
                "estado": "OK",
                "mensaje": "No se detectaron cambios efectivos en el usuario.",
                "data": usuario.to_dict()
            }), 200

        detalle_cambios = "; ".join(cambios)

        db.session.flush()

        auditoria_registrada = registrar_auditoria(
            accion=accion_auditoria,
            entidad_afectada="USUARIO",
            id_registro_afectado=id_usuario,
            resultado="OK",
            detalle=(
                f"Usuario {id_usuario} actualizado. "
                f"{detalle_cambios}"
            ),
            confirmar=False
        )

        if not auditoria_registrada:
            db.session.rollback()
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la actualización."
                )
            }), 500

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Usuario actualizado correctamente.",
            "data": usuario.to_dict()
        }), 200

    except ValueError as error:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": str(error)
        }), 400

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR USUARIO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "el usuario."
            )
        }), 500


# ============================================================
# DELETE - DESACTIVAR USUARIO
# ============================================================

@usuarios_bp.delete("/<int:id_usuario>")
@roles_required("ADMINISTRADOR")
def desactivar_usuario(id_usuario):
    """
    Desactiva lógicamente un usuario de VIGIA.

    El registro no se elimina físicamente.
    Acceso exclusivo para ADMINISTRADOR.
    """

    usuario = db.session.get(
        Usuario,
        id_usuario
    )

    if usuario is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Usuario no encontrado."
        }), 404

    if not usuario.estado:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El usuario ya se encuentra desactivado."
        }), 409

    id_usuario_actual = obtener_id_usuario_actual()

    if id_usuario_actual == usuario.id_usuario:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El Administrador autenticado no puede "
                "desactivar su propia cuenta."
            )
        }), 409

    if (
        es_administrador(usuario)
        and contar_administradores_activos() <= 1
    ):
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No es posible desactivar al último "
                "Administrador activo del sistema."
            )
        }), 409

    try:
        usuario.estado = False
        db.session.flush()

        auditoria_registrada = registrar_auditoria(
            accion="DESACTIVAR_USUARIO",
            entidad_afectada="USUARIO",
            id_registro_afectado=id_usuario,
            resultado="OK",
            detalle=(
                f"Se desactivó el usuario "
                f"'{usuario.correo}' con ID {id_usuario}."
            ),
            confirmar=False
        )

        if not auditoria_registrada:
            db.session.rollback()
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la desactivación."
                )
            }), 500

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Usuario desactivado correctamente.",
            "data": usuario.to_dict()
        }), 200

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL DESACTIVAR USUARIO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible desactivar el usuario."
        }), 500
