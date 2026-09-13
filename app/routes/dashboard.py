from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app import db
from app.models import EventoSeguridad, Alerta, Incidente


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/v1/dashboard"
)


@dashboard_bp.route("/resumen", methods=["GET"])
@jwt_required()
def obtener_resumen_dashboard():

    # ---------------------------------------------------------
    # 1. TOTAL DE EVENTOS
    # ---------------------------------------------------------
    total_eventos = EventoSeguridad.query.count()

    # ---------------------------------------------------------
    # 2. EVENTOS POR SEVERIDAD
    # ---------------------------------------------------------
    eventos_severidad = (
        db.session.query(
            EventoSeguridad.severidad,
            func.count(EventoSeguridad.id_evento)
        )
        .group_by(EventoSeguridad.severidad)
        .all()
    )

    eventos_por_severidad = {
        severidad: cantidad
        for severidad, cantidad in eventos_severidad
    }

    # ---------------------------------------------------------
    # 3. EVOLUCIÓN DE EVENTOS POR FECHA
    # ---------------------------------------------------------
    eventos_fecha = (
        db.session.query(
            func.date(EventoSeguridad.fecha_hora).label("fecha"),
            func.count(EventoSeguridad.id_evento)
        )
        .group_by(func.date(EventoSeguridad.fecha_hora))
        .order_by(func.date(EventoSeguridad.fecha_hora))
        .all()
    )

    eventos_por_fecha = {
        str(fecha): cantidad
        for fecha, cantidad in eventos_fecha
    }

    # ---------------------------------------------------------
    # 4. TOTAL DE ALERTAS
    # ---------------------------------------------------------
    total_alertas = Alerta.query.count()

    # ---------------------------------------------------------
    # 5. ALERTAS POR ESTADO
    # ---------------------------------------------------------
    alertas_estado = (
        db.session.query(
            Alerta.estado,
            func.count(Alerta.id_alerta)
        )
        .group_by(Alerta.estado)
        .all()
    )

    alertas_por_estado = {
        estado: cantidad
        for estado, cantidad in alertas_estado
    }

    # ---------------------------------------------------------
    # 6. TOTAL DE INCIDENTES
    # ---------------------------------------------------------
    total_incidentes = Incidente.query.count()

    # ---------------------------------------------------------
    # 7. INCIDENTES POR ESTADO
    # ---------------------------------------------------------
    incidentes_estado = (
        db.session.query(
            Incidente.estado,
            func.count(Incidente.id_incidente)
        )
        .group_by(Incidente.estado)
        .all()
    )

    incidentes_por_estado = {
        estado: cantidad
        for estado, cantidad in incidentes_estado
    }

    # ---------------------------------------------------------
    # 8. INCIDENTES POR PRIORIDAD
    # ---------------------------------------------------------
    incidentes_prioridad = (
        db.session.query(
            Incidente.prioridad,
            func.count(Incidente.id_incidente)
        )
        .group_by(Incidente.prioridad)
        .all()
    )

    incidentes_por_prioridad = {
        prioridad: cantidad
        for prioridad, cantidad in incidentes_prioridad
    }

    # ---------------------------------------------------------
    # RESPUESTA
    # ---------------------------------------------------------
    return jsonify({
        "estado": "OK",
        "data": {
            "total_eventos": total_eventos,
            "eventos_por_severidad": eventos_por_severidad,
            "eventos_por_fecha": eventos_por_fecha,
            "total_alertas": total_alertas,
            "alertas_por_estado": alertas_por_estado,
            "total_incidentes": total_incidentes,
            "incidentes_por_estado": incidentes_por_estado,
            "incidentes_por_prioridad": incidentes_por_prioridad
        }
    }), 200