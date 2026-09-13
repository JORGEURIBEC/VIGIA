from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import TipoEvento
from app.decorators import roles_required


tipos_eventos_bp = Blueprint(
    "tipos_eventos",
    __name__,
    url_prefix="/api/v1/tipos-eventos"
)


# ============================================================
# LISTAR TIPOS DE EVENTOS
# ============================================================

@tipos_eventos_bp.get("")
@jwt_required()
def listar_tipos_eventos():
    """
    Lista todos los tipos de eventos registrados en VIGIA.

    Acceso permitido para usuarios autenticados:
    - ADMINISTRADOR
    - ANALISTA

    Los perfiles pueden consultar los tipos de eventos,
    pero solamente el ADMINISTRADOR puede administrarlos.
    """

    tipos = TipoEvento.query.order_by(
        TipoEvento.id_tipo_evento
    ).all()

    return jsonify({
        "estado": "OK",
        "total": len(tipos),
        "data": [
            tipo.to_dict()
            for tipo in tipos
        ]
    }), 200


# ============================================================
# OBTENER TIPO DE EVENTO POR ID
# ============================================================

@tipos_eventos_bp.get("/<int:id_tipo_evento>")
@jwt_required()
def obtener_tipo_evento(id_tipo_evento):
    """
    Obtiene un tipo de evento específico mediante su ID.

    Acceso permitido para usuarios autenticados:
    - ADMINISTRADOR
    - ANALISTA
    """

    tipo = TipoEvento.query.filter_by(
        id_tipo_evento=id_tipo_evento
    ).first()

    if not tipo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de evento no encontrado."
        }), 404

    return jsonify({
        "estado": "OK",
        "data": tipo.to_dict()
    }), 200


# ============================================================
# CREAR TIPO DE EVENTO
# ============================================================

@tipos_eventos_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_tipo_evento():
    """
    Registra un nuevo tipo de evento en VIGIA.

    Acceso exclusivo para ADMINISTRADOR.
    """

    datos = request.get_json(silent=True) or {}

    nombre_tipo = str(
        datos.get("nombre_tipo", "")
    ).strip()

    descripcion = str(
        datos.get("descripcion", "")
    ).strip()

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

    # --------------------------------------------------------
    # VALIDAR DUPLICADO
    # --------------------------------------------------------

    existente = TipoEvento.query.filter_by(
        nombre_tipo=nombre_tipo
    ).first()

    if existente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe un tipo de evento registrado "
                "con ese nombre."
            )
        }), 409

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    estado = datos.get("estado", True)

    if not isinstance(estado, bool):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El estado debe ser true o false."
        }), 400

    # --------------------------------------------------------
    # CREAR REGISTRO
    # --------------------------------------------------------

    nuevo_tipo = TipoEvento(
        nombre_tipo=nombre_tipo,
        descripcion=descripcion or None,
        estado=estado
    )

    try:

        db.session.add(nuevo_tipo)
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Tipo de evento creado correctamente.",
            "data": nuevo_tipo.to_dict()
        }), 201

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al registrar "
                "el tipo de evento."
            )
        }), 500


# ============================================================
# ACTUALIZAR TIPO DE EVENTO
# ============================================================

@tipos_eventos_bp.put("/<int:id_tipo_evento>")
@roles_required("ADMINISTRADOR")
def actualizar_tipo_evento(id_tipo_evento):
    """
    Actualiza la información de un tipo de evento.

    Acceso exclusivo para ADMINISTRADOR.
    """

    tipo = TipoEvento.query.filter_by(
        id_tipo_evento=id_tipo_evento
    ).first()

    if not tipo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de evento no encontrado."
        }), 404

    datos = request.get_json(silent=True) or {}

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

        existente = TipoEvento.query.filter(
            TipoEvento.nombre_tipo == nombre_tipo,
            TipoEvento.id_tipo_evento != id_tipo_evento
        ).first()

        if existente:
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

        descripcion = str(
            datos.get("descripcion", "")
        ).strip()

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

    # --------------------------------------------------------
    # GUARDAR
    # --------------------------------------------------------

    try:

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Tipo de evento actualizado correctamente."
            ),
            "data": tipo.to_dict()
        }), 200

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "el tipo de evento."
            )
        }), 500


# ============================================================
# DESACTIVAR TIPO DE EVENTO
# ============================================================

@tipos_eventos_bp.delete("/<int:id_tipo_evento>")
@roles_required("ADMINISTRADOR")
def desactivar_tipo_evento(id_tipo_evento):
    """
    Desactiva lógicamente un tipo de evento.

    No elimina físicamente el registro.

    Acceso exclusivo para ADMINISTRADOR.
    """

    tipo = TipoEvento.query.filter_by(
        id_tipo_evento=id_tipo_evento
    ).first()

    if not tipo:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de evento no encontrado."
        }), 404

    if not tipo.estado:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El tipo de evento ya se encuentra "
                "desactivado."
            )
        }), 409

    try:

        tipo.estado = False
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Tipo de evento desactivado correctamente."
            ),
            "data": tipo.to_dict()
        }), 200

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al desactivar "
                "el tipo de evento."
            )
        }), 500