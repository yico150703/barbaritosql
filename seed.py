"""
Script de inicialización y carga de semillas (Seed) para Sistema de Gestión de Almacén.
Configurado para el esquema simplificado de 5 tablas:
1. perfiles
2. usuario
3. usuario_perfiles
4. opcion_menu (y opciones_menu / OpcionesMenu)
5. perfil_opcion_menu (y opcionesmenu_perfiles / OpcionesMenu_Perfiles)
"""

from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text

from app.extensions import db
from app.models import (
    Perfil,
    Usuario,
    UsuarioPerfil,
    OpcionMenu,
    OpcionMenuPerfil,
)

# -----------------------------------------------------------------------------
# 1. PERFILES (Roles)
# -----------------------------------------------------------------------------
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
        "Nombre": "ME",
        "Descripcion": "Usuario menor que podrá recepcionar y verificar el inventario",
    },
]

# -----------------------------------------------------------------------------
# 2. USUARIOS
# -----------------------------------------------------------------------------
USUARIOS_DATA = [
    {
        "IdUsuario": 1,
        "DNI": "90999999",
        "Nombres": "Carlos",
        "ApellidoPaterno": "Rodriguez",
        "ApellidoMaterno": "Torres",
        "Celular": "987654321",
        "CorreoElectronico": "crodriguez@gmail.com",
        "Clave": "Tec123*",
        "UsuarioCreacion": None,
        "FechaCreacion": datetime(2026, 8, 28, 9, 0, 0),
        "perfiles": [1, 2, 3],  # Foto 1: asignado a 1, 2 y 3
    },
    {
        "IdUsuario": 2,
        "DNI": "56879826",
        "Nombres": "José",
        "ApellidoPaterno": "Ríos",
        "ApellidoMaterno": "Martínez",
        "Celular": "923876122",
        "CorreoElectronico": "jrios@gmail.com",
        "Clave": "Ger123*",
        "UsuarioCreacion": 1,
        "FechaCreacion": datetime(2026, 8, 28, 9, 10, 0),
        "perfiles": [2],  # Foto 1: asignado a Gerente (2)
    },
    {
        "IdUsuario": 3,
        "DNI": "90157845",
        "Nombres": "Roberto",
        "ApellidoPaterno": "Díaz",
        "ApellidoMaterno": "Guerrero",
        "Celular": "987456100",
        "CorreoElectronico": "rdiaz@gmail.com",
        "Clave": "Equ123*",
        "UsuarioCreacion": 1,
        "FechaCreacion": datetime(2026, 8, 28, 9, 20, 0),
        "perfiles": [3],  # Foto 1: asignado a ME (3)
    },
]

