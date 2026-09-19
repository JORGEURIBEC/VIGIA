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
    Interfaz web para administrar y consultar
    los tipos de eventos utilizados por VIGIA.

    El Administrador puede crear, modificar,
    activar y desactivar tipos de eventos.

    El Analista dispone de acceso de consulta.
    """

    return render_template(
        "tipos_eventos.html",
        titulo="Tipos de eventos"
    )


# ============================================================
# REGLAS DE DETECCIÓN
# ============================================================

@web_bp.route("/reglas")
def reglas():
    """
    Interfaz web para administrar las reglas
    de detección utilizadas por VIGIA.

    Este módulo es de acceso administrativo.
    """

    return render_template(
        "reglas.html",
        titulo="Reglas"
    )


# ============================================================
# USUARIOS
# ============================================================

@web_bp.route("/usuarios")
def usuarios():
    """
    Interfaz web para administrar usuarios,
    perfiles y estados de acceso a VIGIA.

    Este módulo es de acceso administrativo.
    """

    return render_template(
        "usuarios.html",
        titulo="Usuarios"
    )


# ============================================================
# AUDITORÍA
# ============================================================

@web_bp.route("/auditoria")
def auditoria():
    """
    Interfaz web para consultar la trazabilidad
    de las operaciones relevantes realizadas en VIGIA.

    Este módulo es de acceso administrativo.
    """

    return render_template(
        "auditoria.html",
        titulo="Auditoría"
    )