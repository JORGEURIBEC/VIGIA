from app import db


class Rol(db.Model):
    __tablename__ = "roles"

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(
    db.DateTime,
    nullable=False,
    server_default=db.func.current_timestamp()
)
    def to_dict(self):
        return {
            "id_rol": self.id_rol,
            "nombre_rol": self.nombre_rol,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "fecha_creacion": (
                self.fecha_creacion.isoformat()
                if self.fecha_creacion
                else None
            )
        }