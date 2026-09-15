from flask import Blueprint, jsonify, request

from app import db
from app.models import FuenteEvento
from app.decorators import roles_required
from app.services.auditoria_service import registrar_auditoria


# ============================================================
# BLUEPRINT DE FUENTES DE EVENTOS
# ============================================================

fuentes_bp = Blueprint(
    "fuentes",
    __name__,
    url_prefix="/api/v1/fuentes"
)


# ============================================================
# LISTAR FUENTES DE EVENTOS
# ADMINISTRADOR / ANALISTA
# ============================================================

@fuentes_bp.get("")
@roles_required("ADMINISTRADOR", "ANALISTA")
def listar_fuentes():
    """
    Lista todas las fuentes de eventos registradas en VIGIA.
    """

    try:

        fuentes = (
            FuenteEvento.query
            .order_by(
                FuenteEvento.id_fuente.asc()
            )
            .all()
        )

        return jsonify({
            "estado": "OK",
            "total": len(fuentes),
            "data": [
                fuente.to_dict()
                for fuente in fuentes
            ]
        }), 200

    except Exception as error:

        print(
            "ERROR AL LISTAR FUENTES:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "las fuentes de eventos."
            ),
            "detalle": str(error)
        }), 500


# ============================================================
# OBTENER FUENTE POR ID
# ADMINISTRADOR / ANALISTA
# ============================================================

@fuentes_bp.get("/<int:id_fuente>")
@roles_required("ADMINISTRADOR", "ANALISTA")
def obtener_fuente(id_fuente):
    """
    Obtiene una fuente de eventos específica mediante su ID.
    """

    try:

        fuente = db.session.get(
            FuenteEvento,
            id_fuente
        )

        if fuente is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje":
                    "Fuente de eventos no encontrada."
            }), 404

        return jsonify({
            "estado": "OK",
            "data": fuente.to_dict()
        }), 200

    except Exception as error:

        print(
            "ERROR AL OBTENER FUENTE:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "la fuente de eventos."
            ),
            "detalle": str(error)
        }), 500


# ============================================================
# CREAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ============================================================

@fuentes_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_fuente():
    """
    Crea una nueva fuente de eventos de seguridad.
    """

    datos = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # OBTENER CAMPOS
    # --------------------------------------------------------

    nombre = str(
        datos.get(
            "nombre",
            ""
        )
    ).strip()

    tipo_fuente = str(
        datos.get(
            "tipo_fuente",
            ""
        )
    ).strip()

    descripcion = datos.get(
        "descripcion"
    )

    # --------------------------------------------------------
    # VALIDAR CAMPOS OBLIGATORIOS
    # --------------------------------------------------------

    if not nombre:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "El nombre de la fuente es obligatorio."
        }), 400

    if not tipo_fuente:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "El tipo de fuente es obligatorio."
        }), 400

    # --------------------------------------------------------
    # VALIDAR LONGITUDES
    # --------------------------------------------------------

    if len(nombre) > 100:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El nombre de la fuente no puede superar "
                "los 100 caracteres."
            )
        }), 400

    if len(tipo_fuente) > 100:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El tipo de fuente no puede superar "
                "los 100 caracteres."
            )
        }), 400

    if descripcion is not None:

        descripcion = str(
            descripcion
        ).strip()

        if len(descripcion) > 255:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La descripción no puede superar "
                    "los 255 caracteres."
                )
            }), 400

        if not descripcion:
            descripcion = None

    # --------------------------------------------------------
    # VERIFICAR NOMBRE DUPLICADO
    # --------------------------------------------------------

    existente = (
        FuenteEvento.query
        .filter_by(
            nombre=nombre
        )
        .first()
    )

    if existente is not None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe una fuente de eventos "
                "registrada con ese nombre."
            )
        }), 409

    try:

        # ----------------------------------------------------
        # CREAR FUENTE
        # ----------------------------------------------------

        fuente = FuenteEvento(
            nombre=nombre,
            tipo_fuente=tipo_fuente,
            descripcion=descripcion,
            estado=True
        )

        db.session.add(
            fuente
        )

        # Permite obtener id_fuente antes del commit.
        db.session.flush()

        # ----------------------------------------------------
        # AUDITORÍA
        # ----------------------------------------------------

        auditoria_registrada = registrar_auditoria(
            accion="CREAR_FUENTE",
            entidad_afectada="FUENTE_EVENTO",
            id_registro_afectado=fuente.id_fuente,
            resultado="OK",
            detalle=(
                f"Se creó la fuente de eventos "
                f"'{fuente.nombre}' "
                f"con ID {fuente.id_fuente}."
            )
        )

        if not auditoria_registrada:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la creación."
                )
            }), 500

        # registrar_auditoria() realiza el commit
        # de la misma sesión.

        return jsonify({
            "estado": "OK",
            "mensaje":
                "Fuente de eventos creada correctamente.",
            "data": fuente.to_dict()
        }), 201

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL CREAR FUENTE:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al crear "
                "la fuente de eventos."
            ),
            "detalle": str(error)
        }), 500


