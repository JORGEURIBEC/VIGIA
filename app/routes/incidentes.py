from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import Incidente, Alerta, Usuario
from app.services.auditoria_service import registrar_auditoria


# ============================================================
# BLUEPRINT
# ============================================================

incidentes_bp = Blueprint(
    "incidentes",
    __name__,
    url_prefix="/api/v1/incidentes"
)


# ============================================================
# VALORES PERMITIDOS
# ============================================================

PRIORIDADES_VALIDAS = {
    "BAJA",
    "MEDIA",
    "ALTA",
    "CRITICA"
}

ESTADOS_VALIDOS = {
    "ABIERTO",
    "EN_ANALISIS",
    "EN_TRATAMIENTO",
    "RESUELTO",
    "CERRADO"
}


# ============================================================
# TRANSICIONES PERMITIDAS
# ============================================================

TRANSICIONES_ESTADO = {
    "ABIERTO": {
        "ABIERTO",
        "EN_ANALISIS"
    },

    "EN_ANALISIS": {
        "EN_ANALISIS",
        "EN_TRATAMIENTO"
    },

    "EN_TRATAMIENTO": {
        "EN_TRATAMIENTO",
        "RESUELTO"
    },

    "RESUELTO": {
        "RESUELTO",
        "CERRADO",
        "EN_TRATAMIENTO"
    },

    "CERRADO": {
        "CERRADO"
    }
}


# ============================================================
# FUNCIÓN AUXILIAR
# ============================================================

def normalizar_texto(valor):
    """
    Convierte un valor a texto eliminando espacios
    al inicio y al final.

    Si el valor es None, devuelve None.
    """

    if valor is None:
        return None

    return str(valor).strip()


# ============================================================
# GET
# LISTAR INCIDENTES
# ============================================================

@incidentes_bp.route("", methods=["GET"])
@jwt_required()
def listar_incidentes():

    try:

        query = Incidente.query

        # ----------------------------------------------------
        # FILTROS OPCIONALES
        # ----------------------------------------------------

        estado = request.args.get("estado")
        prioridad = request.args.get("prioridad")
        id_responsable = request.args.get("id_responsable")
        id_alerta = request.args.get("id_alerta")

        if estado:

            estado = estado.strip().upper()

            if estado not in ESTADOS_VALIDOS:

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "Estado de incidente no válido."
                }), 400

            query = query.filter(
                Incidente.estado == estado
            )

        if prioridad:

            prioridad = prioridad.strip().upper()

            if prioridad not in PRIORIDADES_VALIDAS:

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "Prioridad no válida."
                }), 400

            query = query.filter(
                Incidente.prioridad == prioridad
            )

        if id_responsable:

            try:
                id_responsable = int(id_responsable)

            except (TypeError, ValueError):

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El id_responsable debe ser numérico."
                }), 400

            query = query.filter(
                Incidente.id_responsable == id_responsable
            )

        if id_alerta:

            try:
                id_alerta = int(id_alerta)

            except (TypeError, ValueError):

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "El id_alerta debe ser numérico."
                }), 400

            query = query.filter(
                Incidente.id_alerta == id_alerta
            )

        # ----------------------------------------------------
        # CONSULTA
        # ----------------------------------------------------

        incidentes = (
            query
            .order_by(
                Incidente.fecha_creacion.desc()
            )
            .all()
        )

        return jsonify({
            "estado": "OK",
            "total": len(incidentes),
            "data": [
                incidente.to_dict()
                for incidente in incidentes
            ]
        }), 200

    except Exception as e:

        print(
            "ERROR AL LISTAR INCIDENTES:",
            type(e).__name__,
            str(e)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible obtener los incidentes."
        }), 500


# ============================================================
# GET
# OBTENER INCIDENTE POR ID
# ============================================================

@incidentes_bp.route(
    "/<int:id_incidente>",
    methods=["GET"]
)
@jwt_required()
def obtener_incidente(id_incidente):

    try:

        incidente = db.session.get(
            Incidente,
            id_incidente
        )

        if not incidente:

            return jsonify({
                "estado": "ERROR",
                "mensaje": "Incidente no encontrado."
            }), 404

        return jsonify({
            "estado": "OK",
            "data": incidente.to_dict()
        }), 200

    except Exception as e:

        print(
            "ERROR AL OBTENER INCIDENTE:",
            type(e).__name__,
            str(e)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible obtener el incidente."
        }), 500


# ============================================================
# POST
# CREAR INCIDENTE
# ============================================================

