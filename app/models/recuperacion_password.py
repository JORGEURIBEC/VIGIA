from app import db


class RecuperacionPassword(db.Model):

    __tablename__ = "recuperacion_password"

    # ============================================================
    # CLAVE PRIMARIA
    # ============================================================

    id_recuperacion = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # ============================================================
    # USUARIO
    # ============================================================

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey(
            "usuarios.id_usuario",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ============================================================
    # HASH DEL TOKEN
    # ============================================================
    # Nunca se almacena el token original.

    token_hash = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        index=True
    )

    # ============================================================
    # FECHAS
    # ============================================================

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    fecha_expiracion = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )

    # ============================================================
    # ESTADO
    # ============================================================

    utilizado = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    # ============================================================
    # RELACIÓN CON USUARIO
    # ============================================================

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[id_usuario]
    )

    # ============================================================
    # CONVERSIÓN A DICCIONARIO
    # ============================================================

    def to_dict(self):

        return {
            "id_recuperacion": self.id_recuperacion,
            "id_usuario": self.id_usuario,

            # Por seguridad NO se devuelve token_hash.

            "fecha_creacion": (
                self.fecha_creacion.isoformat()
                if self.fecha_creacion
                else None
            ),

            "fecha_expiracion": (
                self.fecha_expiracion.isoformat()
                if self.fecha_expiracion
                else None
            ),

            "utilizado": self.utilizado
        }

    # ============================================================
    # REPRESENTACIÓN
    # ============================================================

    def __repr__(self):

        return (
            f"<RecuperacionPassword "
            f"id={self.id_recuperacion}, "
            f"usuario={self.id_usuario}, "
            f"utilizado={self.utilizado}>"
        )