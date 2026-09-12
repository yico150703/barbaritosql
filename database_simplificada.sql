-- =============================================================================
-- BASE DE DATOS SIMPLIFICADA (EXACTAMENTE 5 TABLAS)
-- Sistema de Gestión de Almacén - Módulo de Usuarios, Perfiles y Menú Dinámico
-- Tablas:
--   1. perfiles
--   2. usuario
--   3. usuario_perfiles
--   4. "OpcionesMenu"
--   5. "OpcionesMenu_Perfiles"
-- =============================================================================

-- 1. Eliminar absolutamente todas las tablas y vistas anteriores
DROP TABLE IF EXISTS actividad_sistema CASCADE;
DROP TABLE IF EXISTS categoria_producto CASCADE;
DROP TABLE IF EXISTS inventario_cierre_detalle CASCADE;
DROP TABLE IF EXISTS inventario_cierre CASCADE;
DROP TABLE IF EXISTS movimiento_inventario_detalle CASCADE;
DROP TABLE IF EXISTS movimiento_inventario CASCADE;
DROP TABLE IF EXISTS orden_compra_detalle CASCADE;
DROP TABLE IF EXISTS orden_compra CASCADE;
DROP TABLE IF EXISTS producto CASCADE;
DROP TABLE IF EXISTS proveedor CASCADE;
DROP TABLE IF EXISTS opcionesmenu_perfiles CASCADE;
DROP TABLE IF EXISTS perfil_opcion_menu CASCADE;
DROP TABLE IF EXISTS "OpcionesMenu_Perfiles" CASCADE;
DROP TABLE IF EXISTS usuario_perfiles CASCADE;
DROP TABLE IF EXISTS opciones_menu CASCADE;
DROP TABLE IF EXISTS opcion_menu CASCADE;
DROP TABLE IF EXISTS "OpcionesMenu" CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS perfiles CASCADE;

-- Eliminar vistas residuales si existieran
DROP VIEW IF EXISTS "OpcionesMenu_Perfiles" CASCADE;
DROP VIEW IF EXISTS "OpcionesMenu" CASCADE;
DROP VIEW IF EXISTS perfil_opcion_menu CASCADE;
DROP VIEW IF EXISTS opcion_menu CASCADE;
DROP VIEW IF EXISTS opcionesmenu_perfiles CASCADE;
DROP VIEW IF EXISTS opciones_menu CASCADE;

-- -----------------------------------------------------------------------------
-- TABLA 1: perfiles
-- -----------------------------------------------------------------------------
CREATE TABLE perfiles (
    id_perfil SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado_registro SMALLINT DEFAULT 1 NOT NULL
);

-- -----------------------------------------------------------------------------
-- TABLA 2: usuario
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- TABLA 3: usuario_perfiles (Foto 1)
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- TABLA 4: "OpcionesMenu" (Fotos 4 y 5)
-- -----------------------------------------------------------------------------
CREATE TABLE "OpcionesMenu" (
    id_opcion_menu INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    url_menu VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),
    id_padre INT REFERENCES "OpcionesMenu"(id_opcion_menu) ON DELETE CASCADE,
    estado_registro SMALLINT DEFAULT 1 NOT NULL
);

-- -----------------------------------------------------------------------------
-- TABLA 5: "OpcionesMenu_Perfiles" (Fotos 2 y 3)
-- -----------------------------------------------------------------------------
CREATE TABLE "OpcionesMenu_Perfiles" (
    id_opcion_menu INT NOT NULL REFERENCES "OpcionesMenu"(id_opcion_menu) ON DELETE CASCADE,
    id_perfil INT NOT NULL REFERENCES perfiles(id_perfil) ON DELETE CASCADE,
    orden INT DEFAULT 1 NOT NULL,
    estado_registro SMALLINT DEFAULT 1 NOT NULL,
    PRIMARY KEY (id_opcion_menu, id_perfil)
);

-- =============================================================================
-- INSERCIÓN DE DATOS EXACTOS
-- =============================================================================

-- A. PERFILES (1 = Técnico, 2 = Gerente, 3 = ME)
INSERT INTO perfiles (id_perfil, nombre, descripcion, estado_registro) VALUES
(1, 'Técnico', 'Maneja la base de datos', 1),
(2, 'Gerente', 'Encargado de supervisar y administrar los recursos', 1),
(3, 'ME', 'Usuario menor que podrá recepcionar y verificar el inventario', 1);

SELECT setval('perfiles_id_perfil_seq', 3);

