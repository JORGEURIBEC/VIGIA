from flask import request, has_request_context
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import Auditoria


def obtener_ip_cliente():
    """
    Obtiene la dirección IP desde donde se realizó
    una operación sobre VIGIA.
    """

    if not has_request_context():
        return None

    # Si posteriormente VIGIA está detrás de un proxy/hosting,
    # se intenta recuperar la IP original.
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.remote_addr


def obtener_id_usuario_actual():
    """
    Obtiene el identificador del usuario autenticado
    desde el token JWT.
    """

    try:
        identidad = get_jwt_identity()

        if identidad is None:
            return None

        try:
            return int(identidad)

        except (TypeError, ValueError):
            return None

    except Exception:
        return None


def registrar_auditoria(
    accion,
    entidad_afectada,
    id_registro_afectado=None,
    resultado="OK",
    detalle=None,
    id_usuario=None
):
    """
    Registra automáticamente una operación relevante
    realizada dentro de VIGIA.

    Parámetros:
    - accion:
        Acción ejecutada.
        Ejemplo: CREAR_INCIDENTE.

    - entidad_afectada:
        Módulo o entidad afectada.
        Ejemplo: INCIDENTE.

    - id_registro_afectado:
        ID del registro involucrado.

    - resultado:
        Resultado de la operación.
        Generalmente OK o ERROR.

    - detalle:
        Descripción adicional de la operación.

    - id_usuario:
        Permite indicar manualmente un usuario.
        Si no se proporciona, se obtiene desde el JWT.
    """

    try:

        # ----------------------------------------------------
        # Usuario autenticado
        # ----------------------------------------------------

        if id_usuario is None:
            id_usuario = obtener_id_usuario_actual()

        # ----------------------------------------------------
        # Dirección IP
        # ----------------------------------------------------

        direccion_ip = obtener_ip_cliente()

        # ----------------------------------------------------
        # Crear registro
        # ----------------------------------------------------

        registro = Auditoria(
            id_usuario=id_usuario,
            accion=str(accion).strip(),
            entidad_afectada=str(entidad_afectada).strip(),
            id_registro_afectado=id_registro_afectado,
            resultado=str(resultado).strip().upper(),
            detalle=detalle,
            direccion_ip=direccion_ip
        )

        db.session.add(registro)
        db.session.commit()

        return True

    except Exception as e:

        db.session.rollback()

        print(
            "ERROR AL REGISTRAR AUDITORÍA:",
            type(e).__name__,
            str(e)
        )

        return False
    