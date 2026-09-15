from datetime import datetime, timedelta

from sqlalchemy import func, select

from app import db
from app.models import (
    EventoSeguridad,
    Alerta,
    Incidente,
)


class DashboardService:

    # ============================================================
    # TOTAL DE EVENTOS
    # ============================================================

    @staticmethod
    def total_eventos():
        return db.session.scalar(
            select(func.count(EventoSeguridad.id_evento))
        ) or 0

    # ============================================================
    # EVENTOS POR SEVERIDAD
    # ============================================================

    @staticmethod
    def eventos_por_severidad():

        stmt = (
            select(
                EventoSeguridad.severidad,
                func.count(EventoSeguridad.id_evento)
            )
            .group_by(EventoSeguridad.severidad)
            .order_by(EventoSeguridad.severidad)
        )

        resultados = db.session.execute(stmt).all()

        return {
            severidad: cantidad
            for severidad, cantidad in resultados
        }

    # ============================================================
    # TOTAL DE ALERTAS
    # ============================================================

    @staticmethod
    def total_alertas():
        return db.session.scalar(
            select(func.count(Alerta.id_alerta))
        ) or 0

    # ============================================================
    # ALERTAS POR SEVERIDAD
    # ============================================================

    @staticmethod
    def alertas_por_severidad():

        stmt = (
            select(
                Alerta.severidad,
                func.count(Alerta.id_alerta)
            )
            .group_by(Alerta.severidad)
            .order_by(Alerta.severidad)
        )

        resultados = db.session.execute(stmt).all()

        return {
            severidad: cantidad
            for severidad, cantidad in resultados
        }

    # ============================================================
    # ALERTAS POR ESTADO
    # ============================================================

    @staticmethod
    def alertas_por_estado():

        stmt = (
            select(
                Alerta.estado,
                func.count(Alerta.id_alerta)
            )
            .group_by(Alerta.estado)
            .order_by(Alerta.estado)
        )

        resultados = db.session.execute(stmt).all()

        return {
            estado: cantidad
            for estado, cantidad in resultados
        }

    # ============================================================
    # TOTAL DE INCIDENTES
    # ============================================================

    @staticmethod
    def total_incidentes():
        return db.session.scalar(
            select(func.count(Incidente.id_incidente))
        ) or 0

    # ============================================================
    # INCIDENTES POR ESTADO
    # ============================================================

    @staticmethod
    def incidentes_por_estado():

        stmt = (
            select(
                Incidente.estado,
                func.count(Incidente.id_incidente)
            )
            .group_by(Incidente.estado)
            .order_by(Incidente.estado)
        )

        resultados = db.session.execute(stmt).all()

        return {
            estado: cantidad
            for estado, cantidad in resultados
        }

    # ============================================================
    # INCIDENTES POR PRIORIDAD
    # ============================================================

    @staticmethod
    def incidentes_por_prioridad():

        stmt = (
            select(
                Incidente.prioridad,
                func.count(Incidente.id_incidente)
            )
            .group_by(Incidente.prioridad)
            .order_by(Incidente.prioridad)
        )

        resultados = db.session.execute(stmt).all()

        return {
            prioridad: cantidad
            for prioridad, cantidad in resultados
        }

    # ============================================================
    # EVENTOS CRITICOS
    # ============================================================

    @staticmethod
    def total_eventos_criticos():

        stmt = select(
            func.count(EventoSeguridad.id_evento)
        ).where(
            EventoSeguridad.severidad == "CRITICA"
        )

        return db.session.scalar(stmt) or 0

    # ============================================================
    # ALERTAS PENDIENTES
    # ============================================================

    @staticmethod
    def total_alertas_pendientes():

        stmt = select(
            func.count(Alerta.id_alerta)
        ).where(
            Alerta.estado == "PENDIENTE"
        )

        return db.session.scalar(stmt) or 0

    # ============================================================
    # INCIDENTES ABIERTOS
    # ============================================================

    @staticmethod
    def total_incidentes_abiertos():

        estados_abiertos = [
            "ABIERTO",
            "ANALISIS",
            "TRATAMIENTO",
        ]

        stmt = select(
            func.count(Incidente.id_incidente)
        ).where(
            Incidente.estado.in_(estados_abiertos)
        )

        return db.session.scalar(stmt) or 0

    # ============================================================
    # EVOLUCION DE EVENTOS
    # ULTIMOS 7 DIAS
    # ============================================================

    @staticmethod
    def evolucion_eventos(dias=7):

        fecha_inicio = datetime.now() - timedelta(days=dias)

        fecha = func.date(
            EventoSeguridad.fecha_hora
        ).label("fecha")

        stmt = (
            select(
                fecha,
                func.count(
                    EventoSeguridad.id_evento
                ).label("cantidad")
            )
            .where(
                EventoSeguridad.fecha_hora >= fecha_inicio
            )
            .group_by(fecha)
            .order_by(fecha.asc())
        )

        resultados = db.session.execute(stmt).all()

        return [
            {
                "fecha": (
                    registro.fecha.isoformat()
                    if registro.fecha
                    else None
                ),
                "cantidad": registro.cantidad
            }
            for registro in resultados
        ]

    # ============================================================
    # ULTIMOS EVENTOS
    # ============================================================

    @staticmethod
    def ultimos_eventos(limite=10):

        stmt = (
            select(EventoSeguridad)
            .order_by(
                EventoSeguridad.fecha_hora.desc()
            )
            .limit(limite)
        )

        eventos = (
            db.session.execute(stmt)
            .scalars()
            .all()
        )

        return [
            evento.to_dict()
            for evento in eventos
        ]

    # ============================================================
    # ULTIMAS ALERTAS
    # ============================================================

    @staticmethod
    def ultimas_alertas(limite=10):

        stmt = (
            select(Alerta)
            .order_by(
                Alerta.fecha_generacion.desc()
            )
            .limit(limite)
        )

        alertas = (
            db.session.execute(stmt)
            .scalars()
            .all()
        )

        return [
            alerta.to_dict()
            for alerta in alertas
        ]

    # ============================================================
    # RESUMEN COMPLETO DEL DASHBOARD
    # ============================================================

    @classmethod
    def obtener_resumen(cls):

        return {

            "indicadores": {
                "total_eventos":
                    cls.total_eventos(),

                "eventos_criticos":
                    cls.total_eventos_criticos(),

                "total_alertas":
                    cls.total_alertas(),

                "alertas_pendientes":
                    cls.total_alertas_pendientes(),

                "total_incidentes":
                    cls.total_incidentes(),

                "incidentes_abiertos":
                    cls.total_incidentes_abiertos(),
            },

            "eventos_por_severidad":
                cls.eventos_por_severidad(),

            "alertas_por_severidad":
                cls.alertas_por_severidad(),

            "alertas_por_estado":
                cls.alertas_por_estado(),

            "incidentes_por_estado":
                cls.incidentes_por_estado(),

            "incidentes_por_prioridad":
                cls.incidentes_por_prioridad(),

            "evolucion_eventos":
                cls.evolucion_eventos(),

            "ultimos_eventos":
                cls.ultimos_eventos(),

            "ultimas_alertas":
                cls.ultimas_alertas(),
        }
    