# ============================================================
# ACTUALIZAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ============================================================

@fuentes_bp.put("/<int:id_fuente>")
@roles_required("ADMINISTRADOR")
def actualizar_fuente(id_fuente):
    """
    Actualiza una fuente de eventos existente.

    Permite modificar:
    - nombre
    - tipo_fuente
    - descripcion
    - estado
    """

    fuente = db.session.get(
        FuenteEvento,
        id_fuente
    )

    if fuente is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "Fuente de eventos no encontrada."
        }), 404

    datos = request.get_json(
        silent=True
    ) or {}

    if not datos:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "No se recibieron datos para actualizar."
        }), 400

    # --------------------------------------------------------
    # GUARDAR VALORES ANTERIORES
    # --------------------------------------------------------

    nombre_anterior = fuente.nombre
    tipo_anterior = fuente.tipo_fuente
    descripcion_anterior = fuente.descripcion
    estado_anterior = bool(
        fuente.estado
    )

    # --------------------------------------------------------
    # NOMBRE
    # --------------------------------------------------------

    if "nombre" in datos:

        nombre = str(
            datos.get(
                "nombre",
                ""
            )
        ).strip()

        if not nombre:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre de la fuente "
                    "no puede estar vacío."
                )
            }), 400

        if len(nombre) > 100:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre de la fuente no puede "
                    "superar los 100 caracteres."
                )
            }), 400

        existente = (
            FuenteEvento.query
            .filter(
                FuenteEvento.nombre == nombre,
                FuenteEvento.id_fuente != id_fuente
            )
            .first()
        )

        if existente is not None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Ya existe otra fuente de eventos "
                    "registrada con ese nombre."
                )
            }), 409

        fuente.nombre = nombre

    # --------------------------------------------------------
    # TIPO DE FUENTE
    # --------------------------------------------------------

    if "tipo_fuente" in datos:

        tipo_fuente = str(
            datos.get(
                "tipo_fuente",
                ""
            )
        ).strip()

        if not tipo_fuente:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El tipo de fuente "
                    "no puede estar vacío."
                )
            }), 400

        if len(tipo_fuente) > 100:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El tipo de fuente no puede "
                    "superar los 100 caracteres."
                )
            }), 400

        fuente.tipo_fuente = tipo_fuente

    # --------------------------------------------------------
    # DESCRIPCIÓN
    # --------------------------------------------------------

    if "descripcion" in datos:

        descripcion = datos.get(
            "descripcion"
        )

        if descripcion is None:

            fuente.descripcion = None

        else:

            descripcion = str(
                descripcion
            ).strip()

            if len(descripcion) > 255:

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "La descripción no puede "
                        "superar los 255 caracteres."
                    )
                }), 400

            fuente.descripcion = (
                descripcion
                if descripcion
                else None
            )

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    if "estado" in datos:

        estado = datos.get(
            "estado"
        )

        if not isinstance(
            estado,
            bool
        ):

            return jsonify({
                "estado": "ERROR",
                "mensaje":
                    "El estado debe ser true o false."
            }), 400

        fuente.estado = estado

    try:

        # ----------------------------------------------------
        # DETERMINAR ACCIÓN DE AUDITORÍA
        # ----------------------------------------------------

        estado_nuevo = bool(
            fuente.estado
        )

        if (
            estado_anterior is False
            and estado_nuevo is True
        ):

            accion_auditoria = (
                "ACTIVAR_FUENTE"
            )

        elif (
            estado_anterior is True
            and estado_nuevo is False
        ):

            accion_auditoria = (
                "DESACTIVAR_FUENTE"
            )

        else:

            accion_auditoria = (
                "ACTUALIZAR_FUENTE"
            )

        # ----------------------------------------------------
        # CONSTRUIR DETALLE
        # ----------------------------------------------------

        cambios = []

        if nombre_anterior != fuente.nombre:

            cambios.append(
                f"nombre: "
                f"'{nombre_anterior}' -> "
                f"'{fuente.nombre}'"
            )

        if tipo_anterior != fuente.tipo_fuente:

            cambios.append(
                f"tipo: "
                f"'{tipo_anterior}' -> "
                f"'{fuente.tipo_fuente}'"
            )

        if (
            descripcion_anterior
            != fuente.descripcion
        ):

            cambios.append(
                "descripción modificada"
            )

        if (
            estado_anterior
            != estado_nuevo
        ):

            cambios.append(
                f"estado: "
                f"{estado_anterior} -> "
                f"{estado_nuevo}"
            )

        detalle_cambios = (
            "; ".join(
                cambios
            )
            if cambios
            else
            "No se detectaron cambios de valores."
        )

        # ----------------------------------------------------
        # AUDITORÍA Y GUARDADO
        # ----------------------------------------------------

        auditoria_registrada = registrar_auditoria(
            accion=accion_auditoria,
            entidad_afectada="FUENTE_EVENTO",
            id_registro_afectado=id_fuente,
            resultado="OK",
            detalle=(
                f"Fuente {id_fuente} actualizada. "
                f"{detalle_cambios}"
            )
        )

        if not auditoria_registrada:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la actualización."
                )
            }), 500

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Fuente de eventos actualizada "
                "correctamente."
            ),
            "data": fuente.to_dict()
        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR FUENTE:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "la fuente de eventos."
            ),
            "detalle": str(error)
        }), 500


