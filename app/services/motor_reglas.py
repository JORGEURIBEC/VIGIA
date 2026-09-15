from collections import defaultdict, deque
from datetime import timedelta
import unicodedata

from app import db
from app.models import (
    EventoSeguridad,
    ReglaDeteccion,
    Alerta,
    AlertaEvento,
)


class MotorReglas:
    """
    Motor de detección de VIGIA.

    Analiza los eventos almacenados utilizando las reglas
    activas configuradas en la base de datos y genera alertas
    evitando duplicar alertas previamente creadas.
    """

    HORA_INICIO_HABITUAL = 8
    HORA_FIN_HABITUAL = 20

    def __init__(self):
        self.alertas_generadas = 0

    # ==========================================================
    # UTILIDADES
    # ==========================================================

    @staticmethod
    def _normalizar(texto):
        if not texto:
            return ""

        texto = str(texto).lower().strip()

        texto = unicodedata.normalize("NFD", texto)

        return "".join(
            caracter
            for caracter in texto
            if unicodedata.category(caracter) != "Mn"
        )

    @staticmethod
    def _valor_regla(regla):
        """
        Combina nombre y tipo_condicion para no depender
        de un único texto exacto almacenado en la BD.
        """

        return MotorReglas._normalizar(
            f"{regla.nombre or ''} "
            f"{regla.tipo_condicion or ''}"
        )

    @staticmethod
    def _regla_es(regla, palabras):
        texto = MotorReglas._valor_regla(regla)

        return all(
            MotorReglas._normalizar(palabra) in texto
            for palabra in palabras
        )

    # ==========================================================
    # CONTROL DE DUPLICADOS
    # ==========================================================

    @staticmethod
    def _evento_ya_alertado(id_regla, id_evento):
        """
        Comprueba si un evento ya está asociado a una alerta
        generada por la misma regla.
        """

        resultado = (
            db.session.query(AlertaEvento)
            .join(
                Alerta,
                Alerta.id_alerta == AlertaEvento.id_alerta
            )
            .filter(
                Alerta.id_regla == id_regla,
                AlertaEvento.id_evento == id_evento
            )
            .first()
        )

        return resultado is not None

    # ==========================================================
    # CREACIÓN DE ALERTA
    # ==========================================================

    def _crear_alerta(
        self,
        regla,
        eventos,
        descripcion,
        severidad=None
    ):
        """
        Crea una alerta y relaciona los eventos que la originaron.
        """

        if not eventos:
            return None

        eventos_nuevos = [
            evento
            for evento in eventos
            if not self._evento_ya_alertado(
                regla.id_regla,
                evento.id_evento
            )
        ]

        if not eventos_nuevos:
            return None

        alerta = Alerta(
            id_regla=regla.id_regla,
            severidad=(
                severidad
                or regla.severidad_alerta
                or "MEDIA"
            ),
            descripcion=descripcion,
            estado="PENDIENTE"
        )

        db.session.add(alerta)

        # Necesario para obtener id_alerta
        db.session.flush()

        for evento in eventos_nuevos:
            relacion = AlertaEvento(
                id_alerta=alerta.id_alerta,
                id_evento=evento.id_evento
            )

            db.session.add(relacion)

        self.alertas_generadas += 1

        return alerta

    # ==========================================================
    # REGLA 1
    # AUTENTICACIONES FALLIDAS REITERADAS
    # ==========================================================

    def _autenticaciones_fallidas(self, regla, eventos):
        umbral = regla.umbral or 3
        intervalo = regla.intervalo_minutos or 10

        candidatos = []

        for evento in eventos:

            texto = self._normalizar(
                f"{getattr(evento.tipo_evento, 'nombre_tipo', '')} "
                f"{evento.resultado or ''} "
                f"{evento.descripcion or ''}"
            )

            if (
                "autentic" in texto
                and (
                    "fallid" in texto
                    or "error" in texto
                    or "rechaz" in texto
                )
            ):
                candidatos.append(evento)

        por_ip = defaultdict(list)

        for evento in candidatos:
            if evento.direccion_ip:
                por_ip[evento.direccion_ip].append(evento)

        for ip, lista in por_ip.items():

            lista.sort(key=lambda e: e.fecha_hora)

            ventana = deque()

            for evento in lista:

                ventana.append(evento)

                limite = (
                    evento.fecha_hora
                    - timedelta(minutes=intervalo)
                )

                while (
                    ventana
                    and ventana[0].fecha_hora < limite
                ):
                    ventana.popleft()

                if len(ventana) >= umbral:

                    eventos_alerta = list(ventana)

                    self._crear_alerta(
                        regla,
                        eventos_alerta,
                        (
                            f"Se detectaron {len(eventos_alerta)} "
                            f"intentos de autenticación fallida "
                            f"desde la dirección IP {ip} "
                            f"dentro de un período de "
                            f"{intervalo} minutos."
                        )
                    )

                    ventana.clear()

    # ==========================================================
    # REGLA 2
    # CONCENTRACIÓN DE EVENTOS DESDE UNA MISMA IP
    # ==========================================================

    def _concentracion_ip(self, regla, eventos):
        umbral = regla.umbral or 10
        intervalo = regla.intervalo_minutos or 10

        por_ip = defaultdict(list)

        for evento in eventos:
            if evento.direccion_ip:
                por_ip[evento.direccion_ip].append(evento)

        for ip, lista in por_ip.items():

            lista.sort(key=lambda e: e.fecha_hora)

            ventana = deque()

            for evento in lista:

                ventana.append(evento)

                limite = (
                    evento.fecha_hora
                    - timedelta(minutes=intervalo)
                )

                while (
                    ventana
                    and ventana[0].fecha_hora < limite
                ):
                    ventana.popleft()

                if len(ventana) >= umbral:

                    eventos_alerta = list(ventana)

                    self._crear_alerta(
                        regla,
                        eventos_alerta,
                        (
                            f"Se detectó una concentración de "
                            f"{len(eventos_alerta)} eventos "
                            f"provenientes de la dirección IP "
                            f"{ip} dentro de un período de "
                            f"{intervalo} minutos."
                        )
                    )

                    ventana.clear()

    # ==========================================================
    # REGLA 3
    # EVENTOS CRÍTICOS
    # ==========================================================

    def _eventos_criticos(self, regla, eventos):

        for evento in eventos:

            severidad = self._normalizar(
                evento.severidad
            )

            if severidad == "critica":

                self._crear_alerta(
                    regla,
                    [evento],
                    (
                        f"Se detectó un evento de severidad "
                        f"CRÍTICA. Evento #{evento.id_evento}. "
                        f"Origen IP: "
                        f"{evento.direccion_ip or 'No registrada'}."
                    ),
                    severidad="CRITICA"
                )

    # ==========================================================
    # REGLA 4
    # ACTIVIDAD FUERA DE HORARIO
    # ==========================================================

    def _fuera_horario(self, regla, eventos):

        for evento in eventos:

            if not evento.fecha_hora:
                continue

            hora = evento.fecha_hora.hour

            fuera_horario = (
                hora < self.HORA_INICIO_HABITUAL
                or hora >= self.HORA_FIN_HABITUAL
            )

            if fuera_horario:

                self._crear_alerta(
                    regla,
                    [evento],
                    (
                        f"Se detectó actividad fuera del "
                        f"horario habitual. "
                        f"Evento #{evento.id_evento} registrado "
                        f"a las "
                        f"{evento.fecha_hora.strftime('%H:%M:%S')}."
                    )
                )

    # ==========================================================
    # PROCESAMIENTO PRINCIPAL
    # ==========================================================

    def procesar(self):

        print("=" * 60)
        print("VIGIA - MOTOR DE REGLAS DE DETECCION")
        print("=" * 60)

        reglas = (
            ReglaDeteccion.query
            .filter_by(estado=True)
            .order_by(ReglaDeteccion.id_regla)
            .all()
        )

        eventos = (
            EventoSeguridad.query
            .order_by(EventoSeguridad.fecha_hora)
            .all()
        )

        print(f"Eventos disponibles: {len(eventos):,}")
        print(f"Reglas activas: {len(reglas)}")
        print()

        for regla in reglas:

            texto = self._valor_regla(regla)

            print(
                f"Procesando regla "
                f"{regla.id_regla}: {regla.nombre}"
            )

            if (
                "autentic" in texto
                and "fallid" in texto
            ):
                self._autenticaciones_fallidas(
                    regla,
                    eventos
                )

            elif (
                "ip" in texto
                and (
                    "concentr" in texto
                    or "misma" in texto
                )
            ):
                self._concentracion_ip(
                    regla,
                    eventos
                )

            elif "critic" in texto:
                self._eventos_criticos(
                    regla,
                    eventos
                )

            elif (
                "horario" in texto
                or "hora" in texto
            ):
                self._fuera_horario(
                    regla,
                    eventos
                )

            else:
                print(
                    "  AVISO: tipo de regla no reconocido."
                )

        db.session.commit()

        print()
        print("=" * 60)
        print("RESULTADO DEL MOTOR DE REGLAS")
        print("=" * 60)
        print(
            f"Alertas nuevas generadas: "
            f"{self.alertas_generadas:,}"
        )
        print("ESTADO: PROCESAMIENTO FINALIZADO")
        print("=" * 60)

        return self.alertas_generadas
    