@incidentes_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
def crear_incidente():

    datos = request.get_json(
        silent=True
    )

    # --------------------------------------------------------
    # VALIDAR JSON
    # --------------------------------------------------------

    if not datos:

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar datos en formato JSON."
        }), 400

    # --------------------------------------------------------
    # CAMPOS OBLIGATORIOS
    # --------------------------------------------------------

    campos_obligatorios = [
        "id_alerta",
        "titulo",
        "descripcion",
        "prioridad"
    ]

    faltantes = []

    for campo in campos_obligatorios:

        if (
            campo not in datos
            or datos[campo] is None
            or str(datos[campo]).strip() == ""
        ):
            faltantes.append(campo)

    if faltantes:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Faltan campos obligatorios: "
                + ", ".join(faltantes)
            )
        }), 400

    # --------------------------------------------------------
    # ID ALERTA
    # --------------------------------------------------------

    try:

        id_alerta = int(
            datos["id_alerta"]
        )

    except (TypeError, ValueError):

        return jsonify({
            "estado": "ERROR",
            "mensaje": "El id_alerta debe ser numérico."
        }), 400

    # --------------------------------------------------------
    # RESPONSABLE
    # --------------------------------------------------------

    id_responsable = datos.get(
        "id_responsable"
    )

    if id_responsable not in (
        None,
        ""
    ):

        try:

            id_responsable = int(
                id_responsable
            )

        except (TypeError, ValueError):

            return jsonify({
                "estado": "ERROR",
                "mensaje": "El id_responsable debe ser numérico."
            }), 400

    else:

        id_responsable = None

    # --------------------------------------------------------
    # PRIORIDAD
    # --------------------------------------------------------

    prioridad = (
        str(
            datos["prioridad"]
        )
        .strip()
        .upper()
    )

    if prioridad not in PRIORIDADES_VALIDAS:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Prioridad no válida. "
                "Valores permitidos: "
                "BAJA, MEDIA, ALTA o CRITICA."
            )
        }), 400

    # --------------------------------------------------------
    # BUSCAR ALERTA
    # --------------------------------------------------------

    alerta = db.session.get(
        Alerta,
        id_alerta
    )

    if not alerta:

        return jsonify({
            "estado": "ERROR",
            "mensaje": "La alerta indicada no existe."
        }), 404

    # --------------------------------------------------------
    # LA ALERTA DEBE ESTAR ESCALADA
    # --------------------------------------------------------

    if (
        str(alerta.estado)
        .strip()
        .upper()
        != "ESCALADA"
    ):

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Solo se puede crear un incidente "
                "desde una alerta en estado ESCALADA."
            )
        }), 400

    # --------------------------------------------------------
    # EVITAR DOS INCIDENTES PARA LA MISMA ALERTA
    # --------------------------------------------------------

    incidente_existente = (
        Incidente.query
        .filter_by(
            id_alerta=id_alerta
        )
        .first()
    )

    if incidente_existente:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La alerta ya posee un incidente asociado."
            ),
            "id_incidente": incidente_existente.id_incidente
        }), 409

    # --------------------------------------------------------
    # VALIDAR RESPONSABLE
    # --------------------------------------------------------

    if id_responsable is not None:

        responsable = db.session.get(
            Usuario,
            id_responsable
        )

        if not responsable:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El usuario responsable indicado no existe."
                )
            }), 404

    # --------------------------------------------------------
    # CREAR OBJETO
    # --------------------------------------------------------

    incidente = Incidente(
        id_alerta=id_alerta,

        id_responsable=id_responsable,

        titulo=(
            str(datos["titulo"])
            .strip()
        ),

        descripcion=(
            str(datos["descripcion"])
            .strip()
        ),

        clasificacion=(
            normalizar_texto(
                datos.get(
                    "clasificacion"
                )
            )
        ),

        prioridad=prioridad,

        estado="ABIERTO",

        observaciones=(
            normalizar_texto(
                datos.get(
                    "observaciones"
                )
            )
        )
    )

    # --------------------------------------------------------
    # GUARDAR INCIDENTE
    # --------------------------------------------------------

    try:

        db.session.add(
            incidente
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "ERROR AL CREAR INCIDENTE:",
            type(e).__name__,
            str(e)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No fue posible crear el incidente."
        }), 500

    # --------------------------------------------------------
    # AUDITORÍA
    # --------------------------------------------------------

    resultado_auditoria = registrar_auditoria(
        accion="CREAR_INCIDENTE",
        entidad_afectada="INCIDENTE",
        id_registro_afectado=incidente.id_incidente,
        resultado="OK",
        detalle=(
            f"Se creó el Incidente "
            f"{incidente.id_incidente} "
            f"a partir de la Alerta "
            f"{incidente.id_alerta}."
        )
    )

    print(
        "DEBUG AUDITORÍA CREAR INCIDENTE:",
        resultado_auditoria
    )

    # --------------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------------

    return jsonify({
        "estado": "OK",
        "mensaje": (
            "Incidente creado correctamente "
            "desde la alerta escalada."
        ),
        "data": incidente.to_dict()
    }), 201


# ============================================================
# PUT
# ACTUALIZAR INCIDENTE
# ============================================================

