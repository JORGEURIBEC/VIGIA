from flask import Blueprint, jsonify, request

from app import db
from app.models import FuenteEvento
from app.decorators import roles_required


fuentes_bp = Blueprint(
    "fuentes",
    __name__,
    url_prefix="/api/v1/fuentes"
)


# ==========================================================
# LISTAR FUENTES DE EVENTOS
# ADMINISTRADOR / ANALISTA
# ==========================================================

@fuentes_bp.get("")
@roles_required("ADMINISTRADOR", "ANALISTA")
def listar_fuentes():
    """
    Lista todas las fuentes de eventos registradas en VIGIA.
    """

    fuentes = FuenteEvento.query.order_by(
        FuenteEvento.id_fuente
    ).all()

    return jsonify({
        "estado": "OK",
        "total": len(fuentes),
        "data": [
            fuente.to_dict()
            for fuente in fuentes
        ]
    }), 200


# ==========================================================
# OBTENER FUENTE POR ID
# ADMINISTRADOR / ANALISTA
# ==========================================================

@fuentes_bp.get("/<int:id_fuente>")
@roles_required("ADMINISTRADOR", "ANALISTA")
def obtener_fuente(id_fuente):
    """
    Obtiene una fuente de eventos específica mediante su ID.
    """

    fuente = FuenteEvento.query.filter_by(
        id_fuente=id_fuente
    ).first()

    if not fuente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Fuente de eventos no encontrada."
        }), 404

    return jsonify({
        "estado": "OK",
        "data": fuente.to_dict()
    }), 200


# ==========================================================
# CREAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ==========================================================

@fuentes_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_fuente():
    """
    Crea una nueva fuente de eventos de seguridad.
    """

    datos = request.get_json(silent=True) or {}

    nombre = str(
        datos.get("nombre", "")
    ).strip()

    tipo_fuente = str(
        datos.get("tipo_fuente", "")
    ).strip()

    descripcion = datos.get("descripcion")

    # ------------------------------------------------------
    # Validar campos obligatorios
    # ------------------------------------------------------

    if not nombre:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El nombre de la fuente es obligatorio."
        }), 400

    if not tipo_fuente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El tipo de fuente es obligatorio."
        }), 400

    # ------------------------------------------------------
    # Validar longitudes
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # Verificar nombre duplicado
    # ------------------------------------------------------

    existente = FuenteEvento.query.filter_by(
        nombre=nombre
    ).first()

    if existente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe una fuente de eventos "
                "registrada con ese nombre."
            )
        }), 409

    # ------------------------------------------------------
    # Crear registro
    # ------------------------------------------------------

    try:
        fuente = FuenteEvento(
            nombre=nombre,
            tipo_fuente=tipo_fuente,
            descripcion=descripcion,
            estado=True
        )

        db.session.add(fuente)
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Fuente de eventos creada correctamente.",
            "data": fuente.to_dict()
        }), 201

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al crear "
                "la fuente de eventos."
            )
        }), 500


# ==========================================================
# ACTUALIZAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ==========================================================

@fuentes_bp.put("/<int:id_fuente>")
@roles_required("ADMINISTRADOR")
def actualizar_fuente(id_fuente):
    """
    Actualiza una fuente de eventos existente.
    También permite cambiar su estado.
    """

    fuente = FuenteEvento.query.filter_by(
        id_fuente=id_fuente
    ).first()

    if not fuente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Fuente de eventos no encontrada."
        }), 404

    datos = request.get_json(silent=True) or {}

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "No se recibieron datos para actualizar."
        }), 400

    # ------------------------------------------------------
    # Nombre
    # ------------------------------------------------------

    if "nombre" in datos:

        nombre = str(
            datos.get("nombre", "")
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

        existente = FuenteEvento.query.filter(
            FuenteEvento.nombre == nombre,
            FuenteEvento.id_fuente != id_fuente
        ).first()

        if existente:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Ya existe otra fuente de eventos "
                    "registrada con ese nombre."
                )
            }), 409

        fuente.nombre = nombre

    # ------------------------------------------------------
    # Tipo de fuente
    # ------------------------------------------------------

    if "tipo_fuente" in datos:

        tipo_fuente = str(
            datos.get("tipo_fuente", "")
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

    # ------------------------------------------------------
    # Descripción
    # ------------------------------------------------------

    if "descripcion" in datos:

        descripcion = datos.get("descripcion")

        if descripcion is None:
            fuente.descripcion = None

        else:
            descripcion = str(descripcion).strip()

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

    # ------------------------------------------------------
    # Estado
    # ------------------------------------------------------

    if "estado" in datos:

        estado = datos.get("estado")

        if not isinstance(estado, bool):
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El estado debe ser true o false."
                )
            }), 400

        fuente.estado = estado

    # ------------------------------------------------------
    # Guardar cambios
    # ------------------------------------------------------

    try:
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Fuente de eventos actualizada "
                "correctamente."
            ),
            "data": fuente.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "la fuente de eventos."
            )
        }), 500


# ==========================================================
# DESACTIVAR FUENTE DE EVENTOS
# SOLO ADMINISTRADOR
# ==========================================================

@fuentes_bp.delete("/<int:id_fuente>")
@roles_required("ADMINISTRADOR")
def desactivar_fuente(id_fuente):
    """
    Realiza una eliminación lógica de una fuente de eventos.

    La fuente no se elimina físicamente de la base de datos;
    únicamente cambia su estado a inactivo para conservar
    la integridad y trazabilidad de la información.
    """

    fuente = FuenteEvento.query.filter_by(
        id_fuente=id_fuente
    ).first()

    if not fuente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Fuente de eventos no encontrada."
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
        fuente.estado = False

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Fuente de eventos desactivada "
                "correctamente."
            ),
            "data": fuente.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al desactivar "
                "la fuente de eventos."
            )
        }), 500