import csv
import io
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import EventoSeguridad, FuenteEvento, TipoEvento


eventos_bp = Blueprint(
    "eventos",
    __name__,
    url_prefix="/api/v1/eventos"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEVERIDADES_VALIDAS = {
    "BAJA",
    "MEDIA",
    "ALTA",
    "CRITICA"
}


RESULTADOS_VALIDOS = {
    "EXITOSO",
    "FALLIDO",
    "BLOQUEADO"
}


COLUMNAS_CSV_REQUERIDAS = {
    "id_fuente",
    "id_tipo_evento",
    "fecha_hora",
    "usuario_origen",
    "direccion_ip",
    "severidad",
    "resultado",
    "descripcion"
}


MAXIMO_REGISTROS_IMPORTACION = 50000


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def convertir_fecha(valor):
    """
    Convierte una fecha recibida en formato ISO a datetime.

    Formatos aceptados, por ejemplo:

    2026-08-30T20:30:00
    2026-08-30 20:30:00
    """

    if not valor:
        return None

    valor = str(valor).strip()

    try:
        return datetime.fromisoformat(valor)

    except ValueError:
        return None


def limpiar_texto(valor):
    """
    Elimina espacios al inicio y al final.

    Retorna None cuando el valor se encuentra vacío.
    """

    if valor is None:
        return None

    valor = str(valor).strip()

    return valor if valor else None


def normalizar_resultado(valor):
    """
    Normaliza el resultado del evento.
    """

    resultado = limpiar_texto(valor)

    if not resultado:
        return None

    return resultado.upper()


# ============================================================
# LISTAR EVENTOS
# ============================================================

@eventos_bp.get("")
@jwt_required()
def listar_eventos():

    consulta = EventoSeguridad.query

    # --------------------------------------------------------
    # FILTRO POR FUENTE
    # --------------------------------------------------------

    id_fuente = request.args.get(
        "id_fuente",
        type=int
    )

    if id_fuente is not None:
        consulta = consulta.filter(
            EventoSeguridad.id_fuente == id_fuente
        )

    # --------------------------------------------------------
    # FILTRO POR TIPO DE EVENTO
    # --------------------------------------------------------

    id_tipo_evento = request.args.get(
        "id_tipo_evento",
        type=int
    )

    if id_tipo_evento is not None:
        consulta = consulta.filter(
            EventoSeguridad.id_tipo_evento == id_tipo_evento
        )

    # --------------------------------------------------------
    # FILTRO POR SEVERIDAD
    # --------------------------------------------------------

    severidad = request.args.get("severidad")

    if severidad:

        severidad = severidad.strip().upper()

        consulta = consulta.filter(
            EventoSeguridad.severidad == severidad
        )

    # --------------------------------------------------------
    # FILTRO POR USUARIO
    # --------------------------------------------------------

    usuario_origen = request.args.get(
        "usuario_origen"
    )

    if usuario_origen:

        consulta = consulta.filter(
            EventoSeguridad.usuario_origen.ilike(
                f"%{usuario_origen.strip()}%"
            )
        )

    # --------------------------------------------------------
    # FILTRO POR DIRECCIÓN IP
    # --------------------------------------------------------

    direccion_ip = request.args.get(
        "direccion_ip"
    )

    if direccion_ip:

        consulta = consulta.filter(
            EventoSeguridad.direccion_ip
            == direccion_ip.strip()
        )

    # --------------------------------------------------------
    # FILTRO POR RESULTADO
    # --------------------------------------------------------

    resultado = request.args.get(
        "resultado"
    )

    if resultado:

        consulta = consulta.filter(
            EventoSeguridad.resultado.ilike(
                f"%{resultado.strip()}%"
            )
        )

    # --------------------------------------------------------
    # FILTRO POR FECHA DESDE
    # --------------------------------------------------------

    fecha_desde = request.args.get(
        "fecha_desde"
    )

    if fecha_desde:

        fecha_desde_convertida = convertir_fecha(
            fecha_desde
        )

        if fecha_desde_convertida is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La fecha_desde no posee "
                    "un formato válido."
                )
            }), 400

        consulta = consulta.filter(
            EventoSeguridad.fecha_hora
            >= fecha_desde_convertida
        )

    # --------------------------------------------------------
    # FILTRO POR FECHA HASTA
    # --------------------------------------------------------

    fecha_hasta = request.args.get(
        "fecha_hasta"
    )

    if fecha_hasta:

        fecha_hasta_convertida = convertir_fecha(
            fecha_hasta
        )

        if fecha_hasta_convertida is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La fecha_hasta no posee "
                    "un formato válido."
                )
            }), 400

        consulta = consulta.filter(
            EventoSeguridad.fecha_hora
            <= fecha_hasta_convertida
        )

    # --------------------------------------------------------
    # PAGINACIÓN
    # --------------------------------------------------------

    pagina = request.args.get(
        "pagina",
        default=1,
        type=int
    )

    por_pagina = request.args.get(
        "por_pagina",
        default=50,
        type=int
    )

    if pagina < 1:
        pagina = 1

    if por_pagina < 1:
        por_pagina = 50

    if por_pagina > 200:
        por_pagina = 200

    paginacion = (
        consulta
        .order_by(
            EventoSeguridad.fecha_hora.desc()
        )
        .paginate(
            page=pagina,
            per_page=por_pagina,
            error_out=False
        )
    )

    return jsonify({
        "estado": "OK",
        "total": paginacion.total,
        "pagina": paginacion.page,
        "por_pagina": paginacion.per_page,
        "paginas": paginacion.pages,
        "data": [
            evento.to_dict()
            for evento in paginacion.items
        ]
    }), 200


