from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.opcion_menu import OpcionMenu, OpcionMenuPerfil
from ..models.perfil import Perfil
from ..models.usuario import UsuarioPerfil

bp = Blueprint("menu", __name__)


@bp.route("/menu/<int:id_usuario>/<int:id_perfil>", methods=["GET"])
@jwt_required()
def obtener_menu_perfil(id_usuario, id_perfil):
    """
    Endpoint GET /api/menu/<id_usuario>/<id_perfil>
    Devuelve el árbol jerárquico de opciones de menú asignadas al perfil del usuario.
    Reglas de negocio:
    1. El Técnico (IdPerfil = 1) tiene acceso general a todo y puede consultar el menú de cualquier rol.
    2. Para otros roles, validar que el usuario tenga asignado el perfil consultado y esté activo.
    3. Filtrar EstadoRegistro = 1 tanto en la opción como en la relación con el perfil.
    4. Ordenar por 'Orden' ascendente.
    5. Las opciones hijas (IdPadre != NULL) solo se muestran si su padre también está
       activo y asignado a este perfil.
    """
    # Validar que el usuario tenga asignado el perfil consultado y esté activo,
    # o bien que sea Técnico (con acceso general a los 3 paneles).
    es_tecnico = (
        db.session.query(UsuarioPerfil)
        .join(Perfil, UsuarioPerfil.IdPerfil == Perfil.IdPerfil)
        .filter(
            UsuarioPerfil.IdUsuario == id_usuario,
            UsuarioPerfil.EstadoRegistro == 1,
            (Perfil.IdPerfil == 1) | (Perfil.Nombre.ilike("%técnico%")) | (Perfil.Nombre.ilike("%tecnico%"))
        )
        .first() is not None
    )

    if not es_tecnico:
        asignacion = UsuarioPerfil.query.filter_by(
            IdUsuario=id_usuario,
            IdPerfil=id_perfil,
            EstadoRegistro=1
        ).first()

        if not asignacion:
            return jsonify({
                "success": False,
                "mensaje": f"El usuario {id_usuario} no tiene asignado el perfil {id_perfil} o está inactivo."
            }), 403

    # Obtener todas las opciones de menú asignadas al perfil con EstadoRegistro = 1
    relaciones = (
        db.session.query(OpcionMenuPerfil, OpcionMenu)
        .join(OpcionMenu, OpcionMenuPerfil.IdOpcionMenu == OpcionMenu.IdOpcionMenu)
        .filter(
            OpcionMenuPerfil.IdPerfil == id_perfil,
            OpcionMenuPerfil.EstadoRegistro == 1,
            OpcionMenu.EstadoRegistro == 1
        )
        .order_by(OpcionMenuPerfil.Orden.asc(), OpcionMenu.IdOpcionMenu.asc())
        .all()
    )

    if not relaciones:
        return jsonify({
            "success": True,
            "menu": []
        }), 200

    # Conjunto de IDs asignados y activos para validación de jerarquía
    ids_asignados = {omp.IdOpcionMenu for omp, _ in relaciones}

    # Estructurar los nodos iniciales
    nodos = {}
    for omp, op in relaciones:
        nodos[op.IdOpcionMenu] = {
            "idOpcionMenu": op.IdOpcionMenu,
            "nombre": op.Nombre,
            "urlMenu": op.UrlMenu,
            "descripcion": op.Descripcion or "",
            "idPadre": op.IdPadre,
            "orden": omp.Orden,
            "hijos": []
        }

    arbol_menu = []

    # Construir el árbol jerárquico respetando la regla del padre
    for id_op, nodo in nodos.items():
        id_padre = nodo["idPadre"]
        if id_padre is None:
            # Opción raíz
            arbol_menu.append(nodo)
        else:
            # Opción hija: solo se agrega si el padre existe y está en las opciones asignadas
            if id_padre in nodos:
                nodos[id_padre]["hijos"].append(nodo)
            # Si el padre no está asignado o no está activo, la hija se descarta según la regla

    # Asegurar ordenamiento de hijos por 'orden'
    def ordenar_hijos(items):
        items.sort(key=lambda x: (x["orden"], x["idOpcionMenu"]))
        for item in items:
            if item["hijos"]:
                ordenar_hijos(item["hijos"])

    ordenar_hijos(arbol_menu)

    return jsonify({
        "success": True,
        "menu": arbol_menu
    }), 200
