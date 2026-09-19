from flask import Blueprint, jsonify, request

from app import db
from app.models import TipoEvento
from app.decorators import roles_required
from app.services.auditoria_service import registrar_auditoria


# ============================================================
# BLUEPRINT DE TIPOS DE EVENTOS
# ============================================================

tipos_eventos_bp = Blueprint(
    "tipos_eventos",
    __name__,
    url_prefix="/api/v1/tipos-eventos"
)


# ============================================================
# LISTAR TIPOS DE EVENTOS
# ADMINISTRADOR / ANALISTA
# ============================================================

@tipos_eventos_bp.get("")
@roles_required("ADMINISTRADOR", "ANALISTA")
def listar_tipos_eventos():
    """
    Lista todos los tipos de eventos registrados en VIGIA.
    """

    try:
        tipos = (
            TipoEvento.query
            .order_by(TipoEvento.id_tipo_evento.asc())
            .all()
        )

        return jsonify({
            "estado": "OK",
            "total": len(tipos),
            "data": [tipo.to_dict() for tipo in tipos]
        }), 200

    except Exception as error:
        print(
            "ERROR AL LISTAR TIPOS DE EVENTOS:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "los tipos de eventos."
            )
        }), 500


# ============================================================
# OBTENER TIPO DE EVENTO POR ID
# ADMINISTRADOR / ANALISTA
# ============================================================

@tipos_eventos_bp.get("/<int:id_tipo_evento>")
@roles_required("ADMINISTRADOR", "ANALISTA")
def obtener_tipo_evento(id_tipo_evento):
    """
    Obtiene un tipo de evento específico mediante su ID.
    """

    try:
        tipo = db.session.get(
            TipoEvento,
            id_tipo_evento
        )

        if tipo is None:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Tipo de evento no encontrado."
            }), 404

        return jsonify({
            "estado": "OK",
            "data": tipo.to_dict()
        }), 200

    except Exception as error:
        print(
            "ERROR AL OBTENER TIPO DE EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "el tipo de evento."
            )
        }), 500


# ============================================================
# CREAR TIPO DE EVENTO
# SOLO ADMINISTRADOR
# ============================================================

@tipos_eventos_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_tipo_evento():
    """
    Registra un nuevo tipo de evento en VIGIA.
    """

    datos = request.get_json(silent=True) or {}

    nombre_tipo = str(
        datos.get("nombre_tipo", "")
    ).strip()

    descripcion = datos.get("descripcion")

    # --------------------------------------------------------
    # VALIDAR NOMBRE
    # --------------------------------------------------------

    if not nombre_tipo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El nombre del tipo de evento es obligatorio."
            )
        }), 400

    if len(nombre_tipo) > 100:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El nombre del tipo de evento no puede superar "
                "los 100 caracteres."
            )
        }), 400

    # --------------------------------------------------------
    # VALIDAR DESCRIPCIÓN
    # --------------------------------------------------------

    if descripcion is not None:
        descripcion = str(descripcion).strip()

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
    # VALIDAR DUPLICADO
    # --------------------------------------------------------

    existente = (
        TipoEvento.query
        .filter_by(nombre_tipo=nombre_tipo)
        .first()
    )

    if existente is not None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe un tipo de evento registrado "
                "con ese nombre."
            )
        }), 409

    # --------------------------------------------------------
    # VALIDAR ESTADO
    # --------------------------------------------------------

    estado = datos.get("estado", True)

    if not isinstance(estado, bool):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El estado debe ser true o false."
        }), 400

    try:
        nuevo_tipo = TipoEvento(
            nombre_tipo=nombre_tipo,
            descripcion=descripcion,
            estado=estado
        )

        db.session.add(nuevo_tipo)
        db.session.flush()

        auditoria_registrada = registrar_auditoria(
            accion="CREAR_TIPO_EVENTO",
            entidad_afectada="TIPO_EVENTO",
            id_registro_afectado=nuevo_tipo.id_tipo_evento,
            resultado="OK",
            detalle=(
                f"Se creó el tipo de evento "
                f"'{nuevo_tipo.nombre_tipo}' "
                f"con ID {nuevo_tipo.id_tipo_evento}."
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

        return jsonify({
            "estado": "OK",
            "mensaje": "Tipo de evento creado correctamente.",
            "data": nuevo_tipo.to_dict()
        }), 201

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL CREAR TIPO DE EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al registrar "
                "el tipo de evento."
            )
        }), 500


# ============================================================
# ACTUALIZAR TIPO DE EVENTO
# SOLO ADMINISTRADOR
# ============================================================

