from app import db


class EventoSeguridad(db.Model):
    __tablename__ = "eventos_seguridad"

    # ==========================================================
    # CAMPOS
    # ==========================================================

    id_evento = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_fuente = db.Column(
        db.Integer,
        db.ForeignKey("fuentes_eventos.id_fuente"),
        nullable=False,
        index=True
    )

    id_tipo_evento = db.Column(
        db.Integer,
        db.ForeignKey("tipos_eventos.id_tipo_evento"),
        nullable=False,
        index=True
    )

    fecha_hora = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )

    usuario_origen = db.Column(
        db.String(100),
        nullable=True
    )

    direccion_ip = db.Column(
        db.String(45),
        nullable=True,
        index=True
    )

    severidad = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )

    resultado = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    fecha_registro = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    # ==========================================================
    # RELACIONES
    # ==========================================================

    fuente = db.relationship(
        "FuenteEvento",
        foreign_keys=[id_fuente]
    )

    tipo_evento = db.relationship(
        "TipoEvento",
        foreign_keys=[id_tipo_evento]
    )

    # ==========================================================
    # CONVERTIR A DICCIONARIO
    # ==========================================================

    def to_dict(self):
        return {
            "id_evento": self.id_evento,
            "id_fuente": self.id_fuente,
            "fuente": (
                self.fuente.nombre
                if self.fuente
                else None
            ),
            "id_tipo_evento": self.id_tipo_evento,
            "tipo_evento": (
                self.tipo_evento.nombre_tipo
                if self.tipo_evento
                else None
            ),
            "fecha_hora": (
                self.fecha_hora.isoformat()
                if self.fecha_hora
                else None
            ),
            "usuario_origen": self.usuario_origen,
            "direccion_ip": self.direccion_ip,
            "severidad": self.severidad,
            "resultado": self.resultado,
            "descripcion": self.descripcion,
            "fecha_registro": (
                self.fecha_registro.isoformat()
                if self.fecha_registro
                else None
            )
        }

    def __repr__(self):
        return (
            f"<EventoSeguridad "
            f"id={self.id_evento}, "
            f"fuente={self.id_fuente}, "
            f"tipo={self.id_tipo_evento}, "
            f"severidad={self.severidad}>"
        )