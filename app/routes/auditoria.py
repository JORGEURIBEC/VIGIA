from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Auditoria, Usuario


auditoria_bp = Blueprint(
    "auditoria",
    __name__,
    url_prefix="/api/v1/auditoria"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtener_usuario_actual():
    """
    Obtiene el usuario autenticado a partir del JWT.
    VIGIA utiliza el id del usuario como identidad principal.
    También se deja compatibilidad por correo.
    """

    identidad = get_jwt_identity()

    if identidad is None:
        return None

    # Intentar interpretar la identidad como ID numérico
    try:
        id_usuario = int(identidad)
        usuario = db.session.get(Usuario, id_usuario)

        if usuario:
            return usuario

    except (TypeError, ValueError):
        pass

    # Compatibilidad en caso de que el JWT almacene el correo
    return Usuario.query.filter_by(
        correo=str(identidad)
    ).first()


def verificar_administrador():
    """
    Verifica que el usuario autenticado corresponda
    al perfil Administrador.

    En la base de datos actual de VIGIA:
    id_rol = 1 -> ADMINISTRADOR
    id_rol = 2 -> ANALISTA DE SEGURIDAD
    """

    usuario = obtener_usuario_actual()

    if not usuario:
        return None, (
            jsonify({
                "estado": "ERROR",
                "mensaje": "No fue posible identificar al usuario autenticado."
            }),
            401
        )

    if usuario.id_rol != 1:
        return None, (
            jsonify({
                "estado": "ERROR",
                "mensaje": "Acceso denegado. Esta función requiere perfil ADMINISTRADOR."
            }),
            403
        )

    return usuario, None


def auditoria_a_dict(registro):
    """
    Convierte un registro de auditoría en un diccionario
    apto para ser retornado como JSON.
    """

    return {
        "id_auditoria": registro.id_auditoria,
        "id_usuario": registro.id_usuario,
        "accion": registro.accion,
        "entidad_afectada": registro.entidad_afectada,
        "id_registro_afectado": registro.id_registro_afectado,
        "fecha_hora": (
            registro.fecha_hora.isoformat()
            if registro.fecha_hora
            else None
        ),
        "resultado": registro.resultado,
        "detalle": registro.detalle,
        "direccion_ip": registro.direccion_ip
    }


# ============================================================
# GET /api/v1/auditoria
# LISTAR REGISTROS DE AUDITORÍA
# ============================================================

@auditoria_bp.route("", methods=["GET"])
@jwt_required()
def listar_auditoria():

    usuario, error = verificar_administrador()

    if error:
        return error

    consulta = Auditoria.query

    # --------------------------------------------------------
    # FILTRO POR USUARIO
    # --------------------------------------------------------

    id_usuario = request.args.get("id_usuario")

    if id_usuario:
        try:
            consulta = consulta.filter(
                Auditoria.id_usuario == int(id_usuario)
            )
        except ValueError:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "El parámetro id_usuario debe ser numérico."
            }), 400

    # --------------------------------------------------------
    # FILTRO POR ACCIÓN
    # --------------------------------------------------------

    accion = request.args.get("accion")

    if accion:
        consulta = consulta.filter(
            Auditoria.accion.ilike(f"%{accion.strip()}%")
        )

    # --------------------------------------------------------
    # FILTRO POR ENTIDAD
    # --------------------------------------------------------

    entidad = request.args.get("entidad")

    if entidad:
        consulta = consulta.filter(
            Auditoria.entidad_afectada.ilike(
                f"%{entidad.strip()}%"
            )
        )

    # --------------------------------------------------------
    # FILTRO POR RESULTADO
    # --------------------------------------------------------

    resultado = request.args.get("resultado")

    if resultado:
        consulta = consulta.filter(
            Auditoria.resultado == resultado.strip().upper()
        )

    # --------------------------------------------------------
    # FILTRO DESDE FECHA
    # Formato esperado: YYYY-MM-DD
    # --------------------------------------------------------

    fecha_desde = request.args.get("fecha_desde")

    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(
                fecha_desde,
                "%Y-%m-%d"
            )

            consulta = consulta.filter(
                Auditoria.fecha_hora >= fecha_desde_obj
            )

        except ValueError:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "fecha_desde debe utilizar "
                    "el formato YYYY-MM-DD."
                )
            }), 400

    # --------------------------------------------------------
    # FILTRO HASTA FECHA
    # --------------------------------------------------------

    fecha_hasta = request.args.get("fecha_hasta")

    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(
                fecha_hasta,
                "%Y-%m-%d"
            )

            # Incluir todo el día seleccionado
            fecha_hasta_obj = fecha_hasta_obj.replace(
                hour=23,
                minute=59,
                second=59
            )

            consulta = consulta.filter(
                Auditoria.fecha_hora <= fecha_hasta_obj
            )

        except ValueError:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "fecha_hasta debe utilizar "
                    "el formato YYYY-MM-DD."
                )
            }), 400

    # --------------------------------------------------------
    # LÍMITE DE RESULTADOS
    # --------------------------------------------------------

    try:
        limite = int(request.args.get("limite", 100))
    except ValueError:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El parámetro limite debe ser numérico."
        }), 400

    if limite < 1:
        limite = 1

    if limite > 500:
        limite = 500

    registros = (
        consulta
        .order_by(Auditoria.fecha_hora.desc())
        .limit(limite)
        .all()
    )

    return jsonify({
        "estado": "OK",
        "total": len(registros),
        "data": [
            auditoria_a_dict(registro)
            for registro in registros
        ]
    }), 200


# ============================================================
# GET /api/v1/auditoria/<id_auditoria>
# OBTENER UN REGISTRO ESPECÍFICO
# ============================================================

@auditoria_bp.route(
    "/<int:id_auditoria>",
    methods=["GET"]
)
@jwt_required()
def obtener_auditoria(id_auditoria):

    usuario, error = verificar_administrador()

    if error:
        return error

    registro = db.session.get(
        Auditoria,
        id_auditoria
    )

    if not registro:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Registro de auditoría no encontrado."
        }), 404

    return jsonify({
        "estado": "OK",
        "data": auditoria_a_dict(registro)
    }), 200