# ============================================================
# IMPORTAR EVENTOS DESDE CSV
# ============================================================

@eventos_bp.post("/importar")
@jwt_required()
def importar_eventos():
    """
    Importa eventos de seguridad desde un archivo CSV.

    El archivo debe enviarse mediante multipart/form-data
    utilizando el campo:

        archivo

    Columnas requeridas:

        id_fuente
        id_tipo_evento
        fecha_hora
        usuario_origen
        direccion_ip
        severidad
        resultado
        descripcion
    """

    # ========================================================
    # 1. VALIDAR ARCHIVO
    # ========================================================

    if "archivo" not in request.files:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Debe adjuntar un archivo CSV "
                "utilizando el campo 'archivo'."
            )
        }), 400

    archivo = request.files["archivo"]

    if archivo is None or not archivo.filename:

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No se recibió un archivo válido."
        }), 400

    if not archivo.filename.lower().endswith(".csv"):

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El archivo debe utilizar "
                "la extensión .csv."
            )
        }), 400

    # ========================================================
    # 2. LEER ARCHIVO
    # ========================================================

    try:

        contenido_bytes = archivo.read()

        contenido_texto = contenido_bytes.decode(
            "utf-8-sig"
        )

    except UnicodeDecodeError:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El archivo CSV no utiliza "
                "una codificación UTF-8 válida."
            )
        }), 400

    except Exception:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible leer "
                "el archivo CSV."
            )
        }), 400

    # ========================================================
    # 3. CREAR LECTOR CSV
    # ========================================================

    try:

        lector = csv.DictReader(
            io.StringIO(contenido_texto)
        )

    except Exception:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible interpretar "
                "el archivo CSV."
            )
        }), 400

    # ========================================================
    # 4. VALIDAR ENCABEZADOS
    # ========================================================

    if not lector.fieldnames:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El archivo CSV no contiene "
                "encabezados."
            )
        }), 400

    columnas_archivo = {
        str(columna).strip()
        for columna in lector.fieldnames
        if columna
    }

    columnas_faltantes = (
        COLUMNAS_CSV_REQUERIDAS
        - columnas_archivo
    )

    if columnas_faltantes:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El archivo CSV no contiene "
                "todas las columnas requeridas."
            ),
            "columnas_faltantes": sorted(
                columnas_faltantes
            ),
            "columnas_requeridas": sorted(
                COLUMNAS_CSV_REQUERIDAS
            )
        }), 400

    # ========================================================
    # 5. OBTENER FUENTES ACTIVAS
    # ========================================================

    fuentes_activas = {
        fuente.id_fuente
        for fuente in FuenteEvento.query.filter_by(
            estado=True
        ).all()
    }

    if not fuentes_activas:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No existen fuentes de eventos "
                "activas en VIGIA."
            )
        }), 400

    # ========================================================
    # 6. OBTENER TIPOS ACTIVOS
    # ========================================================

    tipos_activos = {
        tipo.id_tipo_evento
        for tipo in TipoEvento.query.filter_by(
            estado=True
        ).all()
    }

    if not tipos_activos:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No existen tipos de eventos "
                "activos en VIGIA."
            )
        }), 400

    # ========================================================
    # 7. PROCESAR REGISTROS
    # ========================================================

    eventos_validos = []

    errores = []

    registros_recibidos = 0

    registros_rechazados = 0

    for numero_fila, fila in enumerate(
        lector,
        start=2
    ):

        # Ignorar filas completamente vacías.

        if not any(
            limpiar_texto(valor)
            for valor in fila.values()
        ):
            continue

        registros_recibidos += 1

        # ----------------------------------------------------
        # LÍMITE
        # ----------------------------------------------------

        if (
            registros_recibidos
            > MAXIMO_REGISTROS_IMPORTACION
        ):

            db.session.rollback()

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El archivo supera el máximo "
                    f"permitido de "
                    f"{MAXIMO_REGISTROS_IMPORTACION:,} "
                    "registros."
                )
            }), 400

        errores_fila = []

        # ----------------------------------------------------
        # FUENTE
        # ----------------------------------------------------

        try:

            id_fuente = int(
                limpiar_texto(
                    fila.get("id_fuente")
                )
            )

        except (TypeError, ValueError):

            id_fuente = None

            errores_fila.append(
                "id_fuente inválido"
            )

        if (
            id_fuente is not None
            and id_fuente not in fuentes_activas
        ):

            errores_fila.append(
                "la fuente no existe o está desactivada"
            )

        # ----------------------------------------------------
        # TIPO DE EVENTO
        # ----------------------------------------------------

        try:

            id_tipo_evento = int(
                limpiar_texto(
                    fila.get(
                        "id_tipo_evento"
                    )
                )
            )

        except (TypeError, ValueError):

            id_tipo_evento = None

            errores_fila.append(
                "id_tipo_evento inválido"
            )

        if (
            id_tipo_evento is not None
            and id_tipo_evento not in tipos_activos
        ):

            errores_fila.append(
                "el tipo de evento no existe "
                "o está desactivado"
            )

        # ----------------------------------------------------
        # FECHA
        # ----------------------------------------------------

        fecha_hora = convertir_fecha(
            fila.get("fecha_hora")
        )

        if fecha_hora is None:

            errores_fila.append(
                "fecha_hora inválida"
            )

        # ----------------------------------------------------
        # SEVERIDAD
        # ----------------------------------------------------

        severidad = limpiar_texto(
            fila.get("severidad")
        )

        if severidad:

            severidad = severidad.upper()

        if (
            not severidad
            or severidad
            not in SEVERIDADES_VALIDAS
        ):

            errores_fila.append(
                "severidad inválida"
            )

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        resultado = normalizar_resultado(
            fila.get("resultado")
        )

        if (
            not resultado
            or resultado
            not in RESULTADOS_VALIDOS
        ):

            errores_fila.append(
                "resultado inválido"
            )

        # ----------------------------------------------------
        # CAMPOS OPCIONALES
        # ----------------------------------------------------

        usuario_origen = limpiar_texto(
            fila.get("usuario_origen")
        )

        direccion_ip = limpiar_texto(
            fila.get("direccion_ip")
        )

        descripcion = limpiar_texto(
            fila.get("descripcion")
        )

        # ----------------------------------------------------
        # REGISTRO INVÁLIDO
        # ----------------------------------------------------

        if errores_fila:

            registros_rechazados += 1

            # Guardamos solamente los primeros
            # errores para no generar una respuesta
            # excesivamente grande.

            if len(errores) < 20:

                errores.append({
                    "fila": numero_fila,
                    "errores": errores_fila
                })

            continue

        # ----------------------------------------------------
        # CREAR OBJETO
        # ----------------------------------------------------

        evento = EventoSeguridad(
            id_fuente=id_fuente,
            id_tipo_evento=id_tipo_evento,
            fecha_hora=fecha_hora,
            usuario_origen=usuario_origen,
            direccion_ip=direccion_ip,
            severidad=severidad,
            resultado=resultado,
            descripcion=descripcion
        )

        eventos_validos.append(
            evento
        )

    # ========================================================
    # 8. VALIDAR CONTENIDO
    # ========================================================

    if registros_recibidos == 0:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El archivo CSV no contiene "
                "registros para importar."
            )
        }), 400

    registros_importados = len(
        eventos_validos
    )

    # ========================================================
    # 9. GUARDAR EVENTOS
    # ========================================================

    try:

        if eventos_validos:

            db.session.add_all(
                eventos_validos
            )

            db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR IMPORTACIÓN MASIVA:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al guardar "
                "los eventos importados."
            )
        }), 500

    # ========================================================
    # 10. RESPUESTA
    # ========================================================

    if registros_rechazados == 0:

        estado_importacion = "COMPLETA"

        mensaje = (
            "Importación masiva completada "
            "correctamente."
        )

    else:

        estado_importacion = "PARCIAL"

        mensaje = (
            "La importación finalizó, pero algunos "
            "registros fueron rechazados."
        )

    return jsonify({
        "estado": "OK",
        "mensaje": mensaje,
        "data": {
            "estado_importacion":
                estado_importacion,

            "archivo":
                archivo.filename,

            "registros_recibidos":
                registros_recibidos,

            "registros_importados":
                registros_importados,

            "registros_rechazados":
                registros_rechazados,

            "errores_mostrados":
                errores
        }
    }), 201


