from flask import Blueprint, jsonify, request

from app import db
from app.models import ReglaDeteccion
from app.decorators import roles_required


reglas_bp = Blueprint(
    "reglas",
    __name__,
    url_prefix="/api/v1/reglas"
)


# ============================================================
# CONFIGURACIÓN DE VALORES PERMITIDOS
# ============================================================

TIPOS_CONDICION_PERMITIDOS = {
    "AUTENTICACIONES_FALLIDAS",
    "MISMA_IP",
    "EVENTO_CRITICO",
    "FUERA_HORARIO"
}

SEVERIDADES_PERMITIDAS = {
    "BAJA",
    "MEDIA",
    "ALTA",
    "CRITICA"
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    """
    Convierte un valor a texto y elimina espacios
    innecesarios al comienzo y al final.
    """
    if valor is None:
        return ""
    return str(valor).strip()


def validar_entero_no_negativo(valor, nombre_campo):
    """
    Valida que un valor pueda convertirse a entero
    y que no sea negativo.
    """
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None, f"El campo '{nombre_campo}' debe ser un número entero."

    if numero < 0:
        return None, f"El campo '{nombre_campo}' no puede ser negativo."

    return numero, None


# ============================================================
# LISTAR REGLAS
# GET /api/v1/reglas
# ============================================================

@reglas_bp.get("")
@roles_required("ADMINISTRADOR")
def listar_reglas():
    """
    Lista todas las reglas de detección registradas en VIGIA.

    Acceso exclusivo para ADMINISTRADOR.
    """

    reglas = ReglaDeteccion.query.order_by(
        ReglaDeteccion.id_regla
    ).all()

    return jsonify({
        "estado": "OK",
        "total": len(reglas),
        "data": [
            regla.to_dict()
            for regla in reglas
        ]
    }), 200


# ============================================================
# OBTENER REGLA POR ID
# GET /api/v1/reglas/<id_regla>
# ============================================================

@reglas_bp.get("/<int:id_regla>")
@roles_required("ADMINISTRADOR")
def obtener_regla(id_regla):
    """
    Obtiene una regla de detección específica mediante su ID.
    """

    regla = ReglaDeteccion.query.filter_by(
        id_regla=id_regla
    ).first()

    if not regla:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Regla de detección no encontrada."
        }), 404

    return jsonify({
        "estado": "OK",
        "data": regla.to_dict()
    }), 200


# ============================================================
# CREAR REGLA
# POST /api/v1/reglas
# ============================================================

@reglas_bp.post("")
@roles_required("ADMINISTRADOR")
def crear_regla():
    """
    Registra una nueva regla de detección.

    Campos requeridos:
    - nombre
    - descripcion
    - tipo_condicion
    - umbral
    - intervalo_minutos
    - severidad_alerta
    """

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar datos en formato JSON."
        }), 400

    # ========================================================
    # NOMBRE
    # ========================================================

    nombre = normalizar_texto(
        datos.get("nombre")
    )

    if not nombre:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "El nombre de la regla es obligatorio."
        }), 400

    if len(nombre) > 120:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El nombre no puede superar "
                "los 120 caracteres."
            )
        }), 400

    regla_existente = ReglaDeteccion.query.filter(
        db.func.lower(ReglaDeteccion.nombre)
        == nombre.lower()
    ).first()

    if regla_existente:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ya existe una regla de detección "
                "registrada con ese nombre."
            )
        }), 409

    # ========================================================
    # DESCRIPCIÓN
    # ========================================================

    descripcion = normalizar_texto(
        datos.get("descripcion")
    )

    if not descripcion:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "La descripción es obligatoria."
        }), 400

    if len(descripcion) > 500:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La descripción no puede superar "
                "los 500 caracteres."
            )
        }), 400

    # ========================================================
    # TIPO DE CONDICIÓN
    # ========================================================

    tipo_condicion = normalizar_texto(
        datos.get("tipo_condicion")
    ).upper()

    if tipo_condicion not in TIPOS_CONDICION_PERMITIDOS:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Tipo de condición no válido.",
            "tipos_permitidos": sorted(
                TIPOS_CONDICION_PERMITIDOS
            )
        }), 400

    # ========================================================
    # UMBRAL
    # ========================================================

    umbral, error = validar_entero_no_negativo(
        datos.get("umbral", 1),
        "umbral"
    )

    if error:
        return jsonify({
            "estado": "ERROR",
            "mensaje": error
        }), 400

    if umbral < 1:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El umbral debe ser igual "
                "o superior a 1."
            )
        }), 400

    # ========================================================
    # INTERVALO
    # ========================================================

    intervalo_minutos, error = validar_entero_no_negativo(
        datos.get("intervalo_minutos", 0),
        "intervalo_minutos"
    )

    if error:
        return jsonify({
            "estado": "ERROR",
            "mensaje": error
        }), 400

    # ========================================================
    # SEVERIDAD
    # ========================================================

    severidad_alerta = normalizar_texto(
        datos.get("severidad_alerta")
    ).upper()

    if severidad_alerta not in SEVERIDADES_PERMITIDAS:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Severidad de alerta no válida.",
            "severidades_permitidas": sorted(
                SEVERIDADES_PERMITIDAS
            )
        }), 400

    # ========================================================
    # ESTADO
    # ========================================================

    estado = datos.get("estado", True)

    if not isinstance(estado, bool):
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "El campo 'estado' debe ser "
                "true o false."
            )
        }), 400

    # ========================================================
    # CREAR REGISTRO
    # ========================================================

    nueva_regla = ReglaDeteccion(
        nombre=nombre,
        descripcion=descripcion,
        tipo_condicion=tipo_condicion,
        umbral=umbral,
        intervalo_minutos=intervalo_minutos,
        severidad_alerta=severidad_alerta,
        estado=estado
    )

    try:

        db.session.add(nueva_regla)
        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Regla de detección creada "
                "correctamente."
            ),
            "data": nueva_regla.to_dict()
        }), 201

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al registrar "
                "la regla de detección."
            )
        }), 500


