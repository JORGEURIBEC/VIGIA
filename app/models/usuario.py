from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Usuario(db.Model):

    __tablename__ = "usuarios"

    # ============================================================
    # CLAVE PRIMARIA
    # ============================================================

    id_usuario = db.Column(
        db.Integer,
        primary_key=True
    )

    # ============================================================
    # ROL DEL USUARIO
    # ============================================================

    id_rol = db.Column(
        db.Integer,
        db.ForeignKey(
            "roles.id_rol",
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    # ============================================================
    # DATOS PERSONALES
    # ============================================================

    nombre = db.Column(
        db.String(80),
        nullable=False
    )

    apellido = db.Column(
        db.String(80),
        nullable=False
    )

    correo = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    # ============================================================
    # SEGURIDAD
    # ============================================================

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # ============================================================
    # FECHAS
    # ============================================================

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    ultimo_acceso = db.Column(
        db.DateTime,
        nullable=True
    )

    # ============================================================
    # RELACIÓN CON ROLES
    # ============================================================

    rol = db.relationship(
        "Rol",
        backref=db.backref(
            "usuarios",
            lazy=True
        )
    )

    # ============================================================
    # CONTRASEÑA
    # ============================================================

    def establecer_password(self, password):
        """
        Genera un hash seguro de la contraseña.
        La contraseña original nunca se almacena.
        """

        if not password or len(password) < 8:
            raise ValueError(
                "La contraseña debe contener al menos 8 caracteres."
            )

        self.password_hash = generate_password_hash(
            password,
            method="scrypt"
        )

    def verificar_password(self, password):
        """
        Comprueba una contraseña contra el hash almacenado.
        """

        return check_password_hash(
            self.password_hash,
            password
        )

    # ============================================================
    # CONVERTIR A DICCIONARIO
    # ============================================================

    def to_dict(self):
        """
        Representación segura del usuario.
        Nunca expone password_hash.
        """

        return {
            "id_usuario": self.id_usuario,
            "id_rol": self.id_rol,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "correo": self.correo,
            "estado": self.estado,

            "fecha_creacion": (
                self.fecha_creacion.isoformat()
                if self.fecha_creacion
                else None
            ),

            "ultimo_acceso": (
                self.ultimo_acceso.isoformat()
                if self.ultimo_acceso
                else None
            ),

            "rol": (
                self.rol.nombre_rol
                if self.rol
                else None
            )
        }

    # ============================================================
    # REPRESENTACIÓN
    # ============================================================

    def __repr__(self):

        return (
            f"<Usuario "
            f"id={self.id_usuario} "
            f"correo={self.correo} "
            f"rol={self.id_rol}>"
        )