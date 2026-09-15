from flask import Blueprint, render_template, redirect, url_for


# ============================================================
# BLUEPRINT WEB
# ============================================================

web_bp = Blueprint(
    "web",
    __name__
)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@web_bp.route("/")
def inicio():
    """
    Página principal de VIGIA.

    Redirige a la pantalla de inicio de sesión.

    La autenticación de la interfaz web utiliza
    el token JWT almacenado por el navegador.
    """

    return redirect(
        url_for("web.login")
    )


# ============================================================
# LOGIN
# ============================================================

@web_bp.route("/login")
def login():
    """
    Pantalla de autenticación de VIGIA.
    """

    return render_template(
        "login.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@web_bp.route("/dashboard")
def dashboard():
    """
    Renderiza el Dashboard principal de VIGIA.

    Los indicadores se obtienen desde:

    GET /api/v1/dashboard/resumen
    """

    return render_template(
        "dashboard.html",
        titulo="Dashboard"
    )


# ============================================================
# EVENTOS DE SEGURIDAD
# ============================================================

@web_bp.route("/eventos")
def eventos():
    """
    Interfaz web para consultar, registrar,
    filtrar e importar eventos de seguridad.

    API principal:

    GET  /api/v1/eventos
    GET  /api/v1/eventos/<id_evento>
    POST /api/v1/eventos
    PUT  /api/v1/eventos/<id_evento>

    Importación:

    POST /api/v1/eventos/importar
    """

    return render_template(
        "eventos.html",
        titulo="Eventos"
    )


# ============================================================
# ALERTAS
# ============================================================

@web_bp.route("/alertas")
def alertas():
    """
    Interfaz web para consultar, revisar,
    clasificar y gestionar las alertas
    de seguridad generadas por VIGIA.

    API principal:

    GET /api/v1/alertas
    GET /api/v1/alertas/<id_alerta>
    PUT /api/v1/alertas/<id_alerta>/estado
    """

    return render_template(
        "alertas.html",
        titulo="Alertas"
    )


# ============================================================
# INCIDENTES
# ============================================================

@web_bp.route("/incidentes")
def incidentes():
    """
    Interfaz de gestión y seguimiento
    del ciclo de vida de los incidentes
    de seguridad de VIGIA.
    """

    return render_template(
        "incidentes.html",
        titulo="Incidentes"
    )


# ============================================================
# FUENTES DE EVENTOS
# ============================================================

@web_bp.route("/fuentes")
def fuentes():
    """
    Interfaz web para administrar y consultar
    las fuentes de eventos de seguridad de VIGIA.

    El Administrador puede crear, modificar,
    activar y desactivar fuentes.

    El Analista dispone de acceso de consulta.
    """

    return render_template(
        "fuentes.html",
        titulo="Fuentes"
    )


# ============================================================
# TIPOS DE EVENTOS
# ============================================================

@web_bp.route("/tipos-eventos")
def tipos_eventos():
    """
    Administración de las categorías o
    tipos de eventos utilizados por VIGIA.
    """

    return render_template(
        "pagina_base.html",
        titulo="Tipos de eventos",
        encabezado="Tipos de Eventos",
        descripcion=(
            "Administración de las categorías utilizadas "
            "para clasificar los eventos de seguridad."
        )
    )


# ============================================================
# REGLAS DE DETECCIÓN
# ============================================================

@web_bp.route("/reglas")
def reglas():
    """
    Administración de las reglas
    de detección utilizadas por VIGIA.
    """

    return render_template(
        "pagina_base.html",
        titulo="Reglas",
        encabezado="Reglas de Detección",
        descripcion=(
            "Configuración de las reglas utilizadas para "
            "analizar eventos y generar alertas."
        )
    )


# ============================================================
# USUARIOS
# ============================================================

@web_bp.route("/usuarios")
def usuarios():
    """
    Administración de usuarios,
    perfiles y estados de acceso.
    """

    return render_template(
        "pagina_base.html",
        titulo="Usuarios",
        encabezado="Gestión de Usuarios",
        descripcion=(
            "Administración de usuarios, perfiles "
            "y estados de acceso al sistema."
        )
    )


# ============================================================
# AUDITORÍA
# ============================================================

@web_bp.route("/auditoria")
def auditoria():
    """
    Consulta de los registros de auditoría
    generados por las operaciones relevantes.
    """

    return render_template(
        "pagina_base.html",
        titulo="Auditoría",
        encabezado="Registro de Auditoría",
        descripcion=(
            "Consulta de las acciones relevantes realizadas "
            "por los usuarios dentro de VIGIA."
        )
    )