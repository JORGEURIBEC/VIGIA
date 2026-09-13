/*
=========================================================
VIGIA
Plataforma Web de Monitoreo, Análisis y Gestión
de Eventos de Seguridad Informática

Archivo:
app/static/js/app.js
=========================================================
*/


"use strict";


/* =========================================================
   1. CONFIGURACIÓN GENERAL
========================================================= */

const VIGIA = {

    API_BASE: "/api/v1",

    TOKEN_KEY: "vigia_access_token",

    USER_KEY: "vigia_usuario"
};


/* =========================================================
   2. INICIALIZACIÓN
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    inicializarMenuLateral();

    marcarMenuActivo();

    inicializarModales();

    inicializarBotonCerrarSesion();

    inicializarMensajes();

});


/* =========================================================
   3. MENÚ LATERAL RESPONSIVE
========================================================= */

function inicializarMenuLateral() {

    const sidebar = document.getElementById("sidebar");

    const menuToggle = document.getElementById("menuToggle");


    if (!sidebar || !menuToggle) {

        return;
    }


    menuToggle.addEventListener("click", (event) => {

        event.stopPropagation();

        sidebar.classList.toggle("active");

    });


    /*
    ---------------------------------------------------------
    Cerrar sidebar al presionar fuera de él en pantallas
    pequeñas.
    ---------------------------------------------------------
    */

    document.addEventListener("click", (event) => {

        if (window.innerWidth > 900) {

            return;
        }


        const clickDentroSidebar =
            sidebar.contains(event.target);


        const clickEnBoton =
            menuToggle.contains(event.target);


        if (
            !clickDentroSidebar &&
            !clickEnBoton &&
            sidebar.classList.contains("active")
        ) {

            sidebar.classList.remove("active");
        }

    });


    /*
    ---------------------------------------------------------
    Cerrar sidebar después de seleccionar una opción
    en dispositivos móviles.
    ---------------------------------------------------------
    */

    const enlacesMenu =
        sidebar.querySelectorAll(".nav-item");


    enlacesMenu.forEach((enlace) => {

        enlace.addEventListener("click", () => {

            if (window.innerWidth <= 900) {

                sidebar.classList.remove("active");
            }

        });

    });


    /*
    ---------------------------------------------------------
    Corregir estado del sidebar al cambiar tamaño ventana.
    ---------------------------------------------------------
    */

    window.addEventListener("resize", () => {

        if (window.innerWidth > 900) {

            sidebar.classList.remove("active");
        }

    });

}


/* =========================================================
   4. MARCAR AUTOMÁTICAMENTE MENÚ ACTIVO
========================================================= */

function marcarMenuActivo() {

    const rutaActual =
        window.location.pathname.toLowerCase();


    const enlaces =
        document.querySelectorAll(".nav-item[href]");


    enlaces.forEach((enlace) => {

        const href =
            enlace.getAttribute("href");


        if (!href || href === "#") {

            return;
        }


        let rutaEnlace;


        try {

            rutaEnlace =
                new URL(
                    enlace.href,
                    window.location.origin
                ).pathname.toLowerCase();

        }
        catch {

            return;
        }


        enlace.classList.remove("active");


        /*
        -----------------------------------------------------
        Inicio debe coincidir solamente con "/".
        Las demás rutas pueden coincidir por prefijo.
        -----------------------------------------------------
        */

        if (
            rutaEnlace === "/" &&
            rutaActual === "/"
        ) {

            enlace.classList.add("active");

        }
        else if (
            rutaEnlace !== "/" &&
            rutaActual.startsWith(rutaEnlace)
        ) {

            enlace.classList.add("active");
        }

    });

}


/* =========================================================
   5. MODALES
========================================================= */