-- B. USUARIOS (Contraseñas: Tec123*, Ger123*, Equ123* hasheadas con bcrypt)
INSERT INTO usuario (id_usuario, dni, nombres, apellido_paterno, apellido_materno, celular, correo_electronico, clave, usuario_creacion, fecha_creacion, usuario_modificacion, fecha_modificacion, estado_registro) VALUES
(1, '90999999', 'Carlos', 'Rodriguez', 'Torres', '987654321', 'crodriguez@gmail.com', '$2b$12$KwweJSlZ6YyqQVpeTQih/OReP60t62U2Y43nkgsqA3QVpfoQryNQC', NULL, '2026-08-28 09:00:00', NULL, NULL, 1),
(2, '56879826', 'José', 'Ríos', 'Martínez', '923876122', 'jrios@gmail.com', '$2b$12$jzuqRoIbiWcHZEupQ1E5M.nM/I8q4ayuFEhDw4DTuClUIw.BrMQFS', 1, '2026-08-28 09:10:00', NULL, NULL, 1),
(3, '90157845', 'Roberto', 'Díaz', 'Guerrero', '987456100', 'rdiaz@gmail.com', '$2b$12$AR5QsMMaHaTQAtlrVhRKDu4OwFy/gVE8Nc04cBawG4Seb447yzB0a', 1, '2026-08-28 09:20:00', NULL, NULL, 1);

SELECT setval('usuario_id_usuario_seq', 3);

-- C. USUARIO_PERFILES (Foto 1 - 5 filas exactas)
INSERT INTO usuario_perfiles (id_usuario, id_perfil, usuario_asignacion, fecha_asignacion, usuario_modificacion, fecha_modificacion, estado_registro) VALUES
(1, 1, 1, '2026-08-28 09:00:00', NULL, NULL, 1),
(2, 2, 1, '2026-08-28 09:10:00', NULL, NULL, 1),
(3, 3, 1, '2026-08-28 09:20:00', NULL, NULL, 1),
(1, 2, 1, '2026-08-28 09:20:00', NULL, NULL, 1),
(1, 3, 1, '2026-08-28 09:20:00', NULL, NULL, 1);

-- D. "OpcionesMenu" (Fotos 4 y 5 - 30 filas exactas)
INSERT INTO "OpcionesMenu" (id_opcion_menu, nombre, url_menu, descripcion, id_padre, estado_registro) VALUES
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

-- E. "OpcionesMenu_Perfiles" (Fotos 2 y 3 - 43 filas exactas)
INSERT INTO "OpcionesMenu_Perfiles" (id_opcion_menu, id_perfil, orden, estado_registro) VALUES
-- Foto 2
(1, 1, 1, 1),  -- Inicio - Tecnico
(1, 2, 1, 1),  -- Inicio - Gerente
(1, 3, 1, 1),  -- Inicio - ME
(2, 1, 2, 1),  -- Panel técnico - Tecnico
(3, 1, 2, 1),  -- Panel gerencial - Tecnico
(4, 1, 2, 1),  -- Panel de miembro de equipo - Tecnico
(5, 1, 3, 1),  -- Mantenimiento de perfiles - Tecnico
(7, 1, 3, 1),  -- Mantenimiento de Opciones de Menú - Tecnico
(9, 1, 3, 1),  -- Gestión de usuarios - Tecnico
(9, 2, 2, 1),  -- Gestión de usuarios - Gerente
(11, 2, 2, 1), -- Seguimiento de actividades - Gerente
(12, 2, 2, 1), -- Gestión de stock - Gerente
(12, 3, 2, 1), -- Gestión de stock - ME
(14, 2, 2, 1), -- Gestión de ítems - Gerente
(17, 2, 2, 1), -- Reportes de inventario - Gerente
(18, 2, 2, 1), -- Entradas y salidas - Gerente
(18, 3, 2, 1), -- Entradas y salidas - ME
(21, 2, 2, 1), -- Gestión de miembros de equipo - Gerente
(24, 2, 2, 1), -- Solicitudes de compra - Gerente
-- Foto 3
(24, 3, 2, 1), -- Solicitudes de compra - ME
(28, 2, 2, 1), -- Realizar inventario - Gerente
(28, 3, 2, 1), -- Realizar inventario - ME
(29, 2, 2, 1), -- Órdenes de compra - Gerente
(6, 1, 4, 1),  -- Editar Perfiles - Tecnico
(8, 1, 4, 1),  -- Editar Opciones de Menú - Tecnico
(6, 2, 3, 1),  -- Editar Perfiles - Gerente
(8, 2, 3, 1),  -- Editar Opciones de Menú - Gerente
(10, 1, 4, 1), -- Editar usuario - Tecnico
(10, 2, 3, 1), -- Editar usuario - Gerente
(13, 2, 3, 1), -- Editar stock - Gerente
(15, 2, 3, 1), -- Agregar item - Gerente
(16, 2, 3, 1), -- Editar item - Gerente
(19, 2, 3, 1), -- Registrar movimiento - Gerente
(19, 3, 3, 1), -- Registrar movimiento - ME
(20, 2, 3, 1), -- Editar movimiento - Gerente
(20, 3, 3, 1), -- Editar movimiento - ME
(22, 2, 3, 1), -- Agregar miembro de equipo - Gerente
(23, 2, 3, 1), -- Editar miembro de equipo - Gerente
(25, 2, 3, 1), -- Registrar solicitud - Gerente
(26, 2, 3, 1), -- Detalle de solicitud - Gerente
(26, 3, 3, 1), -- Detalle de solicitud - ME
(27, 2, 3, 1), -- Editar solicitud - Gerente
(30, 2, 3, 1); -- Detalle de orden de compra - Gerente
