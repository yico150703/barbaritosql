from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.opcion_menu import OpcionMenu

bp = Blueprint("opciones_menu", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def listar_opciones():
    """
    Listar opciones de menú con búsqueda, paginación y filtro de EstadoRegistro = 1.
    """
    query_str = request.args.get("q", "").strip()
    incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"
    solo_padres = request.args.get("solo_padres", "false").lower() == "true"
    page = request.args.get("page", type=int)
    limit = request.args.get("limit", 15, type=int)

    query = OpcionMenu.query
    if not incluir_inactivos:
        query = query.filter(OpcionMenu.EstadoRegistro == 1)

    if solo_padres:
        query = query.filter(OpcionMenu.IdPadre.is_(None))

    if query_str:
        query = query.filter(
            OpcionMenu.Nombre.ilike(f"%{query_str}%") |
            OpcionMenu.UrlMenu.ilike(f"%{query_str}%") |
            OpcionMenu.Descripcion.ilike(f"%{query_str}%")
        )

    query = query.order_by(OpcionMenu.IdPadre.asc().nullsfirst(), OpcionMenu.IdOpcionMenu.asc())

    if page:
        paginado = query.paginate(page=page, per_page=limit, error_out=False)
        return jsonify({
            "success": True,
            "opciones": [op.to_dict() for op in paginado.items],
            "total": paginado.total,
            "pagina_actual": paginado.page,
            "total_paginas": paginado.pages
        }), 200

    items = query.all()
    return jsonify({
        "success": True,
        "opciones": [op.to_dict() for op in items],
        "total": len(items)
    }), 200


@bp.route("/<int:id_opcion>", methods=["GET"])
@jwt_required()
def obtener_opcion(id_opcion):
    opcion = OpcionMenu.query.filter_by(IdOpcionMenu=id_opcion).first()
    if not opcion:
        return jsonify({"success": False, "mensaje": "Opción de menú no encontrada."}), 404
    return jsonify({"success": True, "opcion": opcion.to_dict(incluir_hijos=True)}), 200


@bp.route("", methods=["POST"])
@jwt_required()
@requiere_rol(1, "Técnico")
def crear_opcion():
    datos = request.get_json() or {}
    nombre = datos.get("nombre") or datos.get("Nombre")
    url_menu = datos.get("urlMenu") or datos.get("UrlMenu") or datos.get("url_menu")
    descripcion = datos.get("descripcion") or datos.get("Descripcion", "")
    id_padre = datos.get("idPadre") or datos.get("IdPadre") or datos.get("id_padre")

    if not nombre or not url_menu:
        return jsonify({
            "success": False,
            "mensaje": "Los campos 'nombre' y 'urlMenu' son obligatorios."
        }), 400

    # Validar que si se especifica IdPadre, el padre exista
    if id_padre:
        padre = OpcionMenu.query.filter_by(IdOpcionMenu=int(id_padre)).first()
        if not padre:
            return jsonify({
                "success": False,
                "mensaje": f"La opción padre con ID {id_padre} no existe."
            }), 400

    nueva_opcion = OpcionMenu(
        Nombre=str(nombre).strip(),
        UrlMenu=str(url_menu).strip(),
        Descripcion=str(descripcion).strip() if descripcion else None,
        IdPadre=int(id_padre) if id_padre else None,
        EstadoRegistro=1
    )
    db.session.add(nueva_opcion)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Opción de menú creada exitosamente.",
        "opcion": nueva_opcion.to_dict()
    }), 201


@bp.route("/<int:id_opcion>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, "Técnico")
def actualizar_opcion(id_opcion):
    opcion = OpcionMenu.query.filter_by(IdOpcionMenu=id_opcion).first()
    if not opcion:
        return jsonify({"success": False, "mensaje": "Opción de menú no encontrada."}), 404

    datos = request.get_json() or {}
    if "nombre" in datos or "Nombre" in datos:
        opcion.Nombre = str(datos.get("nombre") or datos.get("Nombre")).strip()
    if "urlMenu" in datos or "UrlMenu" in datos or "url_menu" in datos:
        opcion.UrlMenu = str(datos.get("urlMenu") or datos.get("UrlMenu") or datos.get("url_menu")).strip()
    if "descripcion" in datos or "Descripcion" in datos:
        desc = datos.get("descripcion") or datos.get("Descripcion")
        opcion.Descripcion = str(desc).strip() if desc else None
    if "idPadre" in datos or "IdPadre" in datos or "id_padre" in datos:
        padre_val = datos.get("idPadre") or datos.get("IdPadre") or datos.get("id_padre")
        if padre_val and int(padre_val) != id_opcion:
            opcion.IdPadre = int(padre_val)
        else:
            opcion.IdPadre = None
    if "estadoRegistro" in datos or "EstadoRegistro" in datos:
        opcion.EstadoRegistro = int(datos.get("estadoRegistro") or datos.get("EstadoRegistro"))

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Opción de menú actualizada exitosamente.",
        "opcion": opcion.to_dict()
    }), 200


@bp.route("/<int:id_opcion>", methods=["DELETE"])
@jwt_required()
@requiere_rol(1, "Técnico")
def desactivar_opcion(id_opcion):
    """
    Borrado lógico de opción de menú (EstadoRegistro = 0).
    """
    opcion = OpcionMenu.query.filter_by(IdOpcionMenu=id_opcion).first()
    if not opcion:
        return jsonify({"success": False, "mensaje": "Opción de menú no encontrada."}), 404

    opcion.EstadoRegistro = 0

    # Desactivar recursivamente a los hijos
    for hijo in opcion.hijos:
        hijo.EstadoRegistro = 0

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Opción de menú '{opcion.Nombre}' y sus submenús fueron desactivados exitosamente (EstadoRegistro = 0)."
    }), 200
