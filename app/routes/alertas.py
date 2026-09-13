from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Alerta, AlertaEvento, Usuario


alertas_bp = Blueprint(
    "alertas",
    __name__,
    url_prefix="/api/v1/alertas"
)


ESTADOS_ALERTA = {
    "PENDIENTE",
    "EN_REVISION",
    "DESCARTADA",
    "ESCALADA_INCIDENTE"
}


def obtener_usuario_actual():
    """
    Obtiene el usuario autenticado a partir del JWT.
    """
    identidad = get_jwt_identity()

    try:
        id_usuario = int(identidad)
    except (TypeError, ValueError):
        return None

    return db.session.get(Usuario, id_usuario)


def usuario_puede_gestionar_alertas(usuario):
    """
    Las alertas pueden ser gestionadas por
    ADMINISTRADOR o ANALISTA.
    """
    if not usuario or not usuario.estado:
        return False

    nombre_rol = getattr(usuario.rol, "nombre_rol", None)

    return nombre_rol in {"ADMINISTRADOR", "ANALISTA"}


# ============================================================
# LISTAR ALERTAS
# ============================================================

@alertas_bp.get("")
@jwt_required()
def listar_alertas():
    usuario = obtener_usuario_actual()

    if not usuario_puede_gestionar_alertas(usuario):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "No tiene permisos para consultar las alertas."
        }), 403

    try:
        estado = request.args.get("estado", type=str)
        severidad = request.args.get("severidad", type=str)
        id_regla = request.args.get("id_regla", type=int)

        consulta = Alerta.query

        if estado:
            consulta = consulta.filter(
                Alerta.estado == estado.strip().upper()
            )

        if severidad:
            consulta = consulta.filter(
                Alerta.severidad == severidad.strip().upper()
            )

        if id_regla:
            consulta = consulta.filter(
                Alerta.id_regla == id_regla
            )

        alertas = consulta.order_by(
            Alerta.fecha_generacion.desc()
        ).all()

        datos = []

        for alerta in alertas:
            eventos_relacionados = (
                AlertaEvento.query
                .filter_by(id_alerta=alerta.id_alerta)
                .all()
            )

            datos.append({
                "id_alerta": alerta.id_alerta,
                "id_regla": alerta.id_regla,
                "id_usuario_revisor": alerta.id_usuario_revisor,
                "fecha_generacion": (
                    alerta.fecha_generacion.isoformat()
                    if alerta.fecha_generacion
                    else None
                ),
                "severidad": alerta.severidad,
                "descripcion": alerta.descripcion,
                "estado": alerta.estado,
                "fecha_revision": (
                    alerta.fecha_revision.isoformat()
                    if alerta.fecha_revision
                    else None
                ),
                "eventos": [
                    relacion.id_evento
                    for relacion in eventos_relacionados
                ]
            })

        return jsonify({
            "estado": "OK",
            "total": len(datos),
            "data": datos
        }), 200

    except Exception:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error al consultar las alertas."
        }), 500


# ============================================================
# OBTENER ALERTA POR ID
# ============================================================

@alertas_bp.get("/<int:id_alerta>")
@jwt_required()
def obtener_alerta(id_alerta):
    usuario = obtener_usuario_actual()

    if not usuario_puede_gestionar_alertas(usuario):
        return jsonify({
            "estado": "ERROR",
            "mensaje": "No tiene permisos para consultar la alerta."
        }), 403

    alerta = db.session.get(Alerta, id_alerta)

    if not alerta:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Alerta no encontrada."
        }), 404

    eventos_relacionados = (
        AlertaEvento.query
        .filter_by(id_alerta=id_alerta)
        .all()
    )

    return jsonify({
        "estado": "OK",
        "data": {
            "id_alerta": alerta.id_alerta,
            "id_regla": alerta.id_regla,
            "id_usuario_revisor": alerta.id_usuario_revisor,
            "fecha_generacion": (
                alerta.fecha_generacion.isoformat()
                if alerta.fecha_generacion
                else None
            ),
            "severidad": alerta.severidad,
            "descripcion": alerta.descripcion,
            "estado": alerta.estado,
            "fecha_revision": (
                alerta.fecha_revision.isoformat()
                if alerta.fecha_revision
                else None
            ),
            "eventos": [
                relacion.id_evento
                for relacion in eventos_relacionados
            ]
        }
    }), 200


# ============================================================
# ACTUALIZAR ESTADO DE UNA ALERTA
# ============================================================

@alertas_bp.put("/<int:id_alerta>/estado")
@jwt_required()
def actualizar_estado_alerta(id_alerta):

    datos = request.get_json(silent=True) or {}

    nuevo_estado = str(
        datos.get("estado", "")
    ).strip().upper()

    estados_validos = {
        "EN_REVISION",
        "DESCARTADA",
        "ESCALADA"
    }

    if nuevo_estado not in estados_validos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Estado de alerta no válido.",
            "estados_permitidos": [
                "EN_REVISION",
                "DESCARTADA",
                "ESCALADA"
            ]
        }), 400

    alerta = db.session.get(Alerta, id_alerta)

    if alerta is None:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "La alerta solicitada no existe."
        }), 404

    estado_actual = str(
        alerta.estado or "PENDIENTE"
    ).upper()

    transiciones_permitidas = {
        "PENDIENTE": {
            "EN_REVISION"
        },
        "EN_REVISION": {
            "DESCARTADA",
            "ESCALADA"
        },
        "DESCARTADA": set(),
        "ESCALADA": set()
    }

    if nuevo_estado not in transiciones_permitidas.get(
        estado_actual,
        set()
    ):
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                f"No se permite cambiar una alerta desde "
                f"{estado_actual} hacia {nuevo_estado}."
            )
        }), 400

    try:
        id_usuario_actual = int(get_jwt_identity())

        usuario = db.session.get(
            Usuario,
            id_usuario_actual
        )

        if usuario is None:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "El usuario autenticado no existe."
            }), 404

        alerta.estado = nuevo_estado
        alerta.id_usuario_revisor = usuario.id_usuario
        alerta.fecha_revision = datetime.now()

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": "Estado de la alerta actualizado correctamente.",
            "data": alerta.to_dict()
        }), 200

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error al actualizar la alerta.",
            "detalle": str(error)
        }), 500