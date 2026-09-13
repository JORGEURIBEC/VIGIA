from app import db


class TipoEvento(db.Model):
    """
    Modelo correspondiente a la tabla tipos_eventos.

    Representa las categorías utilizadas para clasificar
    los eventos de seguridad registrados en VIGIA.
    """

    __tablename__ = "tipos_eventos"

    id_tipo_evento = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre_tipo = db.Column(
        db.String(100),
        nullable=False,
        unique=True
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

    def to_dict(self):
        """
        Convierte el objeto TipoEvento en un diccionario
        para poder devolverlo posteriormente como JSON.
        """

        return {
            "id_tipo_evento": self.id_tipo_evento,
            "nombre_tipo": self.nombre_tipo,
            "descripcion": self.descripcion,
            "estado": bool(self.estado)
        }

    def __repr__(self):
        return (
            f"<TipoEvento "
            f"id={self.id_tipo_evento}, "
            f"nombre_tipo='{self.nombre_tipo}'>"
        )