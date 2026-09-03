from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.opcion_menu import OpcionMenuPerfil

bp = Blueprint("opciones_menu_perfiles", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def listar_opciones_perfiles():
    id_perfil = request.args.get("id_perfil", type=int)
    query = OpcionMenuPerfil.query.filter_by(EstadoRegistro=1)
    if id_perfil:
        query = query.filter_by(IdPerfil=id_perfil)

    query = query.order_by(OpcionMenuPerfil.Orden.asc())
    items = query.all()
    return jsonify({
        "success": True,
        "opciones_perfiles": [item.to_dict() for item in items]
    }), 200


@bp.route("", methods=["POST"])
@jwt_required()
@requiere_rol(1, "Técnico")
def asignar_opcion_perfil():
    datos = request.get_json() or {}
    id_opcion = datos.get("idOpcionMenu") or datos.get("IdOpcionMenu") or datos.get("id_opcion_menu")
    id_perfil = datos.get("idPerfil") or datos.get("IdPerfil") or datos.get("id_perfil")
    orden = datos.get("orden") or datos.get("Orden", 0)

    if not id_opcion or not id_perfil:
        return jsonify({"success": False, "mensaje": "idOpcionMenu e idPerfil son obligatorios."}), 400

    asig = OpcionMenuPerfil.query.filter_by(IdOpcionMenu=int(id_opcion), IdPerfil=int(id_perfil)).first()
    if asig:
        asig.Orden = int(orden)
        asig.EstadoRegistro = 1
    else:
        asig = OpcionMenuPerfil(
            IdOpcionMenu=int(id_opcion),
            IdPerfil=int(id_perfil),
            Orden=int(orden),
            EstadoRegistro=1
        )
        db.session.add(asig)

    db.session.commit()
    return jsonify({"success": True, "mensaje": "Opción asignada al perfil correctamente.", "asignacion": asig.to_dict()}), 200


@bp.route("", methods=["DELETE"])
@jwt_required()
@requiere_rol(1, "Técnico")
def desasignar_opcion_perfil():
    datos = request.get_json() or {}
    id_opcion = datos.get("idOpcionMenu") or datos.get("IdOpcionMenu") or request.args.get("id_opcion", type=int)
    id_perfil = datos.get("idPerfil") or datos.get("IdPerfil") or request.args.get("id_perfil", type=int)

    if not id_opcion or not id_perfil:
        return jsonify({"success": False, "mensaje": "idOpcionMenu e idPerfil son obligatorios."}), 400

    asig = OpcionMenuPerfil.query.filter_by(IdOpcionMenu=int(id_opcion), IdPerfil=int(id_perfil)).first()
    if not asig:
        return jsonify({"success": False, "mensaje": "Asignación no encontrada."}), 404

    asig.EstadoRegistro = 0
    db.session.commit()

    return jsonify({"success": True, "mensaje": "Opción desasignada del perfil (EstadoRegistro = 0)."}), 200
