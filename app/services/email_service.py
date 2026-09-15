import smtplib
from email.message import EmailMessage

from flask import current_app


class EmailService:
    """
    Servicio encargado del envío de correos electrónicos
    utilizados por VIGIA.
    """

    @staticmethod
    def enviar_correo(
        destinatario,
        asunto,
        contenido_texto
    ):
        """
        Envía un correo electrónico mediante SMTP.

        Retorna True cuando el mensaje fue enviado
        correctamente.

        En caso de error, la excepción se propaga para que
        sea administrada por la capa correspondiente.
        """

        host = current_app.config.get("MAIL_SERVER")
        puerto = current_app.config.get("MAIL_PORT")
        usuario = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")
        remitente = current_app.config.get("MAIL_DEFAULT_SENDER")
        usar_tls = current_app.config.get("MAIL_USE_TLS", True)

        # ----------------------------------------------------
        # Validar configuración
        # ----------------------------------------------------

        if not host:
            raise RuntimeError(
                "MAIL_SERVER no se encuentra configurado."
            )

        if not puerto:
            raise RuntimeError(
                "MAIL_PORT no se encuentra configurado."
            )

        if not usuario:
            raise RuntimeError(
                "MAIL_USERNAME no se encuentra configurado."
            )

        if not password:
            raise RuntimeError(
                "MAIL_PASSWORD no se encuentra configurado."
            )

        if not remitente:
            remitente = usuario

        # ----------------------------------------------------
        # Crear mensaje
        # ----------------------------------------------------

        mensaje = EmailMessage()

        mensaje["Subject"] = asunto
        mensaje["From"] = remitente
        mensaje["To"] = destinatario

        mensaje.set_content(contenido_texto)

        # ----------------------------------------------------
        # Conexión SMTP
        # ----------------------------------------------------

        with smtplib.SMTP(
            host,
            int(puerto),
            timeout=30
        ) as servidor:

            if usar_tls:
                servidor.starttls()

            servidor.login(
                usuario,
                password
            )

            servidor.send_message(
                mensaje
            )

        return True


    @staticmethod
    def enviar_recuperacion_password(
        destinatario,
        nombre_usuario,
        token,
        minutos_expiracion
    ):
        """
        Envía al usuario las instrucciones para recuperar
        su contraseña de VIGIA.
        """

        asunto = (
            "VIGIA - Recuperación de contraseña"
        )

        contenido = f"""
Hola {nombre_usuario}:

Se recibió una solicitud para restablecer la contraseña de tu cuenta en VIGIA.

Token de recuperación:

{token}

Este token tiene una vigencia de {minutos_expiracion} minutos y puede ser utilizado una sola vez.

Si no realizaste esta solicitud, puedes ignorar este mensaje.

Por razones de seguridad, VIGIA nunca almacena este token en texto plano.

VIGIA
Visualización Integrada y Gestión de Incidentes y Alertas
NovaTech SpA
""".strip()

        return EmailService.enviar_correo(
            destinatario=destinatario,
            asunto=asunto,
            contenido_texto=contenido
        )