# -----------------------------------------------------------------------------
# 3. OPCIONES DE MENÚ (Fotos 4 y 5 - 30 filas exactas)
# -----------------------------------------------------------------------------
OPCIONES_DATA = [
    (1, "Inicio", "/home", "Página principal del sistema", None),
    (2, "Panel técnico", "/home/panel-tecnico", "Panel principal del perfil técnico", 1),
    (3, "Panel gerencial", "/home/panel-gerencial", "Panel principal del perfil gerente", 1),
    (4, "Panel de miembro de equipo", "/home/panel-miembro-equipo", "Panel principal del perfil miembro de equipo", 1),
    (5, "Mantenimiento de perfiles", "/home/perfiles", "Permite consultar de roles y privilegios de acceso al sistema (Tabla Perfiles).", None),
    (6, "Editar Perfiles", "/home/perfiles/editar", "Permite la actualización de nombres de perfiles, descripciones y control de estado de registro.", 5),
    (7, "Mantenimiento de Opciones de Menú", "/home/opciones-menu", "Permite visualizar la estructuración jerárquica de menús (Tabla OpcionesMenu) y accesibilidad por rol.", None),
    (8, "Editar Opciones de Menú", "/home/opciones-menu/editar", "Permite la actualización de títulos de menú, rutas de navegación, orden y estructura jerárquica.", 7),
    (9, "Gestión de usuarios", "/home/usuarios", "Permite consultar y administrar los usuarios", None),
    (10, "Editar usuario", "/home/usuarios/editar", "Permite modificar la información y el perfil de un usuario", 9),
    (11, "Seguimiento de actividades", "/home/actividades", "Permite consultar las actividades propias y las realizadas por el equipo", None),
    (12, "Gestión de stock", "/home/stock", "Permite consultar las existencias actuales de los items", None),
    (13, "Editar stock", "/home/stock/editar", "Permite corregir el stock cuando se detecte un error", 12),
    (14, "Gestión de ítems", "/home/items", "Permite consultar y administrar los items del inventario", None),
    (15, "Agregar item", "/home/items/agregar", "Permite registrar un nuevo item", 14),
    (16, "Editar item", "/home/items/editar", "Permite modificar la información de un item", 14),
    (17, "Reportes de inventario", "/home/reportes", "Permite generar reportes por rango de fechas", None),
    (18, "Entradas y salidas", "/home/movimientos", "Permite consultar los movimientos del inventario", None),
    (19, "Registrar movimiento", "/home/movimientos/registrar", "Permite registrar entradas, salidas, préstamos, devoluciones o desechos", 18),
    (20, "Editar movimiento", "/home/movimientos/editar", "Permite corregir la información de un movimiento", 18),
    (21, "Gestión de miembros de equipo", "/home/miembros-equipo", "Permite consultar y administrar los miembros del equipo", None),
    (22, "Agregar miembro de equipo", "/home/miembros-equipo/agregar", "Permite registrar un nuevo miembro de equipo", 21),
    (23, "Editar miembro de equipo", "/home/miembros-equipo/editar", "Permite modificar o desactivar un miembro de equipo", 21),
    (24, "Solicitudes de compra", "/home/solicitudes", "Permite consultar el estado de las solicitudes", None),
    (25, "Registrar solicitud", "/home/solicitudes/registrar", "Permite generar una nueva solicitud de compra", 24),
    (26, "Detalle de solicitud", "/home/solicitudes/detalle", "Permite consultar los productos, cantidades y estado de una solicitud", 24),
    (27, "Editar solicitud", "/home/solicitudes/editar", "Permite modificar una solicitud pendiente", 24),
    (28, "Realizar inventario", "/home/inventario-realizar", "Permite efectuar el conteo y registrar el inventario por fecha", None),
    (29, "Órdenes de compra", "/home/ordenes-compra", "Permite consultar y administrar las órdenes de compra", None),
    (30, "Detalle de orden de compra", "/home/ordenes-compra/detalle", "Permite consultar los productos y cantidades de una orden de compra", 29),
]

# -----------------------------------------------------------------------------
# 4. ASIGNACIONES OPCIONES-PERFIL (Fotos 2 y 3 - 43 filas exactas)
# (IdOpcionMenu, IdPerfil, Orden)
# -----------------------------------------------------------------------------
ASIGNACIONES_DATA = [
    # Foto 2
    (1, 1, 1),   # Inicio - Tecnico
    (1, 2, 1),   # Inicio - Gerente
    (1, 3, 1),   # Inicio - ME
    (2, 1, 2),   # Panel técnico - Tecnico
    (3, 1, 2),   # Panel gerencial - Tecnico
    (4, 1, 2),   # Panel de miembro de equipo - Tecnico
    (5, 1, 3),   # Mantenimiento de perfiles - Tecnico
    (7, 1, 3),   # Mantenimiento de Opciones de Menú - Tecnico
    (9, 1, 3),   # Gestión de usuarios - Tecnico
    (9, 2, 2),   # Gestión de usuarios - Gerente
    (11, 2, 2),  # Seguimiento de actividades - Gerente
    (12, 2, 2),  # Gestión de stock - Gerente
    (12, 3, 2),  # Gestión de stock - ME
    (14, 2, 2),  # Gestión de ítems - Gerente
    (17, 2, 2),  # Reportes de inventario - Gerente
    (18, 2, 2),  # Entradas y salidas - Gerente
    (18, 3, 2),  # Entradas y salidas - ME
    (21, 2, 2),  # Gestión de miembros de equipo - Gerente
    (24, 2, 2),  # Solicitudes de compra - Gerente
    # Foto 3
    (24, 3, 2),  # Solicitudes de compra - ME
    (28, 2, 2),  # Realizar inventario - Gerente
    (28, 3, 2),  # Realizar inventario - ME
    (29, 2, 2),  # Órdenes de compra - Gerente
    (6, 1, 4),   # Editar Perfiles - Tecnico
    (8, 1, 4),   # Editar Opciones de Menú - Tecnico
    (6, 2, 3),   # Editar Perfiles - Gerente
    (8, 2, 3),   # Editar Opciones de Menú - Gerente
    (10, 1, 4),  # Editar usuario - Tecnico
    (10, 2, 3),  # Editar usuario - Gerente
    (13, 2, 3),  # Editar stock - Gerente
    (15, 2, 3),  # Agregar item - Gerente
    (16, 2, 3),  # Editar item - Gerente
    (19, 2, 3),  # Registrar movimiento - Gerente
    (19, 3, 3),  # Registrar movimiento - ME
    (20, 2, 3),  # Editar movimiento - Gerente
    (20, 3, 3),  # Editar movimiento - ME
    (22, 2, 3),  # Agregar miembro de equipo - Gerente
    (23, 2, 3),  # Editar miembro de equipo - Gerente
    (25, 2, 3),  # Registrar solicitud - Gerente
    (26, 2, 3),  # Detalle de solicitud - Gerente
    (26, 3, 3),  # Detalle de solicitud - ME
    (27, 2, 3),  # Editar solicitud - Gerente
    (30, 2, 3),  # Detalle de orden de compra - Gerente
]