function inicializarModales() {

    /*
    ---------------------------------------------------------
    Botones que abren modales.

    Ejemplo:

    <button data-modal-open="modalIncidente">
        Abrir
    </button>
    ---------------------------------------------------------
    */

    const botonesAbrir =
        document.querySelectorAll(
            "[data-modal-open]"
        );


    botonesAbrir.forEach((boton) => {

        boton.addEventListener("click", () => {

            const modalId =
                boton.dataset.modalOpen;


            abrirModal(modalId);

        });

    });


    /*
    ---------------------------------------------------------
    Botones para cerrar modales.
    ---------------------------------------------------------
    */

    const botonesCerrar =
        document.querySelectorAll(
            "[data-modal-close]"
        );


    botonesCerrar.forEach((boton) => {

        boton.addEventListener("click", () => {

            const modal =
                boton.closest(
                    ".modal-overlay"
                );


            if (modal) {

                cerrarModal(
                    modal.id
                );
            }

        });

    });


    /*
    ---------------------------------------------------------
    Cerrar pulsando sobre fondo oscuro.
    ---------------------------------------------------------
    */

    const overlays =
        document.querySelectorAll(
            ".modal-overlay"
        );


    overlays.forEach((overlay) => {

        overlay.addEventListener(
            "click",
            (event) => {

                if (
                    event.target === overlay
                ) {

                    cerrarModal(
                        overlay.id
                    );
                }

            }
        );

    });


    /*
    ---------------------------------------------------------
    Cerrar modal con tecla ESC.
    ---------------------------------------------------------
    */

    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key !== "Escape") {

                return;
            }


            const modalActivo =
                document.querySelector(
                    ".modal-overlay.active"
                );


            if (modalActivo) {

                cerrarModal(
                    modalActivo.id
                );
            }

        }
    );

}


/* =========================================================
   6. ABRIR MODAL
========================================================= */

function abrirModal(modalId) {

    if (!modalId) {

        return;
    }


    const modal =
        document.getElementById(
            modalId
        );


    if (!modal) {

        console.warn(
            `VIGIA: No existe el modal "${modalId}".`
        );

        return;
    }


    modal.classList.add(
        "active"
    );


    document.body.style.overflow =
        "hidden";

}


/* =========================================================
   7. CERRAR MODAL
========================================================= */

function cerrarModal(modalId) {

    if (!modalId) {

        return;
    }


    const modal =
        document.getElementById(
            modalId
        );


    if (!modal) {

        return;
    }


    modal.classList.remove(
        "active"
    );


    document.body.style.overflow =
        "";

}


/* =========================================================
   8. MENSAJES GLOBALES
========================================================= */

function inicializarMensajes() {

    const mensaje =
        document.getElementById(
            "globalMessage"
        );


    if (!mensaje) {

        return;
    }


    /*
    ---------------------------------------------------------
    Si el contenedor existe pero está vacío, se oculta.
    ---------------------------------------------------------
    */

    if (
        mensaje.textContent.trim() === ""
    ) {

        mensaje.classList.add(
            "hidden"
        );
    }

}


/* =========================================================
   9. MOSTRAR MENSAJE
========================================================= */

function mostrarMensaje(
    texto,
    tipo = "info",
    duracion = 5000
) {

    const contenedor =
        document.getElementById(
            "globalMessage"
        );


    /*
    ---------------------------------------------------------
    Si una página todavía no tiene el elemento globalMessage,
    usamos consola para evitar un error JavaScript.
    ---------------------------------------------------------
    */

    if (!contenedor) {

        console.log(
            `[VIGIA - ${tipo.toUpperCase()}] ${texto}`
        );

        return;
    }


    const clasesPermitidas = {

        success:
            "message-success",

        error:
            "message-error",

        warning:
            "message-warning",

        info:
            "message-info"
    };


    const clase =
        clasesPermitidas[tipo] ||
        clasesPermitidas.info;


    contenedor.className =
        `global-message ${clase}`;


    contenedor.textContent =
        texto;


    contenedor.classList.remove(
        "hidden"
    );


    /*
    ---------------------------------------------------------
    Si duración es mayor a 0, ocultar automáticamente.
    ---------------------------------------------------------
    */

    if (
        duracion &&
        duracion > 0
    ) {

        window.setTimeout(() => {

            ocultarMensaje();

        }, duracion);

    }

}


/* =========================================================
   10. OCULTAR MENSAJE
========================================================= */

