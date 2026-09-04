from flask import Flask, jsonify

from .config import Config
from .errors import register_error_handlers
from .extensions import cors, db, jwt, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configuración de CORS amplia para desarrollo en puertos 5173, 5174 y 3000
    cors.init_app(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # Ruta raíz informativa
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "sistema": "Sistema de Gestión de Almacén - API REST",
            "estado": "En línea y funcionando correctamente",
            "version": "1.0.0",
            "mensaje": "El Backend de Flask está operativo. Para ingresar a la aplicación web visual (React), abre en tu navegador: http://localhost:5174 o http://localhost:5173",
            "frontend_url": "http://localhost:5174",
            "endpoints": {
                "login": "POST /api/login",
                "menu_dinamico": "GET /api/menu/<id_usuario>/<id_perfil>",
                "usuarios": "GET, POST, PUT, DELETE /api/usuarios",
                "perfiles": "GET, POST, PUT, DELETE /api/perfiles",
                "opciones_menu": "GET, POST, PUT, DELETE /api/opciones-menu",
                "items": "GET, POST, PUT /api/items",
                "stock": "GET, POST /api/stock/ajustar",
                "movimientos": "GET, POST /api/movimientos",
                "solicitudes": "GET, POST /api/solicitudes",
                "inventarios": "GET, POST /api/inventarios",
                "miembros_equipo": "GET, POST /api/miembros-equipo",
            }
        }), 200

    @jwt.unauthorized_loader
    def custom_unauthorized_response(err_msg):
        return jsonify({
            "success": False,
            "mensaje": "Se requiere un token de autenticación para acceder.",
            "error": "UNAUTHORIZED"
        }), 401

    @jwt.expired_token_loader
    def custom_expired_token_response(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "mensaje": "La sesión ha expirado (token caducado). Inicie sesión nuevamente.",
            "error": "TOKEN_EXPIRED"
        }), 401

    @jwt.invalid_token_loader
    def custom_invalid_token_response(err_msg):
        return jsonify({
            "success": False,
            "mensaje": "Token de autenticación inválido o alterado.",
            "error": "INVALID_TOKEN"
        }), 401

    # Importar modelos
    from . import models  # noqa: F401

    # Registrar Blueprints de la API REST
    from .api.auth import bp as auth_bp
    from .api.health import bp as health_bp
    from .api.menu import bp as menu_bp
    from .api.opciones_menu import bp as opciones_menu_bp
    from .api.opciones_menu_perfiles import bp as opciones_menu_perfiles_bp
    from .api.operaciones import bp as operaciones_bp
    from .api.perfiles import bp as perfiles_bp
    from .api.usuario_perfiles import bp as usuario_perfiles_bp
    from .api.usuarios import bp as usuarios_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(menu_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
    app.register_blueprint(perfiles_bp, url_prefix="/api/perfiles")
    app.register_blueprint(opciones_menu_bp, url_prefix="/api/opciones-menu")
    app.register_blueprint(usuario_perfiles_bp, url_prefix="/api/usuario-perfiles")
    app.register_blueprint(opciones_menu_perfiles_bp, url_prefix="/api/opciones-menu-perfiles")
    app.register_blueprint(operaciones_bp, url_prefix="/api")

    register_error_handlers(app)

    # Auto-verificación e inicialización automática de base de datos en nube o local
    with app.app_context():
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            tablas_requeridas = {"usuario", "perfiles", "usuario_perfiles", "opcion_menu", "perfil_opcion_menu"}

            # Verificar si la tabla usuario tiene la columna correcta 'id_usuario'
            columnas_usuario = []
            if "usuario" in tables:
                columnas_usuario = [col["name"] for col in inspector.get_columns("usuario")]

            esquema_incompatible = "usuario" in tables and "id_usuario" not in columnas_usuario

            if not tablas_requeridas.issubset(set(tables)) or esquema_incompatible:
                print(f"Esquema incompatible o ausente (id_usuario presente: {'id_usuario' in columnas_usuario}). Reiniciando esquema con CASCADE...")
                if db.engine.dialect.name == "postgresql":
                    try:
                        db.session.rollback()
                        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                        db.session.commit()
                    except Exception as drop_err:
                        print("Aviso al ejecutar DROP SCHEMA public:", drop_err)
                        db.session.rollback()
                        db.drop_all()
                        db.session.commit()
                else:
                    db.drop_all()
                    db.session.commit()

                db.create_all()
                from seed import poblar_datos
                poblar_datos()
                print("Base de datos recreada y poblada con nombres snake_case.")
            else:
                from .models.usuario import Usuario
                try:
                    if Usuario.query.count() == 0:
                        print("BD conectada sin usuarios. Ejecutando poblar_datos()...")
                        from seed import poblar_datos
                        poblar_datos()
                except Exception as schema_err:
                    print(f"Error al verificar modelo Usuario ({schema_err}). Recreando...")
                    if db.engine.dialect.name == "postgresql":
                        db.session.rollback()
                        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                        db.session.commit()
                    else:
                        db.drop_all()
                        db.session.commit()
                    db.create_all()
                    from seed import poblar_datos
                    poblar_datos()
        except Exception as init_err:
            print("Aviso al verificar/inicializar BD al inicio:", init_err)

    return app
