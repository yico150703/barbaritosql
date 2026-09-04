import traceback
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import inspect

from ..extensions import db
from ..models.usuario import Usuario

bp = Blueprint("auth", __name__)


@bp.route("/db-status", methods=["GET"])
def db_status():
    """
    Endpoint GET /api/db-status
    Inspecciona la base de datos conectada, lista tablas y usuarios existentes.
    """
    try:
        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()
        
        usuarios_info = []
        if "usuario" in tablas:
            try:
                usuarios = Usuario.query.all()
                usuarios_info = [
                    {
                        "id": u.IdUsuario,
                        "correo": u.CorreoElectronico,
                        "nombre": u.nombre_completo,
                        "roles": [p.Nombre for p in u.perfiles_activos]
                    }
                    for u in usuarios
                ]
            except Exception as u_err:
                usuarios_info = f"Error al consultar usuarios: {str(u_err)}"

        return jsonify({
            "success": True,
            "database_connected": True,
            "motor": db.engine.dialect.name,
            "tablas_encontradas": tablas,
            "total_tablas": len(tablas),
            "usuarios": usuarios_info,
            "listo_para_login": len(tablas) >= 5 and isinstance(usuarios_info, list) and len(usuarios_info) > 0
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "database_connected": False,
            "error": str(e)
        }), 500


@bp.route("/init-db", methods=["GET", "POST"])
def init_db():
    """
    Endpoint GET/POST /api/init-db
    Crea las 14 tablas maestras y puebla todos los datos iniciales (roles, usuarios, menús, productos).
    Parámetros opcionales: ?reset=true (para descartar tablas previas y recrear en limpio).
    """
    try:
        reset = request.args.get("reset", "").lower() in ["true", "1", "yes"]
        if reset:
            db.drop_all()

        db.create_all()

        from seed import poblar_datos
        poblar_datos()

        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()
        usuarios = Usuario.query.all()

        return jsonify({
            "success": True,
            "mensaje": "Base de datos inicializada y poblada exitosamente en la nube.",
            "reset_ejecutado": reset,
            "tablas_creadas": tablas,
            "total_tablas": len(tablas),
            "usuarios_cargados": [
                {
                    "id": u.IdUsuario,
                    "correo": u.CorreoElectronico,
                    "nombre": u.nombre_completo,
                    "roles": [p.Nombre for p in u.perfiles_activos]
                }
                for u in usuarios
            ]
        }), 200
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            "success": False,
            "mensaje": f"Error al inicializar base de datos: {str(e)}",
            "error": str(e)
        }), 500


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

    # Buscar usuario activo por correo con manejo robusto de excepciones de BD
    try:
        usuario = Usuario.query.filter(
            Usuario.CorreoElectronico.ilike(correo_normalizado),
            Usuario.EstadoRegistro == 1
        ).first()
    except Exception as db_err:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "DATABASE_ERROR",
            "mensaje": f"Error en la base de datos ({str(db_err)}). Las tablas pueden faltar o ser incompatibles. Visite /api/init-db para inicializarlas.",
            "sugerencia": "Ejecute GET /api/init-db para crear y poblar automáticamente las tablas."
        }), 500

    if not usuario or not usuario.verificar_clave(clave):
        return jsonify({
            "success": False,
            "mensaje": "Correo o contraseña incorrectos."
        }), 401

    try:
        perfiles_activos = usuario.perfiles_activos
    except Exception as rel_err:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "DATABASE_RELATION_ERROR",
            "mensaje": f"Error al cargar perfiles asociados ({str(rel_err)}). Visite /api/init-db.",
        }), 500

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
