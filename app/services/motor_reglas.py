from collections import defaultdict, deque
from datetime import timedelta
from time import perf_counter
import unicodedata

from sqlalchemy.orm import joinedload

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

    La detección de duplicados utiliza una caché en memoria
    para evitar ejecutar miles de consultas SQL individuales.
    """

    HORA_INICIO_HABITUAL = 8
    HORA_FIN_HABITUAL = 20

    def __init__(self):
        self.alertas_generadas = 0

        # Conjunto de pares (id_regla, id_evento).
        # Se carga una sola vez antes del procesamiento.
        self.eventos_ya_alertados = set()

    # ==========================================================
    # UTILIDADES
    # ==========================================================

    @staticmethod
    def _normalizar(texto):
        """
        Convierte un texto a minúsculas y elimina tildes
        para facilitar las comparaciones.
        """

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
        """
        Comprueba si una regla contiene determinadas palabras.
        """

        texto = MotorReglas._valor_regla(regla)

        return all(
            MotorReglas._normalizar(palabra) in texto
            for palabra in palabras
        )

    # ==========================================================
    # CARGA Y CONTROL DE DUPLICADOS
    # ==========================================================

    def _cargar_eventos_ya_alertados(self):
        """
        Obtiene en una sola consulta todas las relaciones
        regla-evento que ya han generado una alerta.

        Así se evita consultar MySQL individualmente por cada
        evento procesado.
        """

        inicio = perf_counter()

        print("Cargando relaciones de alertas existentes...")

        relaciones = (
            db.session.query(
                Alerta.id_regla,
                AlertaEvento.id_evento,
            )
            .join(
                AlertaEvento,
                Alerta.id_alerta == AlertaEvento.id_alerta,
            )
            .all()
        )

        self.eventos_ya_alertados = {
            (id_regla, id_evento)
            for id_regla, id_evento in relaciones
        }

        tiempo = perf_counter() - inicio

        print(
            "Relaciones regla-evento cargadas: "
            f"{len(self.eventos_ya_alertados):,}"
        )
        print(
            "Tiempo carga de relaciones: "
            f"{tiempo:.4f} segundos"
        )

    def _evento_ya_alertado(self, id_regla, id_evento):
        """
        Comprueba en memoria si un evento ya fue procesado
        por una determinada regla.
        """

        return (
            id_regla,
            id_evento,
        ) in self.eventos_ya_alertados

    # ==========================================================
    # CREACIÓN DE ALERTA
    # ==========================================================

    def _crear_alerta(
        self,
        regla,
        eventos,
        descripcion,
        severidad=None,
    ):
        """
        Crea una alerta y relaciona los eventos que la originaron.

        Solo considera eventos que todavía no hayan generado
        una alerta para la misma regla.
        """

        if not eventos:
            return None

        eventos_nuevos = [
            evento
            for evento in eventos
            if not self._evento_ya_alertado(
                regla.id_regla,
                evento.id_evento,
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
            estado="PENDIENTE",
        )

        db.session.add(alerta)

        # Necesario para obtener id_alerta antes de crear
        # las relaciones alerta-evento.
        db.session.flush()

        for evento in eventos_nuevos:
            relacion = AlertaEvento(
                id_alerta=alerta.id_alerta,
                id_evento=evento.id_evento,
            )

            db.session.add(relacion)

            # Actualiza inmediatamente la caché para impedir
            # duplicados dentro de esta misma ejecución.
            self.eventos_ya_alertados.add(
                (
                    regla.id_regla,
                    evento.id_evento,
                )
            )

        self.alertas_generadas += 1

        return alerta

    # ==========================================================
    # REGLA 1
    # AUTENTICACIONES FALLIDAS REITERADAS
    # ==========================================================

    def _autenticaciones_fallidas(self, regla, eventos):
        """
        Detecta varios intentos de autenticación fallida
        provenientes de una misma dirección IP dentro
        de un intervalo determinado.
        """

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
                        ),
                    )

                    ventana.clear()

    # ==========================================================
    # REGLA 2
    # CONCENTRACIÓN DE EVENTOS DESDE UNA MISMA IP
    # ==========================================================

    def _concentracion_ip(self, regla, eventos):
        """
        Detecta concentraciones de eventos provenientes
        desde una misma dirección IP.
        """

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
                        ),
                    )

                    ventana.clear()

    # ==========================================================
    # REGLA 3
    # EVENTOS CRÍTICOS
    # ==========================================================

    def _eventos_criticos(self, regla, eventos):
        """
        Genera una alerta individual cuando se detecta
        un evento clasificado con severidad crítica.
        """

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
                    severidad="CRITICA",
                )

    # ==========================================================
    # REGLA 4
    # ACTIVIDAD FUERA DE HORARIO
    # ==========================================================

    def _fuera_horario(self, regla, eventos):
        """
        Detecta eventos registrados fuera del horario
        habitual configurado para VIGIA.
        """

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
                    ),
                )

    # ==========================================================
    # PROCESAMIENTO PRINCIPAL
    # ==========================================================

    def procesar(self):
        """
        Ejecuta todas las reglas activas sobre los eventos
        almacenados en VIGIA.

        La transacción se confirma una sola vez al final para
        evitar que SQLAlchemy expire los objetos cargados entre
        reglas y provoque miles de recargas desde MySQL.
        """

        inicio_total = perf_counter()

        print("=" * 60)
        print("VIGIA - MOTOR DE REGLAS DE DETECCION")
        print("=" * 60)

        # ------------------------------------------------------
        # CARGAR REGLAS ACTIVAS
        # ------------------------------------------------------

        inicio = perf_counter()

        reglas = (
            ReglaDeteccion.query
            .filter_by(estado=True)
            .order_by(ReglaDeteccion.id_regla)
            .all()
        )

        tiempo_reglas = perf_counter() - inicio

        # ------------------------------------------------------
        # CARGAR EVENTOS
        # joinedload evita consultas adicionales al acceder
        # a evento.tipo_evento.
        # ------------------------------------------------------

        inicio = perf_counter()

        eventos = (
            EventoSeguridad.query
            .options(
                joinedload(
                    EventoSeguridad.tipo_evento
                )
            )
            .order_by(EventoSeguridad.fecha_hora)
            .all()
        )

        tiempo_eventos = perf_counter() - inicio

        print(
            f"Eventos disponibles: {len(eventos):,}"
        )
        print(
            f"Reglas activas: {len(reglas)}"
        )
        print(
            "Tiempo carga de reglas: "
            f"{tiempo_reglas:.4f} segundos"
        )
        print(
            "Tiempo carga de eventos: "
            f"{tiempo_eventos:.4f} segundos"
        )
        print()

        # ------------------------------------------------------
        # CARGAR RELACIONES EXISTENTES UNA SOLA VEZ
        # ------------------------------------------------------

        self._cargar_eventos_ya_alertados()

        print()

        # ------------------------------------------------------
        # PROCESAR REGLAS
        # ------------------------------------------------------

        for regla in reglas:
            inicio_regla = perf_counter()

            texto = self._valor_regla(regla)

            print(
                f"Procesando regla "
                f"{regla.id_regla}: "
                f"{regla.nombre}"
            )

            alertas_antes = self.alertas_generadas

            if (
                "autentic" in texto
                and "fallid" in texto
            ):
                self._autenticaciones_fallidas(
                    regla,
                    eventos,
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
                    eventos,
                )

            elif "critic" in texto:
                self._eventos_criticos(
                    regla,
                    eventos,
                )

            elif (
                "horario" in texto
                or "hora" in texto
            ):
                self._fuera_horario(
                    regla,
                    eventos,
                )

            else:
                print(
                    "  AVISO: tipo de regla "
                    "no reconocido."
                )

            # Envía cambios pendientes a la BD sin cerrar
            # la transacción ni expirar los eventos cargados.
            db.session.flush()

            generadas_regla = (
                self.alertas_generadas
                - alertas_antes
            )

            tiempo_regla = (
                perf_counter()
                - inicio_regla
            )

            print(
                f"  Alertas nuevas de esta regla: "
                f"{generadas_regla:,}"
            )
            print(
                f"  Tiempo de la regla: "
                f"{tiempo_regla:.4f} segundos"
            )
            print("  Estado: OK")
            print()

        # ------------------------------------------------------
        # COMMIT ÚNICO FINAL
        # ------------------------------------------------------

        inicio_commit = perf_counter()
        db.session.commit()
        tiempo_commit = perf_counter() - inicio_commit

        tiempo_total = perf_counter() - inicio_total

        # ------------------------------------------------------
        # RESULTADO
        # ------------------------------------------------------

        print("=" * 60)
        print("RESULTADO DEL MOTOR DE REGLAS")
        print("=" * 60)
        print(
            f"Alertas nuevas generadas: "
            f"{self.alertas_generadas:,}"
        )
        print(
            f"Tiempo del commit final: "
            f"{tiempo_commit:.4f} segundos"
        )
        print(
            f"Tiempo total del motor: "
            f"{tiempo_total:.4f} segundos"
        )
        print("ESTADO: PROCESAMIENTO FINALIZADO")
        print("=" * 60)

        return self.alertas_generadas