function ocultarMensaje() {

    const contenedor =
        document.getElementById(
            "globalMessage"
        );


    if (!contenedor) {

        return;
    }


    contenedor.classList.add(
        "hidden"
    );

}


/* =========================================================
   11. MANEJO DEL TOKEN JWT
========================================================= */

function guardarToken(token) {

    if (!token) {

        return;
    }


    localStorage.setItem(
        VIGIA.TOKEN_KEY,
        token
    );

}


/* =========================================================
   12. OBTENER TOKEN
========================================================= */

function obtenerToken() {

    return localStorage.getItem(
        VIGIA.TOKEN_KEY
    );

}


/* =========================================================
   13. ELIMINAR TOKEN
========================================================= */

function eliminarToken() {

    localStorage.removeItem(
        VIGIA.TOKEN_KEY
    );

    localStorage.removeItem(
        VIGIA.USER_KEY
    );

}


/* =========================================================
   14. GUARDAR USUARIO
========================================================= */

function guardarUsuario(usuario) {

    if (!usuario) {

        return;
    }


    localStorage.setItem(
        VIGIA.USER_KEY,
        JSON.stringify(usuario)
    );

}


/* =========================================================
   15. OBTENER USUARIO
========================================================= */

function obtenerUsuario() {

    const usuario =
        localStorage.getItem(
            VIGIA.USER_KEY
        );


    if (!usuario) {

        return null;
    }


    try {

        return JSON.parse(
            usuario
        );

    }
    catch {

        localStorage.removeItem(
            VIGIA.USER_KEY
        );

        return null;
    }

}


/* =========================================================
   16. SOLICITUD GENERAL A LA API
========================================================= */

async function apiRequest(
    endpoint,
    opciones = {}
) {

    const token =
        obtenerToken();


    const configuracion = {

        method:
            opciones.method || "GET",

        headers: {

            "Accept":
                "application/json",

            ...opciones.headers
        }

    };


    /*
    ---------------------------------------------------------
    Agregar JWT.
    ---------------------------------------------------------
    */

    if (token) {

        configuracion.headers[
            "Authorization"
        ] = `Bearer ${token}`;

    }


    /*
    ---------------------------------------------------------
    Agregar body JSON cuando corresponda.
    ---------------------------------------------------------
    */

    if (
        opciones.body !== undefined &&
        opciones.body !== null
    ) {

        configuracion.headers[
            "Content-Type"
        ] = "application/json";


        configuracion.body =
            typeof opciones.body === "string"
                ?
                opciones.body
                :
                JSON.stringify(
                    opciones.body
                );

    }


    let respuesta;


    try {

        respuesta =
            await fetch(
                `${VIGIA.API_BASE}${endpoint}`,
                configuracion
            );

    }
    catch (error) {

        console.error(
            "Error de conexión con VIGIA:",
            error
        );


        throw new Error(
            "No fue posible establecer conexión con el servidor."
        );

    }


    /*
    ---------------------------------------------------------
    Intentamos interpretar la respuesta como JSON.
    ---------------------------------------------------------
    */

    let datos = null;


    try {

        datos =
            await respuesta.json();

    }
    catch {

        datos = null;
    }


    /*
    ---------------------------------------------------------
    Token vencido o no autorizado.
    ---------------------------------------------------------
    */

    if (respuesta.status === 401) {

        const mensaje =
            datos?.msg ||
            datos?.mensaje ||
            "";


        const mensajeNormalizado =
            String(mensaje)
                .toLowerCase();


        if (
            mensajeNormalizado.includes(
                "expired"
            ) ||
            mensajeNormalizado.includes(
                "token"
            )
        ) {

            eliminarToken();

        }

    }


    /*
    ---------------------------------------------------------
    Error HTTP.
    ---------------------------------------------------------
    */

    if (!respuesta.ok) {

        const mensaje =
            datos?.mensaje ||
            datos?.msg ||
            datos?.detail ||
            datos?.detalle ||
            `Error HTTP ${respuesta.status}`;


        const error =
            new Error(mensaje);


        error.status =
            respuesta.status;


        error.data =
            datos;


        throw error;

    }


    return datos;

}


