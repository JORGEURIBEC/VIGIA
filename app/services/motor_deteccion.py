from datetime import timedelta

from app import db
from app.models import (
    EventoSeguridad,
    ReglaDeteccion,
    Alerta,
    AlertaEvento
)


# ============================================================
# CONFIGURACION DEL MOTOR
# ============================================================

HORA_INICIO_HABITUAL = 8
HORA_FIN_HABITUAL = 20


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _alerta_ya_existe(id_regla, ids_eventos):
    """
    Comprueba si ya existe una alerta de la misma regla
    asociada a los eventos indicados.
    """

    if not ids_eventos:
        return False

    alertas_existentes = Alerta.query.filter_by(
        id_regla=id_regla
    ).all()

    ids_buscados = set(ids_eventos)

    for alerta in alertas_existentes:

        relaciones = AlertaEvento.query.filter_by(
            id_alerta=alerta.id_alerta
        ).all()

        ids_asociados = {
            relacion.id_evento
            for relacion in relaciones
        }

        if ids_buscados.issubset(ids_asociados):
            return True

    return False


def _crear_alerta(regla, eventos, descripcion):
    """
    Crea una alerta y relaciona los eventos que provocaron
    su generación.
    """

    ids_eventos = [
        evento.id_evento
        for evento in eventos
    ]

    if _alerta_ya_existe(
        regla.id_regla,
        ids_eventos
    ):
        return None

    alerta = Alerta(
        id_regla=regla.id_regla,
        severidad=regla.severidad_alerta,
        descripcion=descripcion,
        estado="PENDIENTE"
    )

    db.session.add(alerta)
    db.session.flush()

    for evento in eventos:

        relacion = AlertaEvento(
            id_alerta=alerta.id_alerta,
            id_evento=evento.id_evento
        )

        db.session.add(relacion)

    return {
        "id_alerta": alerta.id_alerta,
        "id_regla": regla.id_regla,
        "regla": regla.nombre,
        "severidad": regla.severidad_alerta,
        "eventos": ids_eventos
    }


# ============================================================
# REGLA 1
# AUTENTICACIONES FALLIDAS
# ============================================================

def detectar_autenticaciones_fallidas():

    reglas = ReglaDeteccion.query.filter_by(
        tipo_condicion="AUTENTICACIONES_FALLIDAS",
        estado=True
    ).all()

    alertas_generadas = []

    for regla in reglas:

        eventos = (
            EventoSeguridad.query
            .filter(
                EventoSeguridad.resultado == "FALLIDO",
                EventoSeguridad.direccion_ip.isnot(None)
            )
            .order_by(EventoSeguridad.fecha_hora.asc())
            .all()
        )

        eventos_por_ip = {}

        for evento in eventos:

            eventos_por_ip.setdefault(
                evento.direccion_ip,
                []
            ).append(evento)

        for direccion_ip, lista_eventos in eventos_por_ip.items():

            for indice, evento_inicio in enumerate(lista_eventos):

                limite = (
                    evento_inicio.fecha_hora
                    + timedelta(
                        minutes=regla.intervalo_minutos
                    )
                )

                eventos_ventana = [
                    evento
                    for evento in lista_eventos[indice:]
                    if evento.fecha_hora <= limite
                ]

                if len(eventos_ventana) < regla.umbral:
                    continue

                eventos_detectados = (
                    eventos_ventana[:regla.umbral]
                )

                descripcion = (
                    f"Se detectaron "
                    f"{len(eventos_detectados)} intentos "
                    f"fallidos de autenticación desde la "
                    f"dirección IP {direccion_ip} dentro de "
                    f"un intervalo de "
                    f"{regla.intervalo_minutos} minutos."
                )

                resultado = _crear_alerta(
                    regla,
                    eventos_detectados,
                    descripcion
                )

                if resultado:

                    resultado["direccion_ip"] = direccion_ip
                    resultado["cantidad_eventos"] = len(
                        eventos_detectados
                    )

                    alertas_generadas.append(resultado)

                    break

    return {
        "estado": "OK",
        "alertas_generadas": len(alertas_generadas),
        "data": alertas_generadas
    }


# ============================================================
# REGLA 2
# EVENTO CRITICO
# ============================================================