def poblar_datos(app_instance=None):
    """
    Pobla perfiles, usuarios y menús con la estructura exacta de 5 tablas.
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
    print("Sincronizando exactamente 5 tablas principales...")
    Perfil.__table__.create(db.engine, checkfirst=True)
    Usuario.__table__.create(db.engine, checkfirst=True)
    UsuarioPerfil.__table__.create(db.engine, checkfirst=True)
    OpcionMenu.__table__.create(db.engine, checkfirst=True)
    OpcionMenuPerfil.__table__.create(db.engine, checkfirst=True)

    # 1. Perfiles
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

    # 2. Usuarios
    print("Poblando usuarios...")
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
                UsuarioCreacion=udata.get("UsuarioCreacion"),
                FechaCreacion=udata.get("FechaCreacion", datetime.now()),
                EstadoRegistro=1
            )
            usuario.set_clave(udata["Clave"])
            db.session.add(usuario)
        else:
            usuario.DNI = str(udata["DNI"])
            usuario.Nombres = udata["Nombres"]
            usuario.ApellidoPaterno = udata["ApellidoPaterno"]
            usuario.ApellidoMaterno = udata.get("ApellidoMaterno")
            usuario.Celular = str(udata.get("Celular")) if udata.get("Celular") else None
            usuario.CorreoElectronico = udata["CorreoElectronico"]
            usuario.UsuarioCreacion = udata.get("UsuarioCreacion")
            usuario.FechaCreacion = udata.get("FechaCreacion", usuario.FechaCreacion)
            usuario.set_clave(udata["Clave"])
            usuario.EstadoRegistro = 1

        db.session.commit()

        # 3. Usuario_Perfiles (Foto 1)
        for pid in udata["perfiles"]:
            asig = UsuarioPerfil.query.filter_by(
                IdUsuario=usuario.IdUsuario,
                IdPerfil=pid
            ).first()
            if not asig:
                asig = UsuarioPerfil(
                    IdUsuario=usuario.IdUsuario,
                    IdPerfil=pid,
                    UsuarioAsignacion=1,
                    FechaAsignacion=datetime(2026, 8, 28, 9, 20, 0),
                    EstadoRegistro=1
                )
                db.session.add(asig)
            else:
                asig.EstadoRegistro = 1
        db.session.commit()

    # 4. Opciones de Menú (Fotos 4 y 5)
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

    # 5. OpcionesMenu_Perfiles (Fotos 2 y 3 - 43 asignaciones)
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

    print("\n¡Seed completado con éxito! Las 5 tablas están sincronizadas con las fotos.")


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        _ejecutar_poblado_interno()