/* =========================================================
   17. GET
========================================================= */

async function apiGet(endpoint) {

    return apiRequest(
        endpoint,
        {
            method: "GET"
        }
    );

}


/* =========================================================
   18. POST
========================================================= */

async function apiPost(
    endpoint,
    body
) {

    return apiRequest(
        endpoint,
        {
            method: "POST",
            body: body
        }
    );

}


/* =========================================================
   19. PUT
========================================================= */

async function apiPut(
    endpoint,
    body
) {

    return apiRequest(
        endpoint,
        {
            method: "PUT",
            body: body
        }
    );

}


/* =========================================================
   20. DELETE
========================================================= */

async function apiDelete(endpoint) {

    return apiRequest(
        endpoint,
        {
            method: "DELETE"
        }
    );

}


/* =========================================================
   21. CERRAR SESIÓN
========================================================= */

function inicializarBotonCerrarSesion() {

    const boton =
        document.getElementById(
            "logoutButton"
        );


    if (!boton) {

        return;
    }


    boton.addEventListener(
        "click",
        () => {

            cerrarSesion();

        }
    );

}


/* =========================================================
   22. FUNCIÓN CERRAR SESIÓN
========================================================= */

function cerrarSesion() {

    eliminarToken();


    window.location.href =
        "/login";

}


/* =========================================================
   23. FORMATEAR FECHAS
========================================================= */

function formatearFecha(
    valor
) {

    if (!valor) {

        return "-";
    }


    const fecha =
        new Date(valor);


    if (
        Number.isNaN(
            fecha.getTime()
        )
    ) {

        return valor;
    }


    return new Intl.DateTimeFormat(
        "es-CL",
        {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        }
    ).format(fecha);

}


/* =========================================================
   24. NORMALIZAR TEXTO
========================================================= */

function normalizarTexto(valor) {

    if (
        valor === null ||
        valor === undefined
    ) {

        return "";
    }


    return String(valor)
        .trim()
        .toUpperCase();

}


/* =========================================================
   25. CLASE SEGÚN SEVERIDAD
========================================================= */

function obtenerClaseSeveridad(
    severidad
) {

    const valor =
        normalizarTexto(
            severidad
        );


    const clases = {

        CRITICA:
            "severity-critica",

        "CRÍTICA":
            "severity-critica",

        ALTA:
            "severity-alta",

        MEDIA:
            "severity-media",

        BAJA:
            "severity-baja"

    };


    return clases[valor] ||
        "badge-neutral";

}


/* =========================================================
   26. CREAR BADGE DE SEVERIDAD
========================================================= */

function crearBadgeSeveridad(
    severidad
) {

    const span =
        document.createElement(
            "span"
        );


    span.classList.add(
        "badge",
        obtenerClaseSeveridad(
            severidad
        )
    );


    span.textContent =
        severidad || "SIN DEFINIR";


    return span;

}


/* =========================================================
   27. CLASE SEGÚN ESTADO
========================================================= */

function obtenerClaseEstado(
    estado
) {

    const valor =
        normalizarTexto(
            estado
        );


    const estadosSuccess = [

        "ACTIVO",
        "RESUELTO",
        "CERRADO"

    ];


    const estadosWarning = [

        "PENDIENTE",
        "EN_REVISION",
        "EN REVISIÓN",
        "EN_ANALISIS",
        "EN ANÁLISIS",
        "EN_TRATAMIENTO"

    ];


    const estadosDanger = [

        "CRITICO",
        "CRÍTICO",
        "ERROR"

    ];


    const estadosInfo = [

        "ESCALADA",
        "ABIERTO"

    ];


    if (
        estadosSuccess.includes(
            valor
        )
    ) {

        return "badge-success";
    }


    if (
        estadosWarning.includes(
            valor
        )
    ) {

        return "badge-warning";
    }


    if (
        estadosDanger.includes(
            valor
        )
    ) {

        return "badge-danger";
    }


    if (
        estadosInfo.includes(
            valor
        )
    ) {

        return "badge-info";
    }


    return "badge-neutral";

}


