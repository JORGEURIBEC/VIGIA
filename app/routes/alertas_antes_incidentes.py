from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Alerta, AlertaEvento, Usuario
from app.services.auditoria_service import registrar_auditoria


# ============================================================
# BLUEPRINT DE ALERTAS
# ============================================================

alertas_bp = Blueprint(
    "alertas",
    __name__,
    url_prefix="/api/v1/alertas"
)


# ============================================================
# ESTADOS PERMITIDOS
# ============================================================

ESTADOS_ALERTA = {
    "PENDIENTE",
    "EN_REVISION",
    "DESCARTADA",
    "ESCALADA"
}


# ============================================================
# OBTENER USUARIO AUTENTICADO
# ============================================================

def obtener_usuario_actual():
    """
    Obtiene el usuario autenticado a partir del JWT.
    """

    identidad = get_jwt_identity()

    try:
        id_usuario = int(identidad)

    except (TypeError, ValueError):
        return None

    return db.session.get(
        Usuario,
        id_usuario
    )


# ============================================================
# VALIDAR PERMISOS
# ============================================================

def usuario_puede_gestionar_alertas(usuario):
    """
    Las alertas pueden ser gestionadas por los perfiles
    ADMINISTRADOR y ANALISTA.
    """

    if not usuario or not usuario.estado:
        return False

    nombre_rol = getattr(
        usuario.rol,
        "nombre_rol",
        None
    )

    return nombre_rol in {
        "ADMINISTRADOR",
        "ANALISTA"
    }


# ============================================================
# SERIALIZAR ALERTA
# ============================================================

def serializar_alerta(
    alerta,
    eventos=None
):
    """
    Convierte una alerta a un diccionario JSON e incorpora
    los identificadores de los eventos relacionados.
    """

    if eventos is None:
        eventos = []

    return {
        "id_alerta":
            alerta.id_alerta,

        "id_regla":
            alerta.id_regla,

        "id_usuario_revisor":
            alerta.id_usuario_revisor,

        "fecha_generacion": (
            alerta.fecha_generacion.isoformat()
            if alerta.fecha_generacion
            else None
        ),

        "severidad":
            alerta.severidad,

        "descripcion":
            alerta.descripcion,

        "estado":
            alerta.estado,

        "fecha_revision": (
            alerta.fecha_revision.isoformat()
            if alerta.fecha_revision
            else None
        ),

        "eventos":
            eventos
    }


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
            "mensaje":
                "No tiene permisos para consultar las alertas."
        }), 403

    try:

        # ----------------------------------------------------
        # FILTROS
        # ----------------------------------------------------

        estado = request.args.get(
            "estado",
            type=str
        )

        severidad = request.args.get(
            "severidad",
            type=str
        )

        id_regla = request.args.get(
            "id_regla",
            type=int
        )

        # ----------------------------------------------------
        # PAGINACIÓN
        # ----------------------------------------------------

        pagina = request.args.get(
            "page",
            default=1,
            type=int
        )

        por_pagina = request.args.get(
            "per_page",
            default=25,
            type=int
        )

        pagina = max(
            pagina,
            1
        )

        por_pagina = max(
            1,
            min(
                por_pagina,
                100
            )
        )

        # ----------------------------------------------------
        # CONSULTA BASE
        # ----------------------------------------------------

        consulta = Alerta.query

        # ----------------------------------------------------
        # FILTRAR ESTADO
        # ----------------------------------------------------

        if estado:

            estado = estado.strip().upper()

            if estado not in ESTADOS_ALERTA:

                return jsonify({
                    "estado": "ERROR",
                    "mensaje":
                        "El estado indicado no es válido.",
                    "estados_permitidos":
                        sorted(ESTADOS_ALERTA)
                }), 400

            consulta = consulta.filter(
                Alerta.estado == estado
            )

        # ----------------------------------------------------
        # FILTRAR SEVERIDAD
        # ----------------------------------------------------

        if severidad:

            consulta = consulta.filter(
                Alerta.severidad ==
                severidad.strip().upper()
            )

        # ----------------------------------------------------
        # FILTRAR REGLA
        # ----------------------------------------------------

        if id_regla:

            consulta = consulta.filter(
                Alerta.id_regla == id_regla
            )

        # ----------------------------------------------------
        # TOTAL ANTES DE PAGINAR
        # ----------------------------------------------------

        total = consulta.count()

        # ----------------------------------------------------
        # CONSULTA PAGINADA
        # ----------------------------------------------------

        paginacion = (
            consulta
            .order_by(
                Alerta.fecha_generacion.desc(),
                Alerta.id_alerta.desc()
            )
            .paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
        )

        alertas = paginacion.items

        # ----------------------------------------------------
        # IDS DE ALERTAS CONSULTADAS
        # ----------------------------------------------------

        ids_alertas = [
            alerta.id_alerta
            for alerta in alertas
        ]

        # ----------------------------------------------------
        # OBTENER TODAS LAS RELACIONES EN UNA SOLA CONSULTA
        # ----------------------------------------------------

        eventos_por_alerta = defaultdict(list)

        if ids_alertas:

            relaciones = (
                AlertaEvento.query
                .filter(
                    AlertaEvento.id_alerta.in_(
                        ids_alertas
                    )
                )
                .all()
            )

            for relacion in relaciones:

                eventos_por_alerta[
                    relacion.id_alerta
                ].append(
                    relacion.id_evento
                )

        # ----------------------------------------------------
        # SERIALIZAR
        # ----------------------------------------------------

        datos = [
            serializar_alerta(
                alerta,
                eventos_por_alerta.get(
                    alerta.id_alerta,
                    []
                )
            )
            for alerta in alertas
        ]

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        return jsonify({

            "estado":
                "OK",

            "total":
                total,

            "pagina":
                pagina,

            "por_pagina":
                por_pagina,

            "total_paginas":
                paginacion.pages,

            "data":
                datos

        }), 200

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "Ocurrió un error al consultar las alertas.",
            "detalle":
                str(error)
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
            "mensaje":
                "No tiene permisos para consultar la alerta."
        }), 403

    try:

        alerta = db.session.get(
            Alerta,
            id_alerta
        )

        if not alerta:

            return jsonify({
                "estado": "ERROR",
                "mensaje":
                    "Alerta no encontrada."
            }), 404

        # ----------------------------------------------------
        # EVENTOS RELACIONADOS
        # ----------------------------------------------------

        eventos_relacionados = (
            AlertaEvento.query
            .filter_by(
                id_alerta=id_alerta
            )
            .all()
        )

        eventos = [
            relacion.id_evento
            for relacion
            in eventos_relacionados
        ]

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        return jsonify({

            "estado":
                "OK",

            "data":
                serializar_alerta(
                    alerta,
                    eventos
                )

        }), 200

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "Ocurrió un error al consultar la alerta.",
            "detalle":
                str(error)
        }), 500


