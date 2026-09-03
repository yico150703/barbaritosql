from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..models.usuario import Usuario

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login():
    """
    Endpoint POST /api/login
    Recibe correo y clave, valida contra la BD (clave hasheada),
    y devuelve un JWT con IdUsuario y la lista de perfiles activos del usuario.
    """
    datos = request.get_json() or {}
    correo = datos.get("correo") or datos.get("correoElectronico")
    clave = datos.get("clave") or datos.get("password")

    if not correo or not clave:
        return jsonify({
            "success": False,
            "mensaje": "Debes proporcionar correo electrónico y clave."
        }), 400

    correo_normalizado = str(correo).strip().lower()

    # Buscar usuario activo por correo
    usuario = Usuario.query.filter(
        Usuario.CorreoElectronico.ilike(correo_normalizado),
        Usuario.EstadoRegistro == 1
    ).first()

    if not usuario or not usuario.verificar_clave(clave):
        return jsonify({
            "success": False,
            "mensaje": "Correo o contraseña incorrectos."
        }), 401

    perfiles_activos = usuario.perfiles_activos
    if not perfiles_activos:
        return jsonify({
            "success": False,
            "mensaje": "El usuario no tiene ningún perfil asignado o activo. Contacte al administrador."
        }), 403

    # Generar claims adicionales en el JWT
    claims = {
        "id_usuario": usuario.IdUsuario,
        "nombres": usuario.Nombres,
        "apellido_paterno": usuario.ApellidoPaterno,
        "correo": usuario.CorreoElectronico,
        "perfiles": [p.to_dict() for p in perfiles_activos],
    }

    # El identity del token es el IdUsuario como string
    token = create_access_token(
        identity=str(usuario.IdUsuario),
        additional_claims=claims
    )

    return jsonify({
        "success": True,
        "token": token,
        "usuario": usuario.to_dict(),
        "perfiles": [p.to_dict() for p in perfiles_activos]
    }), 200


@bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    """
    Endpoint GET /api/auth/me
    Devuelve los datos del usuario autenticado en sesión.
    """
    id_usuario = get_jwt_identity()
    usuario = Usuario.query.filter_by(
        IdUsuario=int(id_usuario),
        EstadoRegistro=1
    ).first()

    if not usuario:
        return jsonify({
            "success": False,
            "mensaje": "Usuario no encontrado o inactivo."
        }), 404

    return jsonify({
        "success": True,
        "usuario": usuario.to_dict(),
        "perfiles": [p.to_dict() for p in usuario.perfiles_activos]
    }), 200