@tipos_eventos_bp.put("/<int:id_tipo_evento>")
@roles_required("ADMINISTRADOR")
def actualizar_tipo_evento(id_tipo_evento):
    """
    Actualiza la información de un tipo de evento.

    Permite modificar:
    - nombre_tipo
    - descripcion
    - estado
    """

    tipo = db.session.get(
        TipoEvento,
        id_tipo_evento
    )

    if tipo is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de evento no encontrado."
        }), 404

    datos = request.get_json(silent=True) or {}

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "No se recibieron datos para actualizar."
        }), 400

    nombre_anterior = tipo.nombre_tipo
    descripcion_anterior = tipo.descripcion
    estado_anterior = bool(tipo.estado)

    # --------------------------------------------------------
    # NOMBRE
    # --------------------------------------------------------

    if "nombre_tipo" in datos:
        nombre_tipo = str(
            datos.get("nombre_tipo", "")
        ).strip()

        if not nombre_tipo:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre del tipo de evento "
                    "no puede estar vacío."
                )
            }), 400

        if len(nombre_tipo) > 100:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre del tipo de evento no puede superar "
                    "los 100 caracteres."
                )
            }), 400

        existente = (
            TipoEvento.query
            .filter(
                TipoEvento.nombre_tipo == nombre_tipo,
                TipoEvento.id_tipo_evento != id_tipo_evento
            )
            .first()
        )

        if existente is not None:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Ya existe otro tipo de evento "
                    "registrado con ese nombre."
                )
            }), 409

        tipo.nombre_tipo = nombre_tipo

    # --------------------------------------------------------
    # DESCRIPCIÓN
    # --------------------------------------------------------

    if "descripcion" in datos:
        descripcion = datos.get("descripcion")

        if descripcion is None:
            tipo.descripcion = None
        else:
            descripcion = str(descripcion).strip()

            if len(descripcion) > 255:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "La descripción no puede superar "
                        "los 255 caracteres."
                    )
                }), 400

            tipo.descripcion = descripcion or None

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    if "estado" in datos:
        estado = datos.get("estado")

        if not isinstance(estado, bool):
            return jsonify({
                "estado": "ERROR",
                "mensaje": "El estado debe ser true o false."
            }), 400

        tipo.estado = estado

    try:
        estado_nuevo = bool(tipo.estado)

        if (
            estado_anterior is False
            and estado_nuevo is True
        ):
            accion_auditoria = "ACTIVAR_TIPO_EVENTO"

        elif (
            estado_anterior is True
            and estado_nuevo is False
        ):
            accion_auditoria = "DESACTIVAR_TIPO_EVENTO"

        else:
            accion_auditoria = "ACTUALIZAR_TIPO_EVENTO"

        cambios = []

        if nombre_anterior != tipo.nombre_tipo:
            cambios.append(
                f"nombre: '{nombre_anterior}' -> "
                f"'{tipo.nombre_tipo}'"
            )

        if descripcion_anterior != tipo.descripcion:
            cambios.append("descripción modificada")

        if estado_anterior != estado_nuevo:
            cambios.append(
                f"estado: {estado_anterior} -> {estado_nuevo}"
            )

        detalle_cambios = (
            "; ".join(cambios)
            if cambios
            else "No se detectaron cambios de valores."
        )

        auditoria_registrada = registrar_auditoria(
            accion=accion_auditoria,
            entidad_afectada="TIPO_EVENTO",
            id_registro_afectado=id_tipo_evento,
            resultado="OK",
            detalle=(
                f"Tipo de evento {id_tipo_evento} actualizado. "
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
                "Tipo de evento actualizado correctamente."
            ),
            "data": tipo.to_dict()
        }), 200

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR TIPO DE EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "el tipo de evento."
            )
        }), 500


# ============================================================
# DESACTIVAR TIPO DE EVENTO
# SOLO ADMINISTRADOR
# ============================================================

@tipos_eventos_bp.delete("/<int:id_tipo_evento>")
@roles_required("ADMINISTRADOR")
def desactivar_tipo_evento(id_tipo_evento):
    """
    Desactiva lógicamente un tipo de evento.

    No elimina físicamente el registro porque puede estar
    relacionado con eventos históricos almacenados en VIGIA.
    """

    tipo = db.session.get(
        TipoEvento,
        id_tipo_evento
    )

    if tipo is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de evento no encontrado."
        }), 404

    if not tipo.estado:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El tipo de evento ya se encuentra desactivado."
            )
        }), 409

    try:
        tipo.estado = False

        auditoria_registrada = registrar_auditoria(
            accion="DESACTIVAR_TIPO_EVENTO",
            entidad_afectada="TIPO_EVENTO",
            id_registro_afectado=id_tipo_evento,
            resultado="OK",
            detalle=(
                f"Se desactivó el tipo de evento "
                f"'{tipo.nombre_tipo}' "
                f"con ID {id_tipo_evento}."
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
                "Tipo de evento desactivado correctamente."
            ),
            "data": tipo.to_dict()
        }), 200

    except Exception as error:
        db.session.rollback()

        print(
            "ERROR AL DESACTIVAR TIPO DE EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al desactivar "
                "el tipo de evento."
            )
        }), 500
