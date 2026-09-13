from app import db


class FuenteEvento(db.Model):
    """
    Modelo que representa una fuente generadora de eventos
    de seguridad dentro de la plataforma VIGIA.
    """

    __tablename__ = "fuentes_eventos"

    # ==========================================================
    # COLUMNAS
    # ==========================================================

    id_fuente = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    tipo_fuente = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255),
        nullable=True
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    # ==========================================================
    # CONVERSIÓN A DICCIONARIO
    # ==========================================================

    def to_dict(self):
        """
        Convierte el objeto FuenteEvento a un diccionario
        para poder enviarlo como respuesta JSON mediante la API.
        """

        return {
            "id_fuente": self.id_fuente,
            "nombre": self.nombre,
            "tipo_fuente": self.tipo_fuente,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "fecha_creacion": (
                self.fecha_creacion.strftime("%d-%m-%Y %H:%M:%S")
                if self.fecha_creacion
                else None
            )
        }

    # ==========================================================
    # REPRESENTACIÓN DEL OBJETO
    # ==========================================================

    def __repr__(self):
        return (
            f"<FuenteEvento "
            f"id_fuente={self.id_fuente}, "
            f"nombre='{self.nombre}', "
            f"tipo_fuente='{self.tipo_fuente}'>"
        )