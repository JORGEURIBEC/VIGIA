from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.models import Auditoria, Usuario
from app.decorators import roles_required


auditoria_bp = Blueprint(
    "auditoria",
    __name__,
    url_prefix="/api/v1/auditoria"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def obtener_usuario_por_id(id_usuario):
    if id_usuario is None:
        return None

    try:
        return db.session.get(
            Usuario,
            int(id_usuario)
        )
    except (TypeError, ValueError):
        return None


def auditoria_a_dict(registro, usuario=None):
    """
    Convierte un registro de auditoría en un diccionario JSON.

    La información del usuario se agrega únicamente como apoyo
    para la consulta visual; no modifica el registro de auditoría.
    """

    if usuario is None:
        usuario = obtener_usuario_por_id(
            registro.id_usuario
        )

    return {
        "id_auditoria": registro.id_auditoria,
        "id_usuario": registro.id_usuario,
        "usuario_nombre": (
            f"{usuario.nombre} {usuario.apellido}".strip()
            if usuario
            else None
        ),
        "usuario_correo": (
            usuario.correo
            if usuario
            else None
        ),
        "usuario_rol": (
            usuario.rol.nombre_rol
            if usuario and usuario.rol
            else None
        ),
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


def parsear_entero(nombre_parametro, valor, minimo=None, maximo=None):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(
            f"El parámetro {nombre_parametro} debe ser numérico."
        )

    if minimo is not None and numero < minimo:
        numero = minimo

    if maximo is not None and numero > maximo:
        numero = maximo

    return numero


# ============================================================
# GET /api/v1/auditoria
# LISTAR REGISTROS DE AUDITORÍA
# ============================================================

@auditoria_bp.get("")
@roles_required("ADMINISTRADOR")
def listar_auditoria():
    """
    Lista los registros de auditoría de VIGIA.

    Acceso exclusivo para ADMINISTRADOR.

    Filtros disponibles:
    - texto
    - id_usuario
    - accion
    - entidad
    - id_registro_afectado
    - resultado
    - direccion_ip
    - fecha_desde
    - fecha_hasta
    - limite
    - offset
    """

    try:
        consulta = Auditoria.query

        # ----------------------------------------------------
        # BÚSQUEDA GENERAL
        # ----------------------------------------------------

        texto = normalizar_texto(
            request.args.get("texto")
        )

        if texto:
            patron = f"%{texto}%"

            consulta = consulta.filter(
                db.or_(
                    Auditoria.accion.ilike(patron),
                    Auditoria.entidad_afectada.ilike(patron),
                    Auditoria.resultado.ilike(patron),
                    Auditoria.detalle.ilike(patron),
                    Auditoria.direccion_ip.ilike(patron)
                )
            )

        # ----------------------------------------------------
        # FILTRO POR USUARIO
        # ----------------------------------------------------

        id_usuario = normalizar_texto(
            request.args.get("id_usuario")
        )

        if id_usuario:
            try:
                id_usuario_num = int(id_usuario)
            except ValueError:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El parámetro id_usuario "
                        "debe ser numérico."
                    )
                }), 400

            consulta = consulta.filter(
                Auditoria.id_usuario == id_usuario_num
            )

        # ----------------------------------------------------
        # FILTRO POR ACCIÓN
        # ----------------------------------------------------

        accion = normalizar_texto(
            request.args.get("accion")
        )

        if accion:
            consulta = consulta.filter(
                Auditoria.accion == accion
            )

        # ----------------------------------------------------
        # FILTRO POR ENTIDAD
        # ----------------------------------------------------

        entidad = normalizar_texto(
            request.args.get("entidad")
        )

        if entidad:
            consulta = consulta.filter(
                Auditoria.entidad_afectada == entidad
            )

        # ----------------------------------------------------
        # FILTRO POR ID DEL REGISTRO AFECTADO
        # ----------------------------------------------------

        id_registro_afectado = normalizar_texto(
            request.args.get("id_registro_afectado")
        )

        if id_registro_afectado:
            try:
                id_registro_num = int(
                    id_registro_afectado
                )
            except ValueError:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "El parámetro id_registro_afectado "
                        "debe ser numérico."
                    )
                }), 400

            consulta = consulta.filter(
                Auditoria.id_registro_afectado
                == id_registro_num
            )

        # ----------------------------------------------------
        # FILTRO POR RESULTADO
        # ----------------------------------------------------

        resultado = normalizar_texto(
            request.args.get("resultado")
        ).upper()

        if resultado:
            consulta = consulta.filter(
                Auditoria.resultado == resultado
            )

        # ----------------------------------------------------
        # FILTRO POR IP
        # ----------------------------------------------------

        direccion_ip = normalizar_texto(
            request.args.get("direccion_ip")
        )

        if direccion_ip:
            consulta = consulta.filter(
                Auditoria.direccion_ip.ilike(
                    f"%{direccion_ip}%"
                )
            )

        # ----------------------------------------------------
        # FILTRO DESDE FECHA
        # Formato: YYYY-MM-DD
        # ----------------------------------------------------

        fecha_desde = normalizar_texto(
            request.args.get("fecha_desde")
        )

        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(
                    fecha_desde,
                    "%Y-%m-%d"
                )
            except ValueError:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "fecha_desde debe utilizar "
                        "el formato YYYY-MM-DD."
                    )
                }), 400

            consulta = consulta.filter(
                Auditoria.fecha_hora >= fecha_desde_obj
            )

        # ----------------------------------------------------
        # FILTRO HASTA FECHA
        # ----------------------------------------------------

        fecha_hasta = normalizar_texto(
            request.args.get("fecha_hasta")
        )

        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(
                    fecha_hasta,
                    "%Y-%m-%d"
                ).replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999
                )
            except ValueError:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": (
                        "fecha_hasta debe utilizar "
                        "el formato YYYY-MM-DD."
                    )
                }), 400

            consulta = consulta.filter(
                Auditoria.fecha_hora <= fecha_hasta_obj
            )

        # ----------------------------------------------------
        # PAGINACIÓN SIMPLE
        # ----------------------------------------------------

        try:
            limite = parsear_entero(
                "limite",
                request.args.get("limite", 200),
                minimo=1,
                maximo=500
            )

            offset = parsear_entero(
                "offset",
                request.args.get("offset", 0),
                minimo=0
            )
        except ValueError as error:
            return jsonify({
                "estado": "ERROR",
                "mensaje": str(error)
            }), 400

        # ----------------------------------------------------
        # RESUMEN DEL CONJUNTO FILTRADO
        # ----------------------------------------------------

        total_filtrado = consulta.count()

        total_ok = (
            consulta
            .filter(Auditoria.resultado == "OK")
            .count()
        )

        total_error = (
            consulta
            .filter(Auditoria.resultado == "ERROR")
            .count()
        )

        usuarios_involucrados = (
            consulta
            .filter(Auditoria.id_usuario.isnot(None))
            .with_entities(Auditoria.id_usuario)
            .distinct()
            .count()
        )

        # ----------------------------------------------------
        # OBTENER REGISTROS
        # ----------------------------------------------------

        registros = (
            consulta
            .order_by(
                Auditoria.fecha_hora.desc(),
                Auditoria.id_auditoria.desc()
            )
            .offset(offset)
            .limit(limite)
            .all()
        )

        # ----------------------------------------------------
        # CARGA DE USUARIOS EN BLOQUE
        # ----------------------------------------------------

        ids_usuario = {
            registro.id_usuario
            for registro in registros
            if registro.id_usuario is not None
        }

        usuarios = {}

        if ids_usuario:
            usuarios_consulta = (
                Usuario.query
                .filter(Usuario.id_usuario.in_(ids_usuario))
                .all()
            )

            usuarios = {
                usuario.id_usuario: usuario
                for usuario in usuarios_consulta
            }

        data = [
            auditoria_a_dict(
                registro,
                usuarios.get(registro.id_usuario)
            )
            for registro in registros
        ]

        return jsonify({
            "estado": "OK",
            "total": len(data),
            "total_filtrado": total_filtrado,
            "limite": limite,
            "offset": offset,
            "resumen": {
                "total": total_filtrado,
                "ok": total_ok,
                "error": total_error,
                "usuarios": usuarios_involucrados
            },
            "data": data
        }), 200

    except Exception as error:
        print(
            "ERROR AL LISTAR AUDITORÍA:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "los registros de auditoría."
            )
        }), 500


# ============================================================
# GET /api/v1/auditoria/<id_auditoria>
# OBTENER UN REGISTRO ESPECÍFICO
# ============================================================

@auditoria_bp.get("/<int:id_auditoria>")
@roles_required("ADMINISTRADOR")
def obtener_auditoria(id_auditoria):
    """
    Obtiene un registro específico de auditoría.
    Acceso exclusivo para ADMINISTRADOR.
    """

    try:
        registro = db.session.get(
            Auditoria,
            id_auditoria
        )

        if registro is None:
            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "Registro de auditoría "
                    "no encontrado."
                )
            }), 404

        usuario = obtener_usuario_por_id(
            registro.id_usuario
        )

        return jsonify({
            "estado": "OK",
            "data": auditoria_a_dict(
                registro,
                usuario
            )
        }), 200

    except Exception as error:
        print(
            "ERROR AL OBTENER AUDITORÍA:",
            type(error).__name__,
            str(error)
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "Ocurrió un error al consultar "
                "el registro de auditoría."
            )
        }), 500