# ============================================================
# DESACTIVAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ============================================================

@fuentes_bp.delete("/<int:id_fuente>")
@roles_required("ADMINISTRADOR")
def desactivar_fuente(id_fuente):
    """
    Realiza una eliminación lógica de una fuente de eventos.

    La fuente no se elimina físicamente.
    Únicamente cambia su estado a inactivo.
    """

    fuente = db.session.get(
        FuenteEvento,
        id_fuente
    )

    if fuente is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "Fuente de eventos no encontrada."
        }), 404

    if not fuente.estado:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La fuente de eventos "
                "ya se encuentra desactivada."
            )
        }), 409

    try:

        # ----------------------------------------------------
        # DESACTIVACIÓN LÓGICA
        # ----------------------------------------------------

        fuente.estado = False

        # ----------------------------------------------------
        # AUDITORÍA
        # ----------------------------------------------------

        auditoria_registrada = registrar_auditoria(
            accion="DESACTIVAR_FUENTE",
            entidad_afectada="FUENTE_EVENTO",
            id_registro_afectado=id_fuente,
            resultado="OK",
            detalle=(
                f"Se desactivó la fuente de eventos "
                f"'{fuente.nombre}' "
                f"con ID {id_fuente}."
            )
        )

        if not auditoria_registrada:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la desactivación."
                )
            }), 500

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Fuente de eventos desactivada "
                "correctamente."
            ),
            "data": fuente.to_dict()
        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL DESACTIVAR FUENTE:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al desactivar "
                "la fuente de eventos."
            ),
            "detalle": str(error)
        }), 500