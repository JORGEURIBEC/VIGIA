from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def roles_required(*roles_permitidos):
    """
    Restringe una ruta a uno o más roles autorizados.

    Ejemplo:
        @roles_required("ADMINISTRADOR")

        @roles_required("ADMINISTRADOR", "ANALISTA")
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            # Verifica que exista un JWT válido
            verify_jwt_in_request()

            # Obtiene los datos adicionales contenidos en el token
            claims = get_jwt()

            rol_usuario = claims.get("rol")

            # Si el rol no está autorizado, se rechaza la solicitud
            if rol_usuario not in roles_permitidos:
                return jsonify({
                    "estado": "ERROR",
                    "mensaje": "No tiene permisos para acceder a este recurso.",
                    "rol": rol_usuario
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator