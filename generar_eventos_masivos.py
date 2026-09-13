import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# VIGIA
# GENERADOR DE EVENTOS MASIVOS
# ============================================================
#
# Genera un archivo CSV con 10.000 eventos simulados
# compatibles con la estructura utilizada por VIGIA.
#
# Archivo generado:
# eventos_masivos_vigia.csv
#
# ============================================================


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

CANTIDAD_EVENTOS = 10000

ARCHIVO_SALIDA = Path("eventos_masivos_vigia.csv")


# ============================================================
# 2. IDENTIFICADORES EXISTENTES EN MYSQL
# ============================================================
#
# Comprobado en la base de datos vigia:
#
# fuentes_eventos:
#   id_fuente = 1
#
# tipos_eventos:
#   1 = Autenticación
#   2 = Actividad de red
#   3 = Acceso al sistema
#   4 = Evento crítico
#
# ============================================================

ID_FUENTES = [1]

ID_TIPOS_EVENTOS = [1, 2, 3, 4]


# ============================================================
# 3. USUARIOS SIMULADOS
# ============================================================

USUARIOS = [
    "admin",
    "analista01",
    "usuario01",
    "usuario02",
    "usuario03",
    "servicio_web",
    "sistema",
    "desconocido",
]


# ============================================================
# 4. RESULTADOS POSIBLES
# ============================================================

RESULTADOS = [
    "EXITOSO",
    "FALLIDO",
    "BLOQUEADO",
]


# ============================================================
# 5. DESCRIPCIONES SEGÚN TIPO DE EVENTO
# ============================================================

DESCRIPCIONES_POR_TIPO = {

    # --------------------------------------------------------
    # TIPO 1: AUTENTICACIÓN
    # --------------------------------------------------------
    1: [
        "Inicio de sesión exitoso.",
        "Intento de autenticación fallida.",
        "Múltiples intentos de autenticación registrados.",
        "Intento de acceso con credenciales incorrectas.",
        "Usuario autenticado correctamente.",
        "Intento reiterado de inicio de sesión.",
        "Autenticación bloqueada por política de seguridad.",
    ],

    # --------------------------------------------------------
    # TIPO 2: ACTIVIDAD DE RED
    # --------------------------------------------------------
    2: [
        "Actividad detectada desde una dirección IP no habitual.",
        "Conexión de red registrada por el sistema.",
        "Tráfico de red detectado desde un origen interno.",
        "Comunicación detectada entre dispositivos monitoreados.",
        "Actividad inusual registrada desde una dirección IP.",
        "Conexión rechazada por política de seguridad.",
        "Actividad de red registrada para análisis.",
    ],

    # --------------------------------------------------------
    # TIPO 3: ACCESO AL SISTEMA
    # --------------------------------------------------------
    3: [
        "Acceso realizado fuera del horario habitual.",
        "Intento de acceso a recurso restringido.",
        "Acceso autorizado a recurso del sistema.",
        "Actividad administrativa registrada.",
        "Acceso bloqueado por política de seguridad.",
        "Usuario accede a recurso protegido.",
        "Actividad detectada en horario no habitual.",
    ],

    # --------------------------------------------------------
    # TIPO 4: EVENTO CRÍTICO
    # --------------------------------------------------------
    4: [
        "Evento crítico detectado en sistema monitoreado.",
        "Intento de acceso no autorizado detectado.",
        "Actividad potencialmente comprometida.",
        "Amenaza crítica detectada por el sistema.",
        "Actividad de alta gravedad registrada.",
        "Evento de seguridad que requiere atención prioritaria.",
        "Comportamiento crítico detectado durante el monitoreo.",
    ],
}


# ============================================================
# 6. GENERAR DIRECCIÓN IP
# ============================================================

def generar_ip():
    """
    Genera una dirección IPv4 simulada dentro
    de rangos privados.
    """

    rangos = [
        "192.168",
        "10.0",
        "172.16",
    ]

    rango = random.choice(rangos)

    return (
        f"{rango}."
        f"{random.randint(1, 254)}."
        f"{random.randint(1, 254)}"
    )


# ============================================================
# 7. GENERAR FECHA Y HORA
# ============================================================

def generar_fecha():
    """
    Genera una fecha aleatoria correspondiente
    aproximadamente a los últimos 30 días.

    Se generan horas entre 00:00 y 23:59,
    permitiendo disponer de eventos normales
    y eventos fuera del horario habitual.
    """

    fecha_actual = datetime.now()

    dias_atras = random.randint(0, 29)

    fecha_base = (
        fecha_actual
        - timedelta(days=dias_atras)
    )

    hora = random.randint(0, 23)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)

    fecha = fecha_base.replace(
        hour=hora,
        minute=minuto,
        second=segundo,
        microsecond=0,
    )

    return fecha.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# 8. GENERAR SEVERIDAD
# ============================================================

def generar_severidad(id_tipo_evento):
    """
    Genera una severidad coherente
    con el tipo de evento.
    """

    if id_tipo_evento == 1:

        # Autenticación
        return random.choices(
            ["BAJA", "MEDIA", "ALTA", "CRITICA"],
            weights=[25, 50, 20, 5],
            k=1,
        )[0]

    if id_tipo_evento == 2:

        # Actividad de red
        return random.choices(
            ["BAJA", "MEDIA", "ALTA", "CRITICA"],
            weights=[30, 45, 20, 5],
            k=1,
        )[0]

    if id_tipo_evento == 3:

        # Acceso al sistema
        return random.choices(
            ["BAJA", "MEDIA", "ALTA", "CRITICA"],
            weights=[20, 45, 27, 8],
            k=1,
        )[0]

    if id_tipo_evento == 4:

        # Evento crítico
        return random.choices(
            ["MEDIA", "ALTA", "CRITICA"],
            weights=[10, 35, 55],
            k=1,
        )[0]

    return "MEDIA"


# ============================================================
# 9. GENERAR RESULTADO
# ============================================================

def generar_resultado(id_tipo_evento):
    """
    Genera un resultado probable según
    la naturaleza del evento.
    """

    if id_tipo_evento == 1:

        return random.choices(
            RESULTADOS,
            weights=[45, 40, 15],
            k=1,
        )[0]

    if id_tipo_evento == 2:

        return random.choices(
            RESULTADOS,
            weights=[60, 20, 20],
            k=1,
        )[0]

    if id_tipo_evento == 3:

        return random.choices(
            RESULTADOS,
            weights=[50, 25, 25],
            k=1,
        )[0]

    if id_tipo_evento == 4:

        return random.choices(
            RESULTADOS,
            weights=[10, 40, 50],
            k=1,
        )[0]

    return "FALLIDO"


# ============================================================
# 10. GENERAR DESCRIPCIÓN
# ============================================================

def generar_descripcion(
    id_tipo_evento,
    numero,
):
    """
    Genera una descripción coherente
    con el tipo de evento.
    """

    opciones = DESCRIPCIONES_POR_TIPO.get(
        id_tipo_evento,
        ["Evento de seguridad registrado."],
    )

    descripcion = random.choice(
        opciones
    )

    return (
        f"{descripcion} "
        f"Registro masivo VIGIA #{numero}."
    )


# ============================================================
# 11. GENERAR EVENTO
# ============================================================

def generar_evento(numero):
    """
    Genera un evento completo compatible
    con la estructura del CSV de VIGIA.
    """

    id_fuente = random.choice(
        ID_FUENTES
    )

    id_tipo_evento = random.choice(
        ID_TIPOS_EVENTOS
    )

    fecha_hora = generar_fecha()

    usuario_origen = random.choice(
        USUARIOS
    )

    direccion_ip = generar_ip()

    severidad = generar_severidad(
        id_tipo_evento
    )

    resultado = generar_resultado(
        id_tipo_evento
    )

    descripcion = generar_descripcion(
        id_tipo_evento,
        numero,
    )

    return {
        "id_fuente": id_fuente,
        "id_tipo_evento": id_tipo_evento,
        "fecha_hora": fecha_hora,
        "usuario_origen": usuario_origen,
        "direccion_ip": direccion_ip,
        "severidad": severidad,
        "resultado": resultado,
        "descripcion": descripcion,
    }


# ============================================================
# 12. CREAR ARCHIVO CSV
# ============================================================

def crear_csv():
    """
    Genera el archivo CSV completo.
    """

    columnas = [
        "id_fuente",
        "id_tipo_evento",
        "fecha_hora",
        "usuario_origen",
        "direccion_ip",
        "severidad",
        "resultado",
        "descripcion",
    ]

    with ARCHIVO_SALIDA.open(
        mode="w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
        )

        escritor.writeheader()

        for numero in range(
            1,
            CANTIDAD_EVENTOS + 1,
        ):

            evento = generar_evento(
                numero
            )

            escritor.writerow(
                evento
            )


# ============================================================
# 13. CONTAR REGISTROS GENERADOS
# ============================================================

def contar_registros_csv():
    """
    Comprueba cuántos registros contiene
    realmente el archivo generado.
    """

    with ARCHIVO_SALIDA.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as archivo:

        lector = csv.DictReader(
            archivo
        )

        return sum(
            1
            for _ in lector
        )


# ============================================================
# 14. MOSTRAR RESUMEN
# ============================================================

def mostrar_resumen(
    total_generado,
):
    """
    Muestra información de la ejecución.
    """

    print()
    print(
        "=========================================="
    )

    print(
        "RESULTADO DE LA GENERACIÓN"
    )

    print(
        "=========================================="
    )

    print(
        f"Archivo: {ARCHIVO_SALIDA.resolve()}"
    )

    print(
        f"Cantidad solicitada: "
        f"{CANTIDAD_EVENTOS:,}"
    )

    print(
        f"Cantidad generada: "
        f"{total_generado:,}"
    )

    print(
        "Fuente utilizada: id_fuente = 1"
    )

    print(
        "Tipos utilizados: 1, 2, 3 y 4"
    )

    if total_generado == CANTIDAD_EVENTOS:

        print()
        print(
            "ESTADO: CORRECTO"
        )

        print(
            "El archivo contiene exactamente "
            "10.000 eventos."
        )

    else:

        print()
        print(
            "ESTADO: ADVERTENCIA"
        )

        print(
            "La cantidad generada no coincide "
            "con la cantidad esperada."
        )

    print(
        "=========================================="
    )


# ============================================================
# 15. EJECUCIÓN PRINCIPAL
# ============================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        "VIGIA - GENERADOR DE EVENTOS MASIVOS"
    )

    print(
        "=========================================="
    )

    print()

    print(
        f"Generando "
        f"{CANTIDAD_EVENTOS:,} eventos..."
    )

    crear_csv()

    total_generado = (
        contar_registros_csv()
    )

    mostrar_resumen(
        total_generado
    )