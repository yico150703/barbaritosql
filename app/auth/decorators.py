from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models.usuario import Usuario


def requiere_rol(*roles_permitidos):
    """
    Decorador que verifica que el usuario autenticado por JWT tenga
    al menos uno de los roles permitidos (por IdPerfil o Nombre).
    Admite nombres ("Técnico", "Gerente", "Miembro de equipo") o IDs (1, 2, 3).
    """
    def decorador(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            id_usuario = get_jwt_identity()
            try:
                id_usuario_int = int(id_usuario)
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "mensaje": "Identidad de token inválida.",
                    "error": "INVALID_TOKEN_IDENTITY"
                }), 401

            usuario = Usuario.query.filter_by(
                IdUsuario=id_usuario_int,
                EstadoRegistro=1
            ).first()

            if not usuario:
                return jsonify({
                    "success": False,
                    "mensaje": "Usuario no encontrado o inactivo.",
                    "error": "USER_NOT_FOUND"
                }), 403

            # Obtener perfiles activos del usuario
            perfiles_activos = usuario.perfiles_activos
            ids_activos = {p.IdPerfil for p in perfiles_activos}
            nombres_activos = {p.Nombre.lower().strip() for p in perfiles_activos}

            # Si el cliente especifica el perfil activo en la cabecera X-Perfil-Activo
            perfil_activo_header = request.headers.get("X-Perfil-Activo")
            if perfil_activo_header:
                try:
                    perfil_activo_id = int(perfil_activo_header)
                    # Si el usuario es Técnico (IdPerfil=1), tiene superpoderes para probar y simular
                    # cualquiera de los perfiles (1=Técnico, 2=Gerente, 3=Miembro de equipo).
                    # Al simular Miembro de equipo (3), debe adoptar estrictamente las restricciones del rol 3.
                    if 1 in ids_activos:
                        ids_activos = {perfil_activo_id}
                        if perfil_activo_id == 3:
                            nombres_activos = {"miembro de equipo", "miembro"}
                        elif perfil_activo_id == 2:
                            nombres_activos = {"gerente", "administrador"}
                        else:
                            nombres_activos = {"técnico", "tecnico"}
                    elif perfil_activo_id in ids_activos:
                        ids_activos = {perfil_activo_id}
                        perfil_obj = next((p for p in perfiles_activos if p.IdPerfil == perfil_activo_id), None)
                        if perfil_obj:
                            nombres_activos = {perfil_obj.Nombre.lower().strip()}
                except ValueError:
                    pass

            # Comprobar si coincide con roles_permitidos
            autorizado = False
            for rol in roles_permitidos:
                if isinstance(rol, int) and rol in ids_activos:
                    autorizado = True
                    break
                if isinstance(rol, str) and rol.lower().strip() in nombres_activos:
                    autorizado = True
                    break

            if not autorizado:
                return jsonify({
                    "success": False,
                    "mensaje": f"Acceso denegado. Se requiere uno de los siguientes roles: {list(roles_permitidos)}",
                    "error": "FORBIDDEN_ROLE"
                }), 403

            return fn(*args, **kwargs)

        return wrapper
    return decorador