# ============================================================
# OBTENER EVENTO POR ID
# ============================================================

@eventos_bp.get("/<int:id_evento>")
@jwt_required()
def obtener_evento(id_evento):

    evento = db.session.get(
        EventoSeguridad,
        id_evento
    )

    if evento is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Evento de seguridad no encontrado."
            )
        }), 404

    return jsonify({
        "estado": "OK",
        "data": evento.to_dict()
    }), 200


# ============================================================
# CREAR EVENTO
# ============================================================

@eventos_bp.post("")
@jwt_required()
def crear_evento():

    datos = request.get_json(
        silent=True
    )

    if not datos:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Debe enviar datos "
                "en formato JSON."
            )
        }), 400

    # ========================================================
    # FUENTE
    # ========================================================

    try:

        id_fuente = int(
            datos.get("id_fuente")
        )

    except (TypeError, ValueError):

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El id_fuente es obligatorio "
                "y debe ser válido."
            )
        }), 400

    fuente = db.session.get(
        FuenteEvento,
        id_fuente
    )

    if fuente is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La fuente de eventos indicada "
                "no existe."
            )
        }), 400

    if not fuente.estado:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La fuente de eventos "
                "se encuentra desactivada."
            )
        }), 400

    # ========================================================
    # TIPO DE EVENTO
    # ========================================================

    try:

        id_tipo_evento = int(
            datos.get(
                "id_tipo_evento"
            )
        )

    except (TypeError, ValueError):

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El id_tipo_evento es obligatorio "
                "y debe ser válido."
            )
        }), 400

    tipo_evento = db.session.get(
        TipoEvento,
        id_tipo_evento
    )

    if tipo_evento is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El tipo de evento indicado "
                "no existe."
            )
        }), 400

    if not tipo_evento.estado:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El tipo de evento "
                "se encuentra desactivado."
            )
        }), 400

    # ========================================================
    # FECHA Y HORA
    # ========================================================

    fecha_hora = convertir_fecha(
        datos.get("fecha_hora")
    )

    if fecha_hora is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La fecha_hora es obligatoria "
                "y debe utilizar un formato válido."
            )
        }), 400

    # ========================================================
    # SEVERIDAD
    # ========================================================

    severidad = limpiar_texto(
        datos.get("severidad")
    )

    if not severidad:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La severidad es obligatoria."
            )
        }), 400

    severidad = severidad.upper()

    if severidad not in SEVERIDADES_VALIDAS:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La severidad indicada "
                "no es válida."
            ),
            "valores_permitidos": sorted(
                SEVERIDADES_VALIDAS
            )
        }), 400

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = normalizar_resultado(
        datos.get("resultado")
    )

    if not resultado:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El resultado es obligatorio."
            )
        }), 400

    if resultado not in RESULTADOS_VALIDOS:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El resultado indicado "
                "no es válido."
            ),
            "valores_permitidos": sorted(
                RESULTADOS_VALIDOS
            )
        }), 400

    # ========================================================
    # CAMPOS OPCIONALES
    # ========================================================

    usuario_origen = limpiar_texto(
        datos.get("usuario_origen")
    )

    direccion_ip = limpiar_texto(
        datos.get("direccion_ip")
    )

    descripcion = limpiar_texto(
        datos.get("descripcion")
    )

    # ========================================================
    # CREAR REGISTRO
    # ========================================================

    nuevo_evento = EventoSeguridad(
        id_fuente=id_fuente,
        id_tipo_evento=id_tipo_evento,
        fecha_hora=fecha_hora,
        usuario_origen=usuario_origen,
        direccion_ip=direccion_ip,
        severidad=severidad,
        resultado=resultado,
        descripcion=descripcion
    )

    try:

        db.session.add(
            nuevo_evento
        )

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Evento de seguridad "
                "registrado correctamente."
            ),
            "data": nuevo_evento.to_dict()
        }), 201

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR CREAR EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al registrar "
                "el evento de seguridad."
            )
        }), 500


