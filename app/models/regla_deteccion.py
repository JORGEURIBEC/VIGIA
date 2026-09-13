from app import db


class ReglaDeteccion(db.Model):
    """
    Modelo que representa una regla de detección de VIGIA.

    Las reglas permiten definir condiciones que posteriormente serán
    utilizadas para analizar los eventos de seguridad y generar alertas.
    """

    __tablename__ = "reglas_deteccion"

    # ============================================================
    # IDENTIFICADOR
    # ============================================================

    id_regla = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # ============================================================
    # INFORMACIÓN GENERAL
    # ============================================================

    nombre = db.Column(
        db.String(120),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(500),
        nullable=False
    )

    # ============================================================
    # CONDICIÓN DE DETECCIÓN
    # ============================================================

    tipo_condicion = db.Column(
        db.String(80),
        nullable=False
    )

    umbral = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    intervalo_minutos = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    severidad_alerta = db.Column(
        db.String(20),
        nullable=False
    )

    # ============================================================
    # ESTADO
    # ============================================================

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

    fecha_actualizacion = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # ============================================================
    # CONVERSIÓN A DICCIONARIO
    # ============================================================

    def to_dict(self):
        """
        Convierte el objeto ReglaDeteccion a un diccionario
        para poder enviarlo como respuesta JSON desde la API.
        """

        return {
            "id_regla": self.id_regla,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo_condicion": self.tipo_condicion,
            "umbral": self.umbral,
            "intervalo_minutos": self.intervalo_minutos,
            "severidad_alerta": self.severidad_alerta,
            "estado": self.estado,
            "fecha_creacion": (
                self.fecha_creacion.isoformat()
                if self.fecha_creacion
                else None
            ),
            "fecha_actualizacion": (
                self.fecha_actualizacion.isoformat()
                if self.fecha_actualizacion
                else None
            )
        }

    # ============================================================
    # REPRESENTACIÓN
    # ============================================================

    def __repr__(self):
        return (
            f"<ReglaDeteccion "
            f"id={self.id_regla}, "
            f"nombre='{self.nombre}', "
            f"tipo='{self.tipo_condicion}', "
            f"estado={self.estado}>"
        )