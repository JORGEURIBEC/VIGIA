from app import db


class AlertaEvento(db.Model):
    __tablename__ = "alerta_evento"

    id_alerta = db.Column(
        db.BigInteger,
        db.ForeignKey("alertas.id_alerta"),
        primary_key=True
    )

    id_evento = db.Column(
        db.BigInteger,
        db.ForeignKey("eventos_seguridad.id_evento"),
        primary_key=True
    )

    def to_dict(self):
        return {
            "id_alerta": self.id_alerta,
            "id_evento": self.id_evento
        }