# ============================================================
# ACTUALIZAR EVENTO
# ============================================================

@eventos_bp.put("/<int:id_evento>")
@jwt_required()
def actualizar_evento(id_evento):

    evento = db.session.get(
        EventoSeguridad,
        id_evento
    )

    if evento is None:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Evento de seguridad no encontrado."
            )
        }), 404

    datos = request.get_json(
        silent=True
    )

    if not datos:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Debe enviar datos "
                "en formato JSON."
            )
        }), 400

    # --------------------------------------------------------
    # FUENTE
    # --------------------------------------------------------

    if "id_fuente" in datos:

        try:

            id_fuente = int(
                datos.get(
                    "id_fuente"
                )
            )

        except (TypeError, ValueError):

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El id_fuente no es válido."
                )
            }), 400

        fuente = db.session.get(
            FuenteEvento,
            id_fuente
        )

        if fuente is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La fuente indicada no existe."
                )
            }), 400

        if not fuente.estado:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La fuente indicada "
                    "se encuentra desactivada."
                )
            }), 400

        evento.id_fuente = (
            id_fuente
        )

    # --------------------------------------------------------
    # TIPO DE EVENTO
    # --------------------------------------------------------

    if "id_tipo_evento" in datos:

        try:

            id_tipo_evento = int(
                datos.get(
                    "id_tipo_evento"
                )
            )

        except (TypeError, ValueError):

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El id_tipo_evento "
                    "no es válido."
                )
            }), 400

        tipo_evento = db.session.get(
            TipoEvento,
            id_tipo_evento
        )

        if tipo_evento is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El tipo de evento "
                    "indicado no existe."
                )
            }), 400

        if not tipo_evento.estado:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El tipo de evento indicado "
                    "se encuentra desactivado."
                )
            }), 400

        evento.id_tipo_evento = (
            id_tipo_evento
        )

    # --------------------------------------------------------
    # FECHA
    # --------------------------------------------------------

    if "fecha_hora" in datos:

        fecha_hora = convertir_fecha(
            datos.get(
                "fecha_hora"
            )
        )

        if fecha_hora is None:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La fecha_hora no posee "
                    "un formato válido."
                )
            }), 400

        evento.fecha_hora = (
            fecha_hora
        )

    # --------------------------------------------------------
    # SEVERIDAD
    # --------------------------------------------------------

    if "severidad" in datos:

        severidad = limpiar_texto(
            datos.get(
                "severidad"
            )
        )

        if not severidad:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La severidad no puede "
                    "estar vacía."
                )
            }), 400

        severidad = (
            severidad.upper()
        )

        if (
            severidad
            not in SEVERIDADES_VALIDAS
        ):

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La severidad indicada "
                    "no es válida."
                ),
                "valores_permitidos": sorted(
                    SEVERIDADES_VALIDAS
                )
            }), 400

        evento.severidad = (
            severidad
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if "resultado" in datos:

        resultado = normalizar_resultado(
            datos.get(
                "resultado"
            )
        )

        if not resultado:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El resultado no puede "
                    "estar vacío."
                )
            }), 400

        if resultado not in RESULTADOS_VALIDOS:

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El resultado indicado "
                    "no es válido."
                ),
                "valores_permitidos": sorted(
                    RESULTADOS_VALIDOS
                )
            }), 400

        evento.resultado = (
            resultado
        )

    # --------------------------------------------------------
    # CAMPOS OPCIONALES
    # --------------------------------------------------------

    if "usuario_origen" in datos:

        evento.usuario_origen = limpiar_texto(
            datos.get(
                "usuario_origen"
            )
        )

    if "direccion_ip" in datos:

        evento.direccion_ip = limpiar_texto(
            datos.get(
                "direccion_ip"
            )
        )

    if "descripcion" in datos:

        evento.descripcion = limpiar_texto(
            datos.get(
                "descripcion"
            )
        )

    # --------------------------------------------------------
    # GUARDAR CAMBIOS
    # --------------------------------------------------------

    try:

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Evento de seguridad "
                "actualizado correctamente."
            ),
            "data": evento.to_dict()
        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR ACTUALIZAR EVENTO:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "el evento de seguridad."
            )
        }), 500
    