"""
Script para inicializar la base de datos simplificada con exactamente 5 tablas:
1. perfiles
2. usuario
3. usuario_perfiles
4. opciones_menu (con vistas opcion_menu y OpcionesMenu)
5. opcionesmenu_perfiles (con vistas perfil_opcion_menu y OpcionesMenu_Perfiles)
"""

import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from app import create_app
from app.extensions import db

def hash_clave(clave_plana: str) -> str:
    return generate_password_hash(clave_plana)

def aplicar_esquema_y_datos():
    app = create_app()
    with app.app_context():
        print("Iniciando aplicación de esquema simplificado...")

        # 1. Eliminar tablas y vistas anteriores limpiamente
        drop_sql = """
        DO $$ 
        DECLARE 
            r RECORD;
        BEGIN
            FOR r IN (SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('OpcionesMenu_Perfiles', 'opcionesmenu_perfiles', 'perfil_opcion_menu', 'usuario_perfiles', 'OpcionesMenu', 'opciones_menu', 'opcion_menu', 'usuario', 'perfiles')) LOOP
                IF r.table_type = 'VIEW' THEN
                    EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.table_name) || ' CASCADE';
                ELSE
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.table_name) || ' CASCADE';
                END IF;
            END LOOP;
        END $$;
        """
        db.session.execute(text(drop_sql))
        db.session.commit()
        print("Tablas anteriores eliminadas limpiamente.")

        # 2. Crear las 5 tablas principales
        create_sql = """
        CREATE TABLE perfiles (
            id_perfil SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            descripcion VARCHAR(255),
            estado_registro SMALLINT DEFAULT 1 NOT NULL
        );

        CREATE TABLE usuario (
            id_usuario SERIAL PRIMARY KEY,
            dni VARCHAR(20) NOT NULL,
            nombres VARCHAR(100) NOT NULL,
            apellido_paterno VARCHAR(100) NOT NULL,
            apellido_materno VARCHAR(100),
            celular VARCHAR(20),
            correo_electronico VARCHAR(150) NOT NULL UNIQUE,
            clave VARCHAR(255) NOT NULL,
            usuario_creacion INT,
            fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            usuario_modificacion INT,
            fecha_modificacion TIMESTAMP WITHOUT TIME ZONE,
            estado_registro SMALLINT DEFAULT 1 NOT NULL
        );

        CREATE TABLE usuario_perfiles (
            id_usuario INT NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            id_perfil INT NOT NULL REFERENCES perfiles(id_perfil) ON DELETE CASCADE,
            usuario_asignacion INT NOT NULL DEFAULT 1,
            fecha_asignacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            usuario_modificacion INT,
            fecha_modificacion TIMESTAMP WITHOUT TIME ZONE,
            estado_registro SMALLINT DEFAULT 1 NOT NULL,
            PRIMARY KEY (id_usuario, id_perfil)
        );

        CREATE TABLE opciones_menu (
            id_opcion_menu INT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            url_menu VARCHAR(150) NOT NULL,
            descripcion VARCHAR(255),
            id_padre INT REFERENCES opciones_menu(id_opcion_menu) ON DELETE CASCADE,
            estado_registro SMALLINT DEFAULT 1 NOT NULL
        );

        CREATE TABLE opcionesmenu_perfiles (
            id_opcion_menu INT NOT NULL REFERENCES opciones_menu(id_opcion_menu) ON DELETE CASCADE,
            id_perfil INT NOT NULL REFERENCES perfiles(id_perfil) ON DELETE CASCADE,
            orden INT DEFAULT 1 NOT NULL,
            estado_registro SMALLINT DEFAULT 1 NOT NULL,
            PRIMARY KEY (id_opcion_menu, id_perfil)
        );

        -- Vistas de compatibilidad de nombres
        CREATE OR REPLACE VIEW "OpcionesMenu" AS SELECT * FROM opciones_menu;
        CREATE OR REPLACE VIEW opcion_menu AS SELECT * FROM opciones_menu;
        CREATE OR REPLACE VIEW "OpcionesMenu_Perfiles" AS SELECT * FROM opcionesmenu_perfiles;
        CREATE OR REPLACE VIEW perfil_opcion_menu AS SELECT * FROM opcionesmenu_perfiles;
        """
        db.session.execute(text(create_sql))
        db.session.commit()
        print("5 tablas y vistas creadas exitosamente.")

        # 3. Insertar Perfiles
        perfiles_sql = """
        INSERT INTO perfiles (id_perfil, nombre, descripcion, estado_registro) VALUES
        (1, 'Técnico', 'Maneja la base de datos', 1),
        (2, 'Gerente', 'Encargado de supervisar y administrar los recursos', 1),
        (3, 'ME', 'Usuario menor que podrá recepcionar y verificar el inventario', 1);
        SELECT setval('perfiles_id_perfil_seq', 3);
        """
        db.session.execute(text(perfiles_sql))
        db.session.commit()
        print("Perfiles insertados.")

        # 4. Insertar Usuarios con hashes reales
        clave_tec = hash_clave("Tec123*")
        clave_ger = hash_clave("Ger123*")
        clave_equ = hash_clave("Equ123*")

        usuarios_sql = text("""
        INSERT INTO usuario (id_usuario, dni, nombres, apellido_paterno, apellido_materno, celular, correo_electronico, clave, usuario_creacion, fecha_creacion, usuario_modificacion, fecha_modificacion, estado_registro) VALUES
        (1, '90999999', 'Carlos', 'Rodriguez', 'Torres', '987654321', 'crodriguez@gmail.com', :c1, NULL, '2026-08-28 09:00:00', NULL, NULL, 1),
        (2, '56879826', 'José', 'Ríos', 'Martínez', '923876122', 'jrios@gmail.com', :c2, 1, '2026-08-28 09:10:00', NULL, NULL, 1),
        (3, '90157845', 'Roberto', 'Díaz', 'Guerrero', '987456100', 'rdiaz@gmail.com', :c3, 1, '2026-08-28 09:20:00', NULL, NULL, 1);
        SELECT setval('usuario_id_usuario_seq', 3);
        """)
        db.session.execute(usuarios_sql, {"c1": clave_tec, "c2": clave_ger, "c3": clave_equ})
        db.session.commit()
        print("Usuarios insertados.")

        # 5. Insertar Usuario_Perfiles (Foto 1 - 5 filas)
        asig_sql = """
        INSERT INTO usuario_perfiles (id_usuario, id_perfil, usuario_asignacion, fecha_asignacion, usuario_modificacion, fecha_modificacion, estado_registro) VALUES
        (1, 1, 1, '2026-08-28 09:00:00', NULL, NULL, 1),
        (2, 2, 1, '2026-08-28 09:10:00', NULL, NULL, 1),
        (3, 3, 1, '2026-08-28 09:20:00', NULL, NULL, 1),
        (1, 2, 1, '2026-08-28 09:20:00', NULL, NULL, 1),
        (1, 3, 1, '2026-08-28 09:20:00', NULL, NULL, 1);
        """
        db.session.execute(text(asig_sql))
        db.session.commit()
        print("Asignaciones usuario_perfiles insertadas (5 registros).")

        # 6. Insertar Opciones_Menu (Fotos 4 y 5 - 30 filas)
        opciones_sql = """
        INSERT INTO opciones_menu (id_opcion_menu, nombre, url_menu, descripcion, id_padre, estado_registro) VALUES
        (1, 'Inicio', '/home', 'Página principal del sistema', NULL, 1),
        (2, 'Panel técnico', '/home/panel-tecnico', 'Panel principal del perfil técnico', 1, 1),
        (3, 'Panel gerencial', '/home/panel-gerencial', 'Panel principal del perfil gerente', 1, 1),
        (4, 'Panel de miembro de equipo', '/home/panel-miembro-equipo', 'Panel principal del perfil miembro de equipo', 1, 1),
        (5, 'Mantenimiento de perfiles', '/home/perfiles', 'Permite consultar de roles y privilegios de acceso al sistema (Tabla Perfiles).', NULL, 1),
        (6, 'Editar Perfiles', '/home/perfiles/editar', 'Permite la actualización de nombres de perfiles, descripciones y control de estado de registro.', 5, 1),
        (7, 'Mantenimiento de Opciones de Menú', '/home/opciones-menu', 'Permite visualizar la estructuración jerárquica de menús (Tabla OpcionesMenu) y accesibilidad por rol.', NULL, 1),
        (8, 'Editar Opciones de Menú', '/home/opciones-menu/editar', 'Permite la actualización de títulos de menú, rutas de navegación, orden y estructura jerárquica.', 7, 1),
        (9, 'Gestión de usuarios', '/home/usuarios', 'Permite consultar y administrar los usuarios', NULL, 1),
        (10, 'Editar usuario', '/home/usuarios/editar', 'Permite modificar la información y el perfil de un usuario', 9, 1),
        (11, 'Seguimiento de actividades', '/home/actividades', 'Permite consultar las actividades propias y las realizadas por el equipo', NULL, 1),
        (12, 'Gestión de stock', '/home/stock', 'Permite consultar las existencias actuales de los items', NULL, 1),
        (13, 'Editar stock', '/home/stock/editar', 'Permite corregir el stock cuando se detecte un error', 12, 1),
        (14, 'Gestión de ítems', '/home/items', 'Permite consultar y administrar los items del inventario', NULL, 1),
        (15, 'Agregar item', '/home/items/agregar', 'Permite registrar un nuevo item', 14, 1),
        (16, 'Editar item', '/home/items/editar', 'Permite modificar la información de un item', 14, 1),
        (17, 'Reportes de inventario', '/home/reportes', 'Permite generar reportes por rango de fechas', NULL, 1),
        (18, 'Entradas y salidas', '/home/movimientos', 'Permite consultar los movimientos del inventario', NULL, 1),
        (19, 'Registrar movimiento', '/home/movimientos/registrar', 'Permite registrar entradas, salidas, préstamos, devoluciones o desechos', 18, 1),
        (20, 'Editar movimiento', '/home/movimientos/editar', 'Permite corregir la información de un movimiento', 18, 1),
        (21, 'Gestión de miembros de equipo', '/home/miembros-equipo', 'Permite consultar y administrar los miembros del equipo', NULL, 1),
        (22, 'Agregar miembro de equipo', '/home/miembros-equipo/agregar', 'Permite registrar un nuevo miembro de equipo', 21, 1),
        (23, 'Editar miembro de equipo', '/home/miembros-equipo/editar', 'Permite modificar o desactivar un miembro de equipo', 21, 1),
        (24, 'Solicitudes de compra', '/home/solicitudes', 'Permite consultar el estado de las solicitudes', NULL, 1),
        (25, 'Registrar solicitud', '/home/solicitudes/registrar', 'Permite generar una nueva solicitud de compra', 24, 1),
        (26, 'Detalle de solicitud', '/home/solicitudes/detalle', 'Permite consultar los productos, cantidades y estado de una solicitud', 24, 1),
        (27, 'Editar solicitud', '/home/solicitudes/editar', 'Permite modificar una solicitud pendiente', 24, 1),
        (28, 'Realizar inventario', '/home/inventario-realizar', 'Permite efectuar el conteo y registrar el inventario por fecha', NULL, 1),
        (29, 'Órdenes de compra', '/home/ordenes-compra', 'Permite consultar y administrar las órdenes de compra', NULL, 1),
        (30, 'Detalle de orden de compra', '/home/ordenes-compra/detalle', 'Permite consultar los productos y cantidades de una orden de compra', 29, 1);
        """
        db.session.execute(text(opciones_sql))
        db.session.commit()
        print("Opciones de Menú insertadas (30 registros).")

        # 7. Insertar OpcionesMenu_Perfiles (Fotos 2 y 3 - 43 filas)
        om_perfiles_sql = """
        INSERT INTO opcionesmenu_perfiles (id_opcion_menu, id_perfil, orden, estado_registro) VALUES
        -- Foto 2
        (1, 1, 1, 1),
        (1, 2, 1, 1),
        (1, 3, 1, 1),
        (2, 1, 2, 1),
        (3, 1, 2, 1),
        (4, 1, 2, 1),
        (5, 1, 3, 1),
        (7, 1, 3, 1),
        (9, 1, 3, 1),
        (9, 2, 2, 1),
        (11, 2, 2, 1),
        (12, 2, 2, 1),
        (12, 3, 2, 1),
        (14, 2, 2, 1),
        (17, 2, 2, 1),
        (18, 2, 2, 1),
        (18, 3, 2, 1),
        (21, 2, 2, 1),
        (24, 2, 2, 1),
        -- Foto 3
        (24, 3, 2, 1),
        (28, 2, 2, 1),
        (28, 3, 2, 1),
        (29, 2, 2, 1),
        (6, 1, 4, 1),
        (8, 1, 4, 1),
        (6, 2, 3, 1),
        (8, 2, 3, 1),
        (10, 1, 4, 1),
        (10, 2, 3, 1),
        (13, 2, 3, 1),
        (15, 2, 3, 1),
        (16, 2, 3, 1),
        (19, 2, 3, 1),
        (19, 3, 3, 1),
        (20, 2, 3, 1),
        (20, 3, 3, 1),
        (22, 2, 3, 1),
        (23, 2, 3, 1),
        (25, 2, 3, 1),
        (26, 2, 3, 1),
        (26, 3, 3, 1),
        (27, 2, 3, 1),
        (30, 2, 3, 1);
        """
        db.session.execute(text(om_perfiles_sql))
        db.session.commit()
        print("OpcionesMenu_Perfiles insertadas (43 registros).")

        print("¡Base de datos simplificada creada y poblada con éxito!")

if __name__ == "__main__":
    aplicar_esquema_y_datos()
