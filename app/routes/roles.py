from flask import Blueprint, jsonify

from app.models import Rol
from app.decorators import roles_required


roles_bp = Blueprint(
    "roles",
    __name__,
    url_prefix="/api/v1/roles"
)


@roles_bp.get("")
@roles_required("ADMINISTRADOR")
def listar_roles():

    roles = Rol.query.order_by(Rol.id_rol).all()

    return jsonify({
        "total": len(roles),
        "data": [rol.to_dict() for rol in roles]
    }), 200