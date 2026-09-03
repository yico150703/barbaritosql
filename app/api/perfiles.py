from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.perfil import Perfil

bp = Blueprint("perfiles", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def listar_perfiles():
    """
    Listar perfiles del sistema con soporte para búsqueda y paginación opcional.
    """
    query_str = request.args.get("q", "").strip()
    incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"
    page = request.args.get("page", type=int)
    limit = request.args.get("limit", 10, type=int)

    query = Perfil.query
    if not incluir_inactivos:
        query = query.filter(Perfil.EstadoRegistro == 1)

    if query_str:
        query = query.filter(
            Perfil.Nombre.ilike(f"%{query_str}%") |
            Perfil.Descripcion.ilike(f"%{query_str}%")
        )

    query = query.order_by(Perfil.IdPerfil.asc())

    if page:
        paginado = query.paginate(page=page, per_page=limit, error_out=False)
        return jsonify({
            "success": True,
            "perfiles": [p.to_dict() for p in paginado.items],
            "total": paginado.total,
            "pagina_actual": paginado.page,
            "total_paginas": paginado.pages
        }), 200

    items = query.all()
    return jsonify({
        "success": True,
        "perfiles": [p.to_dict() for p in items],
        "total": len(items)
    }), 200


@bp.route("/<int:id_perfil>", methods=["GET"])
@jwt_required()
def obtener_perfil(id_perfil):
    perfil = Perfil.query.filter_by(IdPerfil=id_perfil).first()
    if not perfil:
        return jsonify({"success": False, "mensaje": "Perfil no encontrado."}), 404
    return jsonify({"success": True, "perfil": perfil.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
@requiere_rol(1, "Técnico")
def crear_perfil():
    datos = request.get_json() or {}
    nombre = datos.get("nombre") or datos.get("Nombre")
    descripcion = datos.get("descripcion") or datos.get("Descripcion", "")

    if not nombre or not str(nombre).strip():
        return jsonify({"success": False, "mensaje": "El nombre del perfil es obligatorio."}), 400

    nombre_limpio = str(nombre).strip()
    if Perfil.query.filter(Perfil.Nombre.ilike(nombre_limpio), Perfil.EstadoRegistro == 1).first():
        return jsonify({"success": False, "mensaje": "Ya existe un perfil activo con ese nombre."}), 409

    nuevo_perfil = Perfil(
        Nombre=nombre_limpio,
        Descripcion=str(descripcion).strip() if descripcion else None,
        EstadoRegistro=1
    )
    db.session.add(nuevo_perfil)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Perfil creado exitosamente.",
        "perfil": nuevo_perfil.to_dict()
    }), 201


@bp.route("/<int:id_perfil>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, "Técnico")
def actualizar_perfil(id_perfil):
    perfil = Perfil.query.filter_by(IdPerfil=id_perfil).first()
    if not perfil:
        return jsonify({"success": False, "mensaje": "Perfil no encontrado."}), 404

    datos = request.get_json() or {}
    if "nombre" in datos or "Nombre" in datos:
        perfil.Nombre = str(datos.get("nombre") or datos.get("Nombre")).strip()
    if "descripcion" in datos or "Descripcion" in datos:
        desc = datos.get("descripcion") or datos.get("Descripcion")
        perfil.Descripcion = str(desc).strip() if desc else None
    if "estadoRegistro" in datos or "EstadoRegistro" in datos:
        perfil.EstadoRegistro = int(datos.get("estadoRegistro") or datos.get("EstadoRegistro"))

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Perfil actualizado exitosamente.",
        "perfil": perfil.to_dict()
    }), 200


@bp.route("/<int:id_perfil>", methods=["DELETE"])
@jwt_required()
@requiere_rol(1, "Técnico")
def desactivar_perfil(id_perfil):
    """
    Borrado lógico de perfil (EstadoRegistro = 0).
    """
    perfil = Perfil.query.filter_by(IdPerfil=id_perfil).first()
    if not perfil:
        return jsonify({"success": False, "mensaje": "Perfil no encontrado."}), 404

    perfil.EstadoRegistro = 0
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Perfil '{perfil.Nombre}' desactivado exitosamente (EstadoRegistro = 0)."
    }), 200