# ============================================================
# ACTUALIZAR REGLA
# PUT /api/v1/reglas/<id_regla>
# ============================================================

@reglas_bp.put("/<int:id_regla>")
@roles_required("ADMINISTRADOR")
def actualizar_regla(id_regla):
    """
    Actualiza los datos de una regla de detección existente.
    """

    regla = ReglaDeteccion.query.filter_by(
        id_regla=id_regla
    ).first()

    if not regla:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Regla de detección no encontrada."
        }), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Debe enviar datos en formato JSON."
        }), 400

    # ========================================================
    # NOMBRE
    # ========================================================

    if "nombre" in datos:

        nombre = normalizar_texto(
            datos.get("nombre")
        )

        if not nombre:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre no puede estar vacío."
                )
            }), 400

        if len(nombre) > 120:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El nombre no puede superar "
                    "los 120 caracteres."
                )
            }), 400

        regla_existente = ReglaDeteccion.query.filter(
            db.func.lower(ReglaDeteccion.nombre)
            == nombre.lower(),
            ReglaDeteccion.id_regla != id_regla
        ).first()

        if regla_existente:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Ya existe otra regla de detección "
                    "con ese nombre."
                )
            }), 409

        regla.nombre = nombre

    # ========================================================
    # DESCRIPCIÓN
    # ========================================================

    if "descripcion" in datos:

        descripcion = normalizar_texto(
            datos.get("descripcion")
        )

        if not descripcion:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La descripción no puede "
                    "estar vacía."
                )
            }), 400

        if len(descripcion) > 500:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La descripción no puede superar "
                    "los 500 caracteres."
                )
            }), 400

        regla.descripcion = descripcion

    # ========================================================
    # TIPO DE CONDICIÓN
    # ========================================================

    if "tipo_condicion" in datos:

        tipo_condicion = normalizar_texto(
            datos.get("tipo_condicion")
        ).upper()

        if tipo_condicion not in TIPOS_CONDICION_PERMITIDOS:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Tipo de condición no válido.",
                "tipos_permitidos": sorted(
                    TIPOS_CONDICION_PERMITIDOS
                )
            }), 400

        regla.tipo_condicion = tipo_condicion

    # ========================================================
    # UMBRAL
    # ========================================================

    if "umbral" in datos:

        umbral, error = validar_entero_no_negativo(
            datos.get("umbral"),
            "umbral"
        )

        if error:
            return jsonify({
                "estado": "ERROR",
                "mensaje": error
            }), 400

        if umbral < 1:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El umbral debe ser igual "
                    "o superior a 1."
                )
            }), 400

        regla.umbral = umbral

    # ========================================================
    # INTERVALO
    # ========================================================

    if "intervalo_minutos" in datos:

        intervalo_minutos, error = (
            validar_entero_no_negativo(
                datos.get("intervalo_minutos"),
                "intervalo_minutos"
            )
        )

        if error:
            return jsonify({
                "estado": "ERROR",
                "mensaje": error
            }), 400

        regla.intervalo_minutos = intervalo_minutos

    # ========================================================
    # SEVERIDAD
    # ========================================================

    if "severidad_alerta" in datos:

        severidad_alerta = normalizar_texto(
            datos.get("severidad_alerta")
        ).upper()

        if severidad_alerta not in SEVERIDADES_PERMITIDAS:
            return jsonify({
                "estado": "ERROR",
                "mensaje": "Severidad de alerta no válida.",
                "severidades_permitidas": sorted(
                    SEVERIDADES_PERMITIDAS
                )
            }), 400

        regla.severidad_alerta = severidad_alerta

    # ========================================================
    # ESTADO
    # ========================================================

    if "estado" in datos:

        estado = datos.get("estado")

        if not isinstance(estado, bool):
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "El campo 'estado' debe ser "
                    "true o false."
                )
            }), 400

        regla.estado = estado

    # ========================================================
    # GUARDAR CAMBIOS
    # ========================================================

    try:

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Regla de detección actualizada "
                "correctamente."
            ),
            "data": regla.to_dict()
        }), 200

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al actualizar "
                "la regla de detección."
            )
        }), 500


# ============================================================
# DESACTIVAR REGLA
# DELETE /api/v1/reglas/<id_regla>
# ============================================================

@reglas_bp.delete("/<int:id_regla>")
@roles_required("ADMINISTRADOR")
def desactivar_regla(id_regla):
    """
    Realiza una eliminación lógica de la regla.

    La regla no se elimina físicamente de MySQL.
    Se cambia su estado a False para conservar
    la trazabilidad.
    """

    regla = ReglaDeteccion.query.filter_by(
        id_regla=id_regla
    ).first()

    if not regla:
        return jsonify({
            "estado": "ERROR",
            "mensaje": "Regla de detección no encontrada."
        }), 404

    if not regla.estado:
        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "La regla de detección ya se "
                "encuentra desactivada."
            )
        }), 409

    try:

        regla.estado = False

        db.session.commit()

        return jsonify({
            "estado": "OK",
            "mensaje": (
                "Regla de detección desactivada "
                "correctamente."
            ),
            "data": regla.to_dict()
        }), 200

    except Exception:

        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al desactivar "
                "la regla de detección."
            )
        }), 500