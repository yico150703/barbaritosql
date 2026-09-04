"""
Script de inicialización y carga de semillas (Seed) para Sistema de Gestión de Almacén.
Carga los roles, usuarios con contraseñas hasheadas y el árbol jerárquico de menús por rol.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    CategoriaProducto,
    InventarioCierre,
    InventarioCierreDetalle,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    OpcionMenu,
    OpcionMenuPerfil,
    OrdenCompra,
    OrdenCompraDetalle,
    Perfil,
    Producto,
    Proveedor,
    Usuario,
    UsuarioPerfil,
)

PERFILES_DATA = [
    {
        "IdPerfil": 1,
        "Nombre": "Técnico",
        "Descripcion": "Maneja la base de datos",
    },
    {
        "IdPerfil": 2,
        "Nombre": "Gerente",
        "Descripcion": "Encargado de supervisar y administrar los recursos",
    },
    {
        "IdPerfil": 3,
        "Nombre": "Miembro de equipo",
        "Descripcion": "Usuario menor que podrá recepcionar y verificar el inventario",
    },
]

# Clave por defecto para todos los usuarios de prueba: password123
PASSWORD_DEFAULT = "password123"

USUARIOS_DATA = [
    {
        "IdUsuario": 1,
        "DNI": 90999999,
        "Nombres": "Carlos",
        "ApellidoPaterno": "Rodríguez",
        "ApellidoMaterno": "García",
        "Celular": 999111222,
        "CorreoElectronico": "crodriguez@gmail.com",
        "perfiles": [1],  # Técnico (acceso general a todos los paneles)
    },
    {
        "IdUsuario": 2,
        "DNI": 56879826,
        "Nombres": "José",
        "ApellidoPaterno": "Ríos",
        "ApellidoMaterno": "Pérez",
        "Celular": 988222333,
        "CorreoElectronico": "jrios@gmail.com",
        "perfiles": [2],  # Gerente (acceso directo)
    },
    {
        "IdUsuario": 3,
        "DNI": 90157845,
        "Nombres": "Roberto",
        "ApellidoPaterno": "Díaz",
        "ApellidoMaterno": "Castro",
        "Celular": 977333444,
        "CorreoElectronico": "rdiaz@gmail.com",
        "perfiles": [3],  # Miembro de equipo (acceso directo)
    },
]

# Definición de las Opciones de Menú (sincronizadas con la navegación por paneles)
OPCIONES_DATA = [
    (1, "Inicio", "/home", "Inicio del sistema", None),
    (2, "Panel técnico", "/home/panel-tecnico", "Módulo técnico del sistema", 1),
    (3, "Panel gerencial", "/home/panel-gerencial", "Vista ejecutiva general", 1),
    (4, "Panel de miembro de equipo", "/home/panel-miembro-equipo", "Acceso operativo", 1),
    (5, "Gestión de usuarios", "/home/usuarios", "Mantenimiento de cuentas de usuario", None),
    (6, "Editar usuario", "/home/usuarios/editar", "Formulario de edición de usuario", 5),
    (7, "Seguimiento de actividades", "/home/actividades", "Seguimiento de actividades y bitácora", None),
    (8, "Gestión de stock", "/home/stock", "Consulta de existencias e inventario", None),
    (9, "Editar stock", "/home/stock/editar", "Ajuste y modificación de existencias", 8),
    (10, "Gestión de ítems", "/home/items", "Catálogo de productos y artículos", None),
    (11, "Agregar ítem", "/home/items/agregar", "Registro de nuevos artículos", 10),
    (12, "Editar ítem", "/home/items/editar", "Modificación de catálogo de ítems", 10),
    (13, "Reportes de inventario", "/home/reportes", "Generación de métricas y reportes ejecutivos", None),
    (14, "Entradas y salidas", "/home/movimientos", "Kardex de entradas y salidas de almacén", None),
    (15, "Registrar movimiento", "/home/movimientos/registrar", "Formulario de registro de movimientos", 14),
    (16, "Editar movimiento", "/home/movimientos/editar", "Corrección de transacciones de almacén", 14),
    (17, "Gestión de miembros de equipo", "/home/miembros-equipo", "Administración del personal operativo", None),
    (18, "Agregar miembro de equipo", "/home/miembros-equipo/agregar", "Alta de nuevo personal", 17),
    (19, "Editar miembro de equipo", "/home/miembros-equipo/editar", "Edición de fichas del personal", 17),
    (20, "Solicitudes de compra", "/home/solicitudes", "Monitoreo de solicitudes y compras", None),
    (21, "Registrar solicitud", "/home/solicitudes/registrar", "Registro de solicitud de compra", 20),
    (22, "Detalle de solicitud", "/home/solicitudes/detalle", "Visualización de solicitudes de compra", 20),
    (23, "Editar solicitud", "/home/solicitudes/editar", "Modificación de solicitudes de compra", 20),
    (24, "Realizar inventario", "/home/inventario/realizar", "Toma física de inventario cíclico", None),
    (25, "Órdenes de compra", "/home/ordenes-compra", "Emisión de órdenes de aprovisionamiento", None),
    (26, "Detalle de orden de compra", "/home/ordenes-compra/detalle", "Detalle de orden de compra", 25),
    (27, "Mantenimiento de Perfiles", "/home/perfiles", "Gestión de roles y perfiles", 2),
    (28, "Mantenimiento de Opciones de Menú", "/home/opciones-menu", "Gestión jerárquica de menús", 2),
]

ASIGNACIONES_DATA = [
    # TÉCNICO (1)
    (1, 1, 1),
    (2, 1, 2),
    (27, 1, 1),
    (28, 1, 2),
    (3, 1, 3),
    (4, 1, 4),

    # GERENTE (2)
    (1, 2, 1),
    (5, 2, 2),
    (6, 2, 1),
    (7, 2, 3),
    (8, 2, 4),
    (9, 2, 1),
    (10, 2, 5),
    (11, 2, 1),
    (12, 2, 2),
    (13, 2, 6),
    (14, 2, 7),
    (15, 2, 1),
    (16, 2, 2),
    (17, 2, 8),
    (18, 2, 1),
    (19, 2, 2),
    (20, 2, 9),
    (21, 2, 1),
    (22, 2, 2),
    (23, 2, 3),
    (24, 2, 10),
    (25, 2, 11),
    (26, 2, 1),

    # MIEMBRO DE EQUIPO (3)
    (1, 3, 1),
    (8, 3, 2),
    (14, 3, 3),
    (15, 3, 1),
    (20, 3, 4),
    (24, 3, 5),
]

CATEGORIAS_DATA = [
    {"id_categoria": 1, "nombre": "Insumos de Cocina", "prefijo": "INS"},
    {"id_categoria": 2, "nombre": "Abarrotes y Granos", "prefijo": "ABA"},
    {"id_categoria": 3, "nombre": "Carnes y Embutidos", "prefijo": "CAR"},
    {"id_categoria": 4, "nombre": "Bebidas y Licores", "prefijo": "BEB"},
]

PROVEEDORES_DATA = [
    {"id_proveedor": 1, "nombre": "Distribuidora Lima S.A.C."},
    {"id_proveedor": 2, "nombre": "Agropecuaria Central"},
]

PRODUCTOS_DATA = [
    {"id_producto": 1, "codigo": "INS-001", "nombre": "Aceite Vegetal Premium", "id_categoria": 1, "id_proveedor": 1, "unidad": "Lt", "stock_minimo": 10.0},
    {"id_producto": 2, "codigo": "ABA-002", "nombre": "Arroz Superior Extra", "id_categoria": 2, "id_proveedor": 1, "unidad": "Kg", "stock_minimo": 20.0},
    {"id_producto": 3, "codigo": "CAR-003", "nombre": "Pechuga de Pollo Fresca", "id_categoria": 3, "id_proveedor": 2, "unidad": "Kg", "stock_minimo": 15.0},
    {"id_producto": 4, "codigo": "BEB-004", "nombre": "Agua Mineral 500ml", "id_categoria": 4, "id_proveedor": 1, "unidad": "Und", "stock_minimo": 30.0},
]


def poblar_datos(app_instance=None):
    """
    Función idempotente para poblar perfiles, usuarios de prueba,
    menús del sistema, categorías y productos iniciales.
    Garantiza el contexto de la aplicación automáticamente.
    """
    from flask import has_app_context
    if not has_app_context():
        if app_instance is None:
            from app import create_app
            app_instance = create_app()
        with app_instance.app_context():
            return _ejecutar_poblado_interno()
    else:
        return _ejecutar_poblado_interno()


def _ejecutar_poblado_interno():
    print("Verificando y sincronizando datos de base de datos...")
    db.create_all()

    print("Poblando perfiles...")
    for pdata in PERFILES_DATA:
        perfil = Perfil.query.filter_by(IdPerfil=pdata["IdPerfil"]).first()
        if not perfil:
            perfil = Perfil(
                IdPerfil=pdata["IdPerfil"],
                Nombre=pdata["Nombre"],
                Descripcion=pdata["Descripcion"],
                EstadoRegistro=1
            )
            db.session.add(perfil)
        else:
            perfil.Nombre = pdata["Nombre"]
            perfil.Descripcion = pdata["Descripcion"]
            perfil.EstadoRegistro = 1
    db.session.commit()

    print("Poblando usuarios...")
    hash_comun = generate_password_hash(PASSWORD_DEFAULT)
    for udata in USUARIOS_DATA:
        usuario = Usuario.query.filter(
            (Usuario.CorreoElectronico == udata["CorreoElectronico"]) |
            (Usuario.IdUsuario == udata["IdUsuario"])
        ).first()

        if not usuario:
            usuario = Usuario(
                IdUsuario=udata["IdUsuario"],
                DNI=str(udata["DNI"]),
                Nombres=udata["Nombres"],
                ApellidoPaterno=udata["ApellidoPaterno"],
                ApellidoMaterno=udata.get("ApellidoMaterno"),
                Celular=str(udata.get("Celular")) if udata.get("Celular") else None,
                CorreoElectronico=udata["CorreoElectronico"],
                Clave=hash_comun,
                FechaCreacion=datetime.now(),
                EstadoRegistro=1
            )
            db.session.add(usuario)
        else:
            usuario.DNI = str(udata["DNI"])
            usuario.Nombres = udata["Nombres"]
            usuario.ApellidoPaterno = udata["ApellidoPaterno"]
            usuario.ApellidoMaterno = udata.get("ApellidoMaterno")
            usuario.Celular = str(udata.get("Celular")) if udata.get("Celular") else None
            usuario.CorreoElectronico = udata["CorreoElectronico"]
            usuario.Clave = hash_comun
            usuario.EstadoRegistro = 1

        db.session.commit()

        # Asignar perfiles
        for pid in udata["perfiles"]:
            asig = UsuarioPerfil.query.filter_by(
                IdUsuario=usuario.IdUsuario,
                IdPerfil=pid
            ).first()
            if not asig:
                asig = UsuarioPerfil(
                    IdUsuario=usuario.IdUsuario,
                    IdPerfil=pid,
                    FechaAsignacion=datetime.now(),
                    EstadoRegistro=1
                )
                db.session.add(asig)
            else:
                asig.EstadoRegistro = 1
        db.session.commit()

    print("Poblando opciones de menú...")
    for id_op, nom, url, desc, padre in OPCIONES_DATA:
        opcion = OpcionMenu.query.filter_by(IdOpcionMenu=id_op).first()
        if not opcion:
            opcion = OpcionMenu(
                IdOpcionMenu=id_op,
                Nombre=nom,
                UrlMenu=url,
                Descripcion=desc,
                IdPadre=padre,
                EstadoRegistro=1
            )
            db.session.add(opcion)
        else:
            opcion.Nombre = nom
            opcion.UrlMenu = url
            opcion.Descripcion = desc
            opcion.IdPadre = padre
            opcion.EstadoRegistro = 1
    db.session.commit()

    print("Poblando asignaciones de menú por rol...")
    for id_op, id_per, orden in ASIGNACIONES_DATA:
        rel = OpcionMenuPerfil.query.filter_by(
            IdOpcionMenu=id_op,
            IdPerfil=id_per
        ).first()
        if not rel:
            rel = OpcionMenuPerfil(
                IdOpcionMenu=id_op,
                IdPerfil=id_per,
                Orden=orden,
                EstadoRegistro=1
            )
            db.session.add(rel)
        else:
            rel.Orden = orden
            rel.EstadoRegistro = 1
    db.session.commit()

    print("Poblando categorías iniciales...")
    for cdata in CATEGORIAS_DATA:
        cat = CategoriaProducto.query.filter_by(id_categoria=cdata["id_categoria"]).first()
        if not cat:
            cat = CategoriaProducto(
                id_categoria=cdata["id_categoria"],
                nombre=cdata["nombre"],
                prefijo=cdata["prefijo"],
                activo=True
            )
            db.session.add(cat)
    db.session.commit()

    print("Poblando proveedores iniciales...")
    for pdata in PROVEEDORES_DATA:
        prov = Proveedor.query.filter_by(id_proveedor=pdata["id_proveedor"]).first()
        if not prov:
            prov = Proveedor(
                id_proveedor=pdata["id_proveedor"],
                nombre=pdata["nombre"],
                activo=True
            )
            db.session.add(prov)
    db.session.commit()

    print("Poblando productos iniciales de catálogo...")
    for prdata in PRODUCTOS_DATA:
        prod = Producto.query.filter_by(id_producto=prdata["id_producto"]).first()
        if not prod:
            prod = Producto(
                id_producto=prdata["id_producto"],
                codigo=prdata["codigo"],
                nombre=prdata["nombre"],
                id_categoria=prdata["id_categoria"],
                id_proveedor=prdata["id_proveedor"],
                unidad=prdata["unidad"],
                stock_minimo=prdata["stock_minimo"],
                presentacion=1,
                activo=True
            )
            db.session.add(prod)
    db.session.commit()

    # Sincronizar secuencias en PostgreSQL
    if db.engine.dialect.name == "postgresql":
        from sqlalchemy import text
        consultas = [
            "SELECT setval('usuario_id_usuario_seq', COALESCE((SELECT MAX(id_usuario) FROM usuario), 1));",
            "SELECT setval('perfiles_id_perfil_seq', COALESCE((SELECT MAX(id_perfil) FROM perfiles), 1));",
            "SELECT setval('opcion_menu_id_opcion_menu_seq', COALESCE((SELECT MAX(id_opcion_menu) FROM opcion_menu), 1));",
            "SELECT setval('categoria_producto_id_categoria_seq', COALESCE((SELECT MAX(id_categoria) FROM categoria_producto), 1));",
            "SELECT setval('proveedor_id_proveedor_seq', COALESCE((SELECT MAX(id_proveedor) FROM proveedor), 1));",
            "SELECT setval('producto_id_producto_seq', COALESCE((SELECT MAX(id_producto) FROM producto), 1));",
        ]
        for c in consultas:
            try:
                db.session.execute(text(c))
                db.session.commit()
            except Exception:
                db.session.rollback()

    print("\nSeed completado con éxito!")
    print("------------------------------------------------------------")
    print("Usuarios de prueba cargados (Clave para todos: password123):")
    print("1. Carlos Rodríguez  -> crodriguez@gmail.com  (Técnico + Gerente)")
    print("2. José Ríos         -> jrios@gmail.com        (Gerente)")
    print("3. Roberto Díaz      -> rdiaz@gmail.com        (Miembro de equipo)")
    print("------------------------------------------------------------")


def ejecutar_seed():
    """Alias para compatibilidad retroactiva."""
    poblar_datos()


if __name__ == "__main__":
    poblar_datos()
