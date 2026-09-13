from datetime import datetime
from app import db


class Alerta(db.Model):
    __tablename__ = "alertas"

    id_alerta = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_regla = db.Column(
        db.Integer,
        db.ForeignKey("reglas_deteccion.id_regla"),
        nullable=False
    )

    id_usuario_revisor = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id_usuario"),
        nullable=True
    )

    fecha_generacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    severidad = db.Column(
        db.String(20),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="PENDIENTE"
    )

    fecha_revision = db.Column(
        db.DateTime,
        nullable=True
    )

    def to_dict(self):
        return {
            "id_alerta": self.id_alerta,
            "id_regla": self.id_regla,
            "id_usuario_revisor": self.id_usuario_revisor,
            "fecha_generacion": (
                self.fecha_generacion.isoformat()
                if self.fecha_generacion
                else None
            ),
            "severidad": self.severidad,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "fecha_revision": (
                self.fecha_revision.isoformat()
                if self.fecha_revision
                else None
            )
        }