/* =========================================================
   28. CREAR BADGE DE ESTADO
========================================================= */

function crearBadgeEstado(
    estado
) {

    const span =
        document.createElement(
            "span"
        );


    span.classList.add(
        "badge",
        obtenerClaseEstado(
            estado
        )
    );


    span.textContent =
        String(
            estado || "SIN DEFINIR"
        ).replaceAll(
            "_",
            " "
        );


    return span;

}


/* =========================================================
   29. ESCAPAR TEXTO HTML
========================================================= */

function escaparHTML(valor) {

    if (
        valor === null ||
        valor === undefined
    ) {

        return "";
    }


    const elemento =
        document.createElement(
            "div"
        );


    elemento.textContent =
        String(valor);


    return elemento.innerHTML;

}


/* =========================================================
   30. CONFIRMACIÓN GENERAL
========================================================= */

function confirmarAccion(
    mensaje =
        "¿Desea continuar con esta operación?"
) {

    return window.confirm(
        mensaje
    );

}


/* =========================================================
   31. CONVERTIR FORMULARIO A OBJETO
========================================================= */

function formularioAObjeto(
    formulario
) {

    if (!formulario) {

        return {};
    }


    const formData =
        new FormData(
            formulario
        );


    const objeto = {};


    formData.forEach(
        (valor, clave) => {

            objeto[clave] =
                typeof valor === "string"
                    ?
                    valor.trim()
                    :
                    valor;

        }
    );


    return objeto;

}


/* =========================================================
   32. MOSTRAR / OCULTAR ELEMENTO
========================================================= */

function mostrarElemento(
    elemento
) {

    if (!elemento) {

        return;
    }


    elemento.classList.remove(
        "hidden"
    );

}


function ocultarElemento(
    elemento
) {

    if (!elemento) {

        return;
    }


    elemento.classList.add(
        "hidden"
    );

}


/* =========================================================
   33. ESTADO DE BOTÓN DURANTE OPERACIÓN
========================================================= */

function bloquearBoton(
    boton,
    texto = "Procesando..."
) {

    if (!boton) {

        return;
    }


    boton.dataset.textoOriginal =
        boton.textContent;


    boton.disabled = true;

    boton.textContent =
        texto;

}


function desbloquearBoton(
    boton
) {

    if (!boton) {

        return;
    }


    boton.disabled = false;


    if (
        boton.dataset.textoOriginal
    ) {

        boton.textContent =
            boton.dataset.textoOriginal;


        delete boton.dataset
            .textoOriginal;
    }

}


/* =========================================================
   34. FUNCIONES DISPONIBLES GLOBALMENTE
========================================================= */

window.VIGIA = VIGIA;

window.abrirModal =
    abrirModal;

window.cerrarModal =
    cerrarModal;

window.mostrarMensaje =
    mostrarMensaje;

window.ocultarMensaje =
    ocultarMensaje;

window.guardarToken =
    guardarToken;

window.obtenerToken =
    obtenerToken;

window.eliminarToken =
    eliminarToken;

window.guardarUsuario =
    guardarUsuario;

window.obtenerUsuario =
    obtenerUsuario;

window.apiRequest =
    apiRequest;

window.apiGet =
    apiGet;

window.apiPost =
    apiPost;

window.apiPut =
    apiPut;

window.apiDelete =
    apiDelete;

window.formatearFecha =
    formatearFecha;

window.obtenerClaseSeveridad =
    obtenerClaseSeveridad;

window.crearBadgeSeveridad =
    crearBadgeSeveridad;

window.obtenerClaseEstado =
    obtenerClaseEstado;

window.crearBadgeEstado =
    crearBadgeEstado;

window.escaparHTML =
    escaparHTML;

window.confirmarAccion =
    confirmarAccion;

window.formularioAObjeto =
    formularioAObjeto;

window.bloquearBoton =
    bloquearBoton;

window.desbloquearBoton =
    desbloquearBoton;