# ============================================================
# ACTUALIZAR ESTADO DE UNA ALERTA
# ============================================================
# ============================================================
# ACTUALIZAR ESTADO DE UNA ALERTA
# ============================================================

@alertas_bp.put("/<int:id_alerta>/estado")
@jwt_required()
def actualizar_estado_alerta(id_alerta):

    usuario = obtener_usuario_actual()

    # --------------------------------------------------------
    # VALIDAR PERMISOS
    # --------------------------------------------------------

    if not usuario_puede_gestionar_alertas(
        usuario
    ):

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "No tiene permisos para gestionar alertas."
        }), 403

    # --------------------------------------------------------
    # OBTENER JSON
    # --------------------------------------------------------

    datos = request.get_json(
        silent=True
    ) or {}

    nuevo_estado = str(
        datos.get(
            "estado",
            ""
        )
    ).strip().upper()

    # --------------------------------------------------------
    # COMPATIBILIDAD
    # --------------------------------------------------------

    if nuevo_estado == "ESCALADA_INCIDENTE":
        nuevo_estado = "ESCALADA"

    # --------------------------------------------------------
    # VALIDAR NUEVO ESTADO
    # --------------------------------------------------------

    estados_actualizables = {
        "EN_REVISION",
        "DESCARTADA",
        "ESCALADA"
    }

    if nuevo_estado not in estados_actualizables:

        return jsonify({

            "estado":
                "ERROR",

            "mensaje":
                "Estado de alerta no válido.",

            "estados_permitidos": [
                "EN_REVISION",
                "DESCARTADA",
                "ESCALADA"
            ]

        }), 400

    # --------------------------------------------------------
    # BUSCAR ALERTA
    # --------------------------------------------------------

    alerta = db.session.get(
        Alerta,
        id_alerta
    )

    if alerta is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "La alerta solicitada no existe."
        }), 404

    # --------------------------------------------------------
    # ESTADO ACTUAL
    # --------------------------------------------------------

    estado_actual = str(
        alerta.estado or "PENDIENTE"
    ).upper()

    # Compatibilidad con registros antiguos.
    if estado_actual == "ESCALADA_INCIDENTE":
        estado_actual = "ESCALADA"

    # --------------------------------------------------------
    # TRANSICIONES PERMITIDAS
    # --------------------------------------------------------

    transiciones_permitidas = {

        "PENDIENTE": {
            "EN_REVISION"
        },

        "EN_REVISION": {
            "DESCARTADA",
            "ESCALADA"
        },

        "DESCARTADA":
            set(),

        "ESCALADA":
            set()

    }

    if nuevo_estado not in (
        transiciones_permitidas.get(
            estado_actual,
            set()
        )
    ):

        return jsonify({

            "estado":
                "ERROR",

            "mensaje": (
                f"No se permite cambiar una alerta "
                f"desde {estado_actual} "
                f"hacia {nuevo_estado}."
            )

        }), 400

    try:

        # ----------------------------------------------------
        # ACTUALIZAR ALERTA
        # ----------------------------------------------------

        alerta.estado = nuevo_estado

        # El revisor y la fecha corresponden al inicio
        # de la revisión. Si ya existen, se conservan.
        if nuevo_estado == "EN_REVISION":

            alerta.id_usuario_revisor = (
                usuario.id_usuario
            )

            alerta.fecha_revision = (
                datetime.now(
                    timezone.utc
                ).replace(
                    tzinfo=None
                )
            )

        else:

            if alerta.id_usuario_revisor is None:
                alerta.id_usuario_revisor = (
                    usuario.id_usuario
                )

            if alerta.fecha_revision is None:
                alerta.fecha_revision = (
                    datetime.now(
                        timezone.utc
                    ).replace(
                        tzinfo=None
                    )
                )

        # ----------------------------------------------------
        # EVENTOS RELACIONADOS
        # ----------------------------------------------------

        eventos_relacionados = (
            AlertaEvento.query
            .filter_by(
                id_alerta=id_alerta
            )
            .all()
        )

        eventos = [
            relacion.id_evento
            for relacion
            in eventos_relacionados
        ]

        # ----------------------------------------------------
        # DEFINIR ACCIÓN DE AUDITORÍA
        # ----------------------------------------------------

        acciones_auditoria = {

            (
                "PENDIENTE",
                "EN_REVISION"
            ):
                "REVISAR_ALERTA",

            (
                "EN_REVISION",
                "DESCARTADA"
            ):
                "DESCARTAR_ALERTA",

            (
                "EN_REVISION",
                "ESCALADA"
            ):
                "ESCALAR_ALERTA"
        }

        accion_auditoria = acciones_auditoria.get(
            (
                estado_actual,
                nuevo_estado
            )
        )

        if accion_auditoria is None:
            db.session.rollback()

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible determinar la acción "
                    "de auditoría para la transición solicitada."
                )
            }), 500

        # ----------------------------------------------------
        # REGISTRAR AUDITORÍA Y GUARDAR TRANSACCIÓN
        # ----------------------------------------------------
        #
        # registrar_auditoria() agrega el registro de auditoría
        # y realiza db.session.commit(). Como la modificación
        # de la alerta todavía pertenece a la misma sesión,
        # ambos cambios se persisten juntos.
        #
        # Si la auditoría falla, el servicio realiza rollback.
        # ----------------------------------------------------

        auditoria_registrada = registrar_auditoria(

            accion=accion_auditoria,

            entidad_afectada="ALERTA",

            id_registro_afectado=id_alerta,

            resultado="OK",

            detalle=(
                f"La alerta {id_alerta} cambió "
                f"de {estado_actual} "
                f"a {nuevo_estado}."
            ),

            id_usuario=usuario.id_usuario

        )

        if not auditoria_registrada:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "No fue posible registrar la "
                    "trazabilidad de la operación."
                )
            }), 500

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        return jsonify({

            "estado":
                "OK",

            "mensaje":
                "Estado de la alerta actualizado correctamente.",

            "data":
                serializar_alerta(
                    alerta,
                    eventos
                )

        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR ALERTA:",
            type(error).__name__,
            str(error)
        )

        return jsonify({

            "estado":
                "ERROR",

            "mensaje":
                "Ocurrió un error al actualizar la alerta.",

            "detalle":
                str(error)

        }), 500
