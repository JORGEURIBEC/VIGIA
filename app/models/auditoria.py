from app import db


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    # ============================================================
    # CLAVE PRIMARIA
    # ============================================================

    id_auditoria = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # ============================================================
    # USUARIO QUE REALIZA LA ACCIÓN
    # ============================================================

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey(
            "usuarios.id_usuario",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # ============================================================
    # ACCIÓN REALIZADA
    # Ejemplos:
    # CREAR_INCIDENTE
    # ACTUALIZAR_INCIDENTE
    # ACTUALIZAR_ALERTA
    # ============================================================

    accion = db.Column(
        db.String(150),
        nullable=False
    )

    # ============================================================
    # ENTIDAD AFECTADA
    # Ejemplos:
    # INCIDENTE
    # ALERTA
    # EVENTO
    # USUARIO
    # ============================================================

    entidad_afectada = db.Column(
        db.String(100),
        nullable=False
    )

    # ============================================================
    # ID DEL REGISTRO AFECTADO
    # ============================================================

    id_registro_afectado = db.Column(
        db.BigInteger,
        nullable=True
    )

    # ============================================================
    # FECHA Y HORA
    # ============================================================

    fecha_hora = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    # ============================================================
    # RESULTADO DE LA OPERACIÓN
    # Ejemplos:
    # OK
    # ERROR
    # ============================================================

    resultado = db.Column(
        db.String(20),
        nullable=False
    )

    # ============================================================
    # DETALLE ADICIONAL
    # ============================================================

    detalle = db.Column(
        db.Text,
        nullable=True
    )

    # ============================================================
    # DIRECCIÓN IP DEL CLIENTE
    # IPv4 o IPv6
    # ============================================================

    direccion_ip = db.Column(
        db.String(45),
        nullable=True
    )

    # ============================================================
    # CONVERTIR REGISTRO A DICCIONARIO
    # ============================================================

    def to_dict(self):
        return {
            "id_auditoria": self.id_auditoria,
            "id_usuario": self.id_usuario,
            "accion": self.accion,
            "entidad_afectada": self.entidad_afectada,
            "id_registro_afectado": self.id_registro_afectado,
            "fecha_hora": (
                self.fecha_hora.strftime("%d-%m-%Y %H:%M:%S")
                if self.fecha_hora
                else None
            ),
            "resultado": self.resultado,
            "detalle": self.detalle,
            "direccion_ip": self.direccion_ip
        }

    # ============================================================
    # REPRESENTACIÓN DEL OBJETO
    # ============================================================

    def __repr__(self):
        return (
            f"<Auditoria "
            f"id={self.id_auditoria} "
            f"accion={self.accion} "
            f"entidad={self.entidad_afectada}>"
        )