@incidentes_bp.route(
    "/<int:id_incidente>",
    methods=["PUT"]
)
@jwt_required()
def actualizar_incidente(id_incidente):

    # --------------------------------------------------------
    # BUSCAR INCIDENTE
    # --------------------------------------------------------

    incidente = db.session.get(
        Incidente,
        id_incidente
    )

    if not incidente:

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Incidente no encontrado."
        }), 404

    # --------------------------------------------------------
    # RECIBIR JSON
    # --------------------------------------------------------

    datos = request.get_json(
        silent=True
    )

    if not datos:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Debe enviar al menos un campo para actualizar."
            )
        }), 400

    # Guardamos estado anterior para la auditoría.
    estado_anterior = incidente.estado

    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    if "titulo" in datos:

        titulo = normalizar_texto(
            datos.get("titulo")
        )

        if not titulo:

            return jsonify({
                "estado": "ERROR",
                "mensaje": "El título no puede quedar vacío."
            }), 400

        incidente.titulo = titulo

    # --------------------------------------------------------
    # DESCRIPCIÓN
    # --------------------------------------------------------

    if "descripcion" in datos:

        descripcion = normalizar_texto(
            datos.get("descripcion")
        )

        if not descripcion:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La descripción no puede quedar vacía."
                )
            }), 400

        incidente.descripcion = descripcion

    # --------------------------------------------------------
    # CLASIFICACIÓN
    # --------------------------------------------------------

    if "clasificacion" in datos:

        clasificacion = normalizar_texto(
            datos.get(
                "clasificacion"
            )
        )

        incidente.clasificacion = (
            clasificacion
            if clasificacion
            else None
        )

    # --------------------------------------------------------
    # PRIORIDAD
    # --------------------------------------------------------

    if "prioridad" in datos:

        prioridad = (
            str(
                datos["prioridad"]
            )
            .strip()
            .upper()
        )

        if prioridad not in PRIORIDADES_VALIDAS:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Prioridad no válida. "
                    "Valores permitidos: "
                    "BAJA, MEDIA, ALTA o CRITICA."
                )
            }), 400

        incidente.prioridad = prioridad

    # --------------------------------------------------------
    # RESPONSABLE
    # --------------------------------------------------------

    if "id_responsable" in datos:

        nuevo_responsable = datos.get(
            "id_responsable"
        )

        if nuevo_responsable in (
            None,
            ""
        ):

            incidente.id_responsable = None

        else:

            try:

                nuevo_responsable = int(
                    nuevo_responsable
                )

            except (TypeError, ValueError):

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El id_responsable debe ser numérico."
                    )
                }), 400

            usuario = db.session.get(
                Usuario,
                nuevo_responsable
            )

            if not usuario:

                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El usuario responsable indicado no existe."
                    )
                }), 404

            incidente.id_responsable = (
                nuevo_responsable
            )

    # --------------------------------------------------------
    # OBSERVACIONES
    # --------------------------------------------------------

    if "observaciones" in datos:

        observaciones = normalizar_texto(
            datos.get(
                "observaciones"
            )
        )

        incidente.observaciones = (
            observaciones
            if observaciones
            else None
        )

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    if "estado" in datos:

        nuevo_estado = (
            str(
                datos["estado"]
            )
            .strip()
            .upper()
        )

        if nuevo_estado not in ESTADOS_VALIDOS:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Estado no válido. "
                    "Valores permitidos: "
                    "ABIERTO, EN_ANALISIS, "
                    "EN_TRATAMIENTO, RESUELTO o CERRADO."
                )
            }), 400

        estado_actual = (
            str(
                incidente.estado
            )
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # VALIDAR TRANSICIÓN
        # ----------------------------------------------------

        estados_permitidos = (
            TRANSICIONES_ESTADO.get(
                estado_actual,
                set()
            )
        )

        if nuevo_estado not in estados_permitidos:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    f"No se permite cambiar el incidente "
                    f"desde {estado_actual} "
                    f"hacia {nuevo_estado}."
                )
            }), 400

        incidente.estado = nuevo_estado

        # ----------------------------------------------------
        # FECHA DE CIERRE
        # ----------------------------------------------------

        if nuevo_estado == "CERRADO":

         incidente.fecha_cierre = (
        datetime.now(
            timezone.utc
        ).replace(
            tzinfo=None
        )
    )

        elif estado_actual == "CERRADO":

            incidente.fecha_cierre = None

    # --------------------------------------------------------
    # GUARDAR CAMBIOS
    # --------------------------------------------------------

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR INCIDENTE:",
            type(e).__name__,
            str(e)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible actualizar el incidente."
            ),
            "detalle": (
                f"{type(e).__name__}: {str(e)}"
            )
        }), 500

    # --------------------------------------------------------
    # AUDITORÍA
    # --------------------------------------------------------

    resultado_auditoria = registrar_auditoria(
        accion="ACTUALIZAR_INCIDENTE",
        entidad_afectada="INCIDENTE",
        id_registro_afectado=incidente.id_incidente,
        resultado="OK",
        detalle=(
            f"Incidente {incidente.id_incidente} actualizado. "
            f"Estado anterior: {estado_anterior}. "
            f"Estado actual: {incidente.estado}."
        )
    )

    print(
        "DEBUG AUDITORÍA ACTUALIZAR INCIDENTE:",
        resultado_auditoria
    )

    # --------------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------------

    return jsonify({
        "estado": "OK",
        "mensaje": "Incidente actualizado correctamente.",
        "data": incidente.to_dict()
    }), 200