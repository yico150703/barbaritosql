"""
Script de inicialización y carga de semillas (Seed) para Sistema de Gestión de Almacén.
Carga los roles, usuarios con contraseñas hasheadas y el árbol jerárquico de menús por rol.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.opcion_menu import OpcionMenu, OpcionMenuPerfil
from app.models.perfil import Perfil
from app.models.usuario import Usuario, UsuarioPerfil

app = create_app()

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

# Definición de las Opciones de Menú
OPCIONES_DATA = [
    (1, "Home", "/dashboard", "Inicio del sistema", None),
    (2, "Técnico", "/dashboard/tecnico", "Módulo técnico del sistema", 1),
    (3, "Mantenimiento de Perfiles", "/dashboard/perfiles", "Gestión de roles y perfiles", 2),
    (4, "Mantenimiento de Opciones de Menú", "/dashboard/opciones-menu", "Gestión jerárquica de menús", 2),
    (5, "Gerencial", "/dashboard/gerencial", "Vista ejecutiva general", 1),
    (6, "ME (Miembro de Equipo)", "/dashboard/miembro-equipo", "Acceso operativo", 1),
    (7, "Gestión de usuarios", "/dashboard/usuarios", "Mantenimiento de cuentas de usuario", 1),
    (8, "Editar usuario", "/dashboard/usuarios/editar", "Formulario de edición de usuario", 7),
    (9, "Actividades", "/dashboard/actividades", "Seguimiento de actividades y bitácora", 1),
    (10, "Stock", "/dashboard/stock", "Consulta de existencias e inventario", 1),
    (11, "Editar stock", "/dashboard/stock/editar", "Ajuste y modificación de existencias", 10),
    (12, "Ítems", "/dashboard/items", "Catálogo de productos y artículos", 1),
    (13, "Agregar ítem", "/dashboard/items/agregar", "Registro de nuevos artículos", 12),
    (14, "Editar ítem", "/dashboard/items/editar", "Modificación de catálogo de ítems", 12),
    (15, "Reportes", "/dashboard/reportes", "Generación de métricas y reportes ejecutivos", 1),
    (16, "Entrada y salida", "/dashboard/movimientos", "Kardex de entradas y salidas de almacén", 1),
    (17, "Registrar entrada/salida", "/dashboard/movimientos/registrar", "Formulario de registro de movimientos", 16),
    (18, "Editar entrada/salida", "/dashboard/movimientos/editar", "Corrección de transacciones de almacén", 16),
    (19, "Gestionar miembros de equipo", "/dashboard/miembros", "Administración del personal operativo", 1),
    (20, "Agregar miembro de equipo", "/dashboard/miembros/agregar", "Alta de nuevo personal", 19),
    (21, "Editar miembro de equipo", "/dashboard/miembros/editar", "Edición de fichas del personal", 19),
    (22, "Estado de solicitud", "/dashboard/solicitudes", "Monitoreo de solicitudes y compras", 1),
    (23, "Detalle de orden de compra", "/dashboard/solicitudes/detalle-oc", "Visualización de órdenes de compra", 22),
    (24, "Editar solicitud", "/dashboard/solicitudes/editar", "Modificación de solicitudes de compra", 22),
    (25, "Realizar inventario", "/dashboard/inventario", "Toma física de inventario cíclico", 1),
    (26, "Orden de compra", "/dashboard/orden-compra", "Emisión de órdenes de aprovisionamiento", 1),
]

ASIGNACIONES_DATA = [
    # TÉCNICO (1)
    (1, 1, 1),
    (2, 1, 2),
    (3, 1, 1),
    (4, 1, 2),
    (5, 1, 3),
    (6, 1, 4),

    # GERENTE (2)
    (1, 2, 1),
    (7, 2, 2),
    (8, 2, 1),
    (9, 2, 3),
    (10, 2, 4),
    (11, 2, 1),
    (12, 2, 5),
    (13, 2, 1),
    (14, 2, 2),
    (15, 2, 6),
    (16, 2, 7),
    (17, 2, 1),
    (18, 2, 2),
    (19, 2, 8),
    (20, 2, 1),
    (21, 2, 2),
    (22, 2, 9),
    (23, 2, 1),
    (24, 2, 2),
    (25, 2, 10),
    (26, 2, 11),

    # MIEMBRO DE EQUIPO (3)
    (1, 3, 1),
    (10, 3, 2),
    (16, 3, 3),
    (17, 3, 1),
    (22, 3, 4),
    (25, 3, 5),
]


def ejecutar_seed():
    with app.app_context():
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
            # Buscar por Correo o por IdUsuario
            usuario = Usuario.query.filter(
                (Usuario.CorreoElectronico == udata["CorreoElectronico"]) |
                (Usuario.IdUsuario == udata["IdUsuario"])
            ).first()

            if not usuario:
                usuario = Usuario(
                    IdUsuario=udata["IdUsuario"],
                    DNI=udata["DNI"],
                    Nombres=udata["Nombres"],
                    ApellidoPaterno=udata["ApellidoPaterno"],
                    ApellidoMaterno=udata.get("ApellidoMaterno"),
                    Celular=udata.get("Celular"),
                    CorreoElectronico=udata["CorreoElectronico"],
                    Clave=hash_comun,
                    FechaCreacion=datetime.now(),
                    EstadoRegistro=1
                )
                db.session.add(usuario)
            else:
                usuario.DNI = udata["DNI"]
                usuario.Nombres = udata["Nombres"]
                usuario.ApellidoPaterno = udata["ApellidoPaterno"]
                usuario.ApellidoMaterno = udata.get("ApellidoMaterno")
                usuario.Celular = udata.get("Celular")
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

        print("\nSeed completado con éxito!")
        print("------------------------------------------------------------")
        print("Usuarios de prueba cargados (Clave para todos: password123):")
        print("1. Carlos Rodríguez  -> crodriguez@gmail.com  (Técnico + Gerente)")
        print("2. José Ríos         -> jrios@gmail.com        (Gerente)")
        print("3. Roberto Díaz      -> rdiaz@gmail.com        (Miembro de equipo)")
        print("------------------------------------------------------------")


if __name__ == "__main__":
    ejecutar_seed()
