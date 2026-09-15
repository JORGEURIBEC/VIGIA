from app import db


class Incidente(db.Model):
    __tablename__ = "incidentes"

    id_incidente = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_alerta = db.Column(
        db.BigInteger,
        db.ForeignKey("alertas.id_alerta"),
        nullable=False,
        unique=True
    )

    id_responsable = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id_usuario"),
        nullable=True
    )

    titulo = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    clasificacion = db.Column(
        db.String(100),
        nullable=True
    )

    prioridad = db.Column(
        db.String(20),
        nullable=False
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="ABIERTO"
    )

    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    fecha_actualizacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    fecha_cierre = db.Column(
        db.DateTime,
        nullable=True
    )

    def to_dict(self):
        return {
            "id_incidente": self.id_incidente,
            "id_alerta": self.id_alerta,
            "id_responsable": self.id_responsable,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "clasificacion": self.clasificacion,
            "prioridad": self.prioridad,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "fecha_creacion": (
                self.fecha_creacion.isoformat()
                if self.fecha_creacion
                else None
            ),
            "fecha_actualizacion": (
                self.fecha_actualizacion.isoformat()
                if self.fecha_actualizacion
                else None
            ),
            "fecha_cierre": (
                self.fecha_cierre.isoformat()
                if self.fecha_cierre
                else None
            ),
        }
    