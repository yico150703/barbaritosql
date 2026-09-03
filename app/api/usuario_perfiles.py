from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.usuario import UsuarioPerfil

bp = Blueprint("usuario_perfiles", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def listar_asignaciones():
    id_usuario = request.args.get("id_usuario", type=int)
    query = UsuarioPerfil.query.filter_by(EstadoRegistro=1)
    if id_usuario:
        query = query.filter_by(IdUsuario=id_usuario)

    items = query.all()
    return jsonify({
        "success": True,
        "asignaciones": [item.to_dict() for item in items]
    }), 200


@bp.route("", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def asignar_perfil():
    datos = request.get_json() or {}
    id_usuario = datos.get("idUsuario") or datos.get("IdUsuario") or datos.get("id_usuario")
    id_perfil = datos.get("idPerfil") or datos.get("IdPerfil") or datos.get("id_perfil")

    if not id_usuario or not id_perfil:
        return jsonify({"success": False, "mensaje": "idUsuario e idPerfil son obligatorios."}), 400

    id_auth = get_jwt_identity()
    asig = UsuarioPerfil.query.filter_by(IdUsuario=int(id_usuario), IdPerfil=int(id_perfil)).first()

    if asig:
        asig.EstadoRegistro = 1
        asig.UsuarioModificacion = int(id_auth) if id_auth else None
        asig.FechaModificacion = datetime.now()
    else:
        asig = UsuarioPerfil(
            IdUsuario=int(id_usuario),
            IdPerfil=int(id_perfil),
            UsuarioAsignacion=int(id_auth) if id_auth else None,
            FechaAsignacion=datetime.now(),
            EstadoRegistro=1
        )
        db.session.add(asig)

    db.session.commit()
    return jsonify({"success": True, "mensaje": "Perfil asignado correctamente.", "asignacion": asig.to_dict()}), 200


@bp.route("", methods=["DELETE"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def desasignar_perfil():
    datos = request.get_json() or {}
    id_usuario = datos.get("idUsuario") or datos.get("IdUsuario") or request.args.get("id_usuario", type=int)
    id_perfil = datos.get("idPerfil") or datos.get("IdPerfil") or request.args.get("id_perfil", type=int)

    if not id_usuario or not id_perfil:
        return jsonify({"success": False, "mensaje": "idUsuario e idPerfil son obligatorios."}), 400

    asig = UsuarioPerfil.query.filter_by(IdUsuario=int(id_usuario), IdPerfil=int(id_perfil)).first()
    if not asig:
        return jsonify({"success": False, "mensaje": "Asignación no encontrada."}), 404

    id_auth = get_jwt_identity()
    asig.EstadoRegistro = 0
    asig.UsuarioModificacion = int(id_auth) if id_auth else None
    asig.FechaModificacion = datetime.now()
    db.session.commit()

    return jsonify({"success": True, "mensaje": "Perfil desasignado lógicamente (EstadoRegistro = 0)."}), 200