def detectar_eventos_criticos():

    reglas = ReglaDeteccion.query.filter_by(
        tipo_condicion="EVENTO_CRITICO",
        estado=True
    ).all()

    alertas_generadas = []

    for regla in reglas:

        eventos = (
            EventoSeguridad.query
            .filter(
                EventoSeguridad.severidad == "CRITICA"
            )
            .order_by(
                EventoSeguridad.fecha_hora.asc()
            )
            .all()
        )

        for evento in eventos:

            descripcion = (
                f"VIGIA detectó un evento de seguridad "
                f"clasificado con severidad CRITICA. "
                f"Evento ID {evento.id_evento}"
            )

            resultado = _crear_alerta(
                regla,
                [evento],
                descripcion
            )

            if resultado:

                resultado["id_evento"] = evento.id_evento

                alertas_generadas.append(resultado)

    return {
        "estado": "OK",
        "alertas_generadas": len(alertas_generadas),
        "data": alertas_generadas
    }


# ============================================================
# REGLA 3
# ACTIVIDAD FUERA DE HORARIO
# ============================================================

def detectar_fuera_horario():

    reglas = ReglaDeteccion.query.filter_by(
        tipo_condicion="FUERA_HORARIO",
        estado=True
    ).all()

    alertas_generadas = []

    for regla in reglas:

        eventos = (
            EventoSeguridad.query
            .order_by(
                EventoSeguridad.fecha_hora.asc()
            )
            .all()
        )

        for evento in eventos:

            hora = evento.fecha_hora.hour

            fuera_horario = (
                hora < HORA_INICIO_HABITUAL
                or hora >= HORA_FIN_HABITUAL
            )

            if not fuera_horario:
                continue

            descripcion = (
                f"Se detectó actividad de seguridad fuera "
                f"del horario habitual. "
                f"Evento ID {evento.id_evento}, registrado "
                f"a las "
                f"{evento.fecha_hora.strftime('%H:%M:%S')}."
            )

            resultado = _crear_alerta(
                regla,
                [evento],
                descripcion
            )

            if resultado:

                resultado["id_evento"] = evento.id_evento
                resultado["hora_evento"] = (
                    evento.fecha_hora.strftime(
                        "%H:%M:%S"
                    )
                )

                alertas_generadas.append(resultado)

    return {
        "estado": "OK",
        "alertas_generadas": len(alertas_generadas),
        "data": alertas_generadas
    }


# ============================================================
# REGLA 4
# MULTIPLES EVENTOS DESDE UNA MISMA IP
# ============================================================

def detectar_misma_ip():

    reglas = ReglaDeteccion.query.filter_by(
        tipo_condicion="MISMA_IP",
        estado=True
    ).all()

    alertas_generadas = []

    for regla in reglas:

        eventos = (
            EventoSeguridad.query
            .filter(
                EventoSeguridad.direccion_ip.isnot(None)
            )
            .order_by(
                EventoSeguridad.fecha_hora.asc()
            )
            .all()
        )

        eventos_por_ip = {}

        for evento in eventos:

            eventos_por_ip.setdefault(
                evento.direccion_ip,
                []
            ).append(evento)

        for direccion_ip, lista_eventos in eventos_por_ip.items():

            for indice, evento_inicio in enumerate(lista_eventos):

                limite = (
                    evento_inicio.fecha_hora
                    + timedelta(
                        minutes=regla.intervalo_minutos
                    )
                )

                eventos_ventana = [
                    evento
                    for evento in lista_eventos[indice:]
                    if evento.fecha_hora <= limite
                ]

                if len(eventos_ventana) < regla.umbral:
                    continue

                eventos_detectados = (
                    eventos_ventana[:regla.umbral]
                )

                descripcion = (
                    f"Se detectaron "
                    f"{len(eventos_detectados)} eventos "
                    f"provenientes desde la dirección IP "
                    f"{direccion_ip} dentro de un intervalo "
                    f"de {regla.intervalo_minutos} minutos."
                )

                resultado = _crear_alerta(
                    regla,
                    eventos_detectados,
                    descripcion
                )

                if resultado:

                    resultado["direccion_ip"] = direccion_ip
                    resultado["cantidad_eventos"] = len(
                        eventos_detectados
                    )

                    alertas_generadas.append(resultado)

                    break

    return {
        "estado": "OK",
        "alertas_generadas": len(alertas_generadas),
        "data": alertas_generadas
    }


# ============================================================
# EJECUCION GENERAL DEL MOTOR
# ============================================================

def ejecutar_motor_deteccion():

    resultados = {
        "autenticaciones_fallidas":
            detectar_autenticaciones_fallidas(),

        "eventos_criticos":
            detectar_eventos_criticos(),

        "fuera_horario":
            detectar_fuera_horario(),

        "misma_ip":
            detectar_misma_ip()
    }

    db.session.commit()

    total_alertas = sum(
        resultado["alertas_generadas"]
        for resultado in resultados.values()
    )

    return {
        "estado": "OK",
        "motor": "VIGIA",
        "reglas_evaluadas": 4,
        "total_alertas_generadas": total_alertas,
        "resultados": resultados
    }