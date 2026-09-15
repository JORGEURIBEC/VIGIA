from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.services.dashboard_service import DashboardService


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/v1/dashboard"
)


@dashboard_bp.route("/resumen", methods=["GET"])
@jwt_required()
def obtener_resumen_dashboard():
    """
    Devuelve el resumen general del dashboard de VIGIA.

    La información es obtenida mediante DashboardService,
    manteniendo separada la lógica de negocio de las rutas HTTP.
    """

    try:
        resumen = DashboardService.obtener_resumen()

        return jsonify({
            "estado": "OK",
            "data": resumen
        }), 200

    except Exception as error:

        return jsonify({
            "estado": "ERROR",
            "mensaje": (
                "No fue posible obtener la información "
                "del dashboard."
            ),
            "detalle": str(error)
        }), 500
    