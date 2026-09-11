-- =============================================================================
-- SCRIPT DE INICIALIZACIÓN Y SEED DE BASE DE DATOS POSTGRESQL (SCHEMA EXACTO)
-- Sistema de Almacén con RBAC (Técnico, Gerente/Admin, Miembro de equipo)
-- Compatible con SQLAlchemy models (snake_case) para Render / Supabase / Neon
-- =============================================================================

-- 1. LIMPIEZA DE TABLAS PREVIAS (SI EXISTEN CON SCHEMA OBSOLETO)
DROP TABLE IF EXISTS orden_compra_detalle CASCADE;
DROP TABLE IF EXISTS movimiento_inventario_detalle CASCADE;
DROP TABLE IF EXISTS inventario_cierre_detalle CASCADE;
DROP TABLE IF EXISTS inventario_cierre CASCADE;
DROP TABLE IF EXISTS orden_compra CASCADE;
DROP TABLE IF EXISTS movimiento_inventario CASCADE;
DROP TABLE IF EXISTS producto CASCADE;
DROP TABLE IF EXISTS proveedor CASCADE;
DROP TABLE IF EXISTS categoria_producto CASCADE;
DROP TABLE IF EXISTS perfil_opcion_menu CASCADE;
DROP TABLE IF EXISTS opcionesmenu_perfiles CASCADE;
DROP TABLE IF EXISTS opcionesmenu CASCADE;
DROP TABLE IF EXISTS opcion_menu CASCADE;
DROP TABLE IF EXISTS usuario_perfiles CASCADE;
DROP TABLE IF EXISTS perfiles CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

-- 2. CREACIÓN DE TABLAS DE SEGURIDAD Y MENÚS
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
    usuario_creacion INTEGER,
    fecha_creacion DATE DEFAULT NOW() NOT NULL,
    usuario_modificacion INTEGER,
    fecha_modificacion DATE,
    estado_registro SMALLINT DEFAULT 1 NOT NULL
);

CREATE TABLE usuario_perfiles (
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_perfil INTEGER NOT NULL REFERENCES perfiles(id_perfil) ON DELETE CASCADE,
    usuario_asignacion INTEGER DEFAULT 1 NOT NULL,
    fecha_asignacion DATE DEFAULT NOW() NOT NULL,
    usuario_modificacion INTEGER,
    fecha_modificacion DATE,
    estado_registro SMALLINT DEFAULT 1 NOT NULL,
    PRIMARY KEY (id_usuario, id_perfil)
);

CREATE TABLE opcion_menu (
    id_opcion_menu SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    url_menu VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),
    id_padre INTEGER REFERENCES opcion_menu(id_opcion_menu) ON DELETE CASCADE,
    estado_registro SMALLINT DEFAULT 1 NOT NULL
);

CREATE TABLE perfil_opcion_menu (
    id_perfil INTEGER NOT NULL REFERENCES perfiles(id_perfil) ON DELETE CASCADE,
    id_opcion_menu INTEGER NOT NULL REFERENCES opcion_menu(id_opcion_menu) ON DELETE CASCADE,
    puede_consultar BOOLEAN DEFAULT TRUE,
    puede_crear BOOLEAN DEFAULT FALSE,
    puede_editar BOOLEAN DEFAULT FALSE,
    puede_revisar BOOLEAN DEFAULT FALSE,
    puede_cerrar BOOLEAN DEFAULT FALSE,
    orden SMALLINT DEFAULT 0 NOT NULL,
    estado_registro SMALLINT DEFAULT 1 NOT NULL,
    PRIMARY KEY (id_perfil, id_opcion_menu)
);

-- 3. TABLAS DEL MÓDULO DE ALMACÉN
CREATE TABLE categoria_producto (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    prefijo VARCHAR(10) NOT NULL,
    siguiente_numero INTEGER DEFAULT 1,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE proveedor (
    id_proveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE producto (
    id_producto SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    id_categoria INTEGER REFERENCES categoria_producto(id_categoria),
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor),
    unidad VARCHAR(20) NOT NULL,
    stock_minimo NUMERIC(10, 3) DEFAULT 10,
    presentacion NUMERIC(10, 3) DEFAULT 1,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE movimiento_inventario (
    id_movimiento_inventario SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    tipo_movimiento VARCHAR(50) NOT NULL,
    motivo_movimiento VARCHAR(100) NOT NULL,
    fecha_movimiento DATE DEFAULT NOW() NOT NULL,
    usuario_registro INTEGER,
    local_relacionado VARCHAR(100),
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor),
    observacion VARCHAR(255)
);

CREATE TABLE movimiento_inventario_detalle (
    id_movimiento_inventario_detalle SERIAL PRIMARY KEY,
    id_movimiento_inventario INTEGER NOT NULL REFERENCES movimiento_inventario(id_movimiento_inventario),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad NUMERIC(10, 3) NOT NULL
);

CREATE TABLE orden_compra (
    id_orden_compra SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    estado_orden_compra VARCHAR(50) DEFAULT 'Pendiente',
    usuario_registro INTEGER,
    fecha_registro DATE DEFAULT NOW()
);

CREATE TABLE orden_compra_detalle (
    id_orden_compra_detalle SERIAL PRIMARY KEY,
    id_orden_compra INTEGER NOT NULL REFERENCES orden_compra(id_orden_compra),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad_solicitada NUMERIC(10, 3) NOT NULL
);

CREATE TABLE inventario_cierre (
    id_inventario_cierre SERIAL PRIMARY KEY,
    fecha_inventario DATE NOT NULL,
    estado_inventario VARCHAR(50) DEFAULT 'Completado',
    usuario_registro INTEGER,
    fecha_registro DATE DEFAULT NOW(),
    usuario_revision INTEGER,
    motivo_revision VARCHAR(255),
    observacion VARCHAR(255)
);

CREATE TABLE inventario_cierre_detalle (
    id_inventario_cierre_detalle SERIAL PRIMARY KEY,
    id_inventario_cierre INTEGER NOT NULL REFERENCES inventario_cierre(id_inventario_cierre),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    stock_contado NUMERIC(10, 3) NOT NULL
);

-- =============================================================================
-- 4. POBLADO DE DATOS (SEED)
-- =============================================================================

-- PERFILES (ROLES)
INSERT INTO perfiles (id_perfil, nombre, descripcion, estado_registro) VALUES 
(1, 'Técnico', 'Maneja la base de datos y configuración del sistema', 1),
(2, 'Gerente', 'Encargado de supervisar y administrar los recursos', 1),
(3, 'Miembro de equipo', 'Usuario operativo para recepcionar y verificar el inventario', 1);

-- USUARIOS (Carlos Rodriguez: Tec123*, José Ríos: Ger123*, Roberto Díaz: Equ123*)
INSERT INTO usuario (id_usuario, dni, nombres, apellido_paterno, apellido_materno, celular, correo_electronico, clave, usuario_creacion, fecha_creacion, usuario_modificacion, fecha_modificacion, estado_registro) VALUES
(1, '90999999', 'Carlos', 'Rodriguez', 'Torres', '987654321', 'crodriguez@gmail.com', '$2b$12$uf4lPK8fYBijFzJ7ek1ZlOvjYIxEajqIC27IIHNinBTlYSRlLaWZ2', NULL, '2026-08-28 09:00:00', NULL, NULL, 1),
(2, '56879826', 'José', 'Ríos', 'Martínez', '923876122', 'jrios@gmail.com', '$2b$12$gWqHThRLl8tZMVHgqg7vtuahBiMhWiPGCulV0m2vSOQvavjDazIPi', 1, '2026-08-28 09:10:00', NULL, NULL, 1),
(3, '90157845', 'Roberto', 'Díaz', 'Guerrero', '987456100', 'rdiaz@gmail.com', '$2b$12$d.QMPuYtQ.anZUvI58jTseyRr.JmlMMRv28qJ6LTDTGWS5GkiAIYW', 1, '2026-08-28 09:20:00', NULL, NULL, 1);

-- ASIGNACIONES DE ROLES
INSERT INTO usuario_perfiles (id_usuario, id_perfil, estado_registro) VALUES 
(1, 1, 1),
(2, 2, 1),
(3, 3, 1);

-- OPCIONES DE MENÚ JERÁRQUICAS
INSERT INTO opcion_menu (id_opcion_menu, nombre, url_menu, descripcion, id_padre, estado_registro) VALUES
(1, 'Inicio', '/home', 'Inicio del sistema', NULL, 1),
(2, 'Panel técnico', '/home/panel-tecnico', 'Módulo técnico del sistema', 1, 1),
(3, 'Panel gerencial', '/home/panel-gerencial', 'Vista ejecutiva general', 1, 1),
(4, 'Panel de miembro de equipo', '/home/panel-miembro-equipo', 'Acceso operativo', 1, 1),
(5, 'Gestión de usuarios', '/home/usuarios', 'Mantenimiento de cuentas de usuario', NULL, 1),
(6, 'Editar usuario', '/home/usuarios/editar', 'Formulario de edición de usuario', 5, 1),
(7, 'Seguimiento de actividades', '/home/actividades', 'Seguimiento de actividades y bitácora', NULL, 1),
(8, 'Gestión de stock', '/home/stock', 'Consulta de existencias e inventario', NULL, 1),
(9, 'Editar stock', '/home/stock/editar', 'Ajuste y modificación de existencias', 8, 1),
(10, 'Gestión de ítems', '/home/items', 'Catálogo de productos y artículos', NULL, 1),
(11, 'Agregar ítem', '/home/items/agregar', 'Registro de nuevos artículos', 10, 1),
(12, 'Editar ítem', '/home/items/editar', 'Modificación de catálogo de ítems', 10, 1),
(13, 'Reportes de inventario', '/home/reportes', 'Generación de métricas y reportes ejecutivos', NULL, 1),
(14, 'Entradas y salidas', '/home/movimientos', 'Kardex de entradas y salidas de almacén', NULL, 1),
(15, 'Registrar movimiento', '/home/movimientos/registrar', 'Formulario de registro de movimientos', 14, 1),
(16, 'Editar movimiento', '/home/movimientos/editar', 'Corrección de transacciones de almacén', 14, 1),
(17, 'Gestión de miembros de equipo', '/home/miembros-equipo', 'Administración del personal operativo', NULL, 1),
(18, 'Agregar miembro de equipo', '/home/miembros-equipo/agregar', 'Alta de nuevo personal', 17, 1),
(19, 'Editar miembro de equipo', '/home/miembros-equipo/editar', 'Edición de fichas del personal', 17, 1),
(20, 'Solicitudes de compra', '/home/solicitudes', 'Monitoreo de solicitudes y compras', NULL, 1),
(21, 'Registrar solicitud', '/home/solicitudes/registrar', 'Registro de solicitud de compra', 20, 1),
(22, 'Detalle de solicitud', '/home/solicitudes/detalle', 'Visualización de solicitudes de compra', 20, 1),
(23, 'Editar solicitud', '/home/solicitudes/editar', 'Modificación de solicitudes de compra', 20, 1),
(24, 'Realizar inventario', '/home/inventario-realizar', 'Toma física de inventario cíclico', NULL, 1),
(25, 'Órdenes de compra', '/home/ordenes-compra', 'Emisión de órdenes de aprovisionamiento', NULL, 1),
(26, 'Detalle de orden de compra', '/home/ordenes-compra/detalle', 'Detalle de orden de compra', 25, 1),
(27, 'Mantenimiento de Perfiles', '/home/perfiles', 'Gestión de roles y perfiles', 2, 1),
(28, 'Mantenimiento de Opciones de Menú', '/home/opciones-menu', 'Gestión jerárquica de menús', 2, 1);

-- ASIGNACIONES DE MENÚS POR ROL (perfil_opcion_menu)
-- TÉCNICO (1)
INSERT INTO perfil_opcion_menu (id_opcion_menu, id_perfil, orden, estado_registro) VALUES
(1, 1, 1, 1),
(2, 1, 2, 1),
(27, 1, 1, 1),
(28, 1, 2, 1),
(3, 1, 3, 1),
(4, 1, 4, 1);

-- GERENTE (2)
INSERT INTO perfil_opcion_menu (id_opcion_menu, id_perfil, orden, estado_registro) VALUES
(1, 2, 1, 1),
(5, 2, 2, 1),
(6, 2, 1, 1),
(7, 2, 3, 1),
(8, 2, 4, 1),
(9, 2, 1, 1),
(10, 2, 5, 1),
(11, 2, 1, 1),
(12, 2, 2, 1),
(13, 2, 6, 1),
(14, 2, 7, 1),
(15, 2, 1, 1),
(16, 2, 2, 1),
(17, 2, 8, 1),
(18, 2, 1, 1),
(19, 2, 2, 1),
(20, 2, 9, 1),
(21, 2, 1, 1),
(22, 2, 2, 1),
(23, 2, 3, 1),
(24, 2, 10, 1),
(25, 2, 11, 1),
(26, 2, 1, 1);

-- MIEMBRO DE EQUIPO (3)
INSERT INTO perfil_opcion_menu (id_opcion_menu, id_perfil, orden, estado_registro) VALUES
(1, 3, 1, 1),
(8, 3, 2, 1),
(14, 3, 3, 1),
(15, 3, 1, 1),
(16, 3, 2, 1),
(20, 3, 4, 1),
(22, 3, 1, 1),
(24, 3, 5, 1);

-- CATEGORÍAS Y PRODUCTOS INICIALES PARA EL ALMACÉN
INSERT INTO categoria_producto (id_categoria, nombre, prefijo, activo) VALUES
(1, 'Insumos de Cocina', 'INS', TRUE),
(2, 'Abarrotes y Granos', 'ABA', TRUE),
(3, 'Carnes y Embutidos', 'CAR', TRUE),
(4, 'Bebidas y Licores', 'BEB', TRUE);

INSERT INTO proveedor (id_proveedor, nombre, activo) VALUES
(1, 'Distribuidora Lima S.A.C.', TRUE),
(2, 'Agropecuaria Central', TRUE);

INSERT INTO producto (id_producto, codigo, nombre, id_categoria, id_proveedor, unidad, stock_minimo, presentacion, activo) VALUES
(1, 'INS-001', 'Aceite Vegetal Premium', 1, 1, 'Lt', 10, 1, TRUE),
(2, 'ABA-002', 'Arroz Superior Extra', 2, 1, 'Kg', 20, 1, TRUE),
(3, 'CAR-003', 'Pechuga de Pollo Fresca', 3, 2, 'Kg', 15, 1, TRUE),
(4, 'BEB-004', 'Agua Mineral 500ml', 4, 1, 'Und', 30, 1, TRUE);

-- AJUSTAR SECUENCIAS
SELECT setval('usuario_id_usuario_seq', COALESCE((SELECT MAX(id_usuario) FROM usuario), 1));
SELECT setval('perfiles_id_perfil_seq', COALESCE((SELECT MAX(id_perfil) FROM perfiles), 1));
SELECT setval('opcion_menu_id_opcion_menu_seq', COALESCE((SELECT MAX(id_opcion_menu) FROM opcion_menu), 1));
SELECT setval('categoria_producto_id_categoria_seq', COALESCE((SELECT MAX(id_categoria) FROM categoria_producto), 1));
SELECT setval('proveedor_id_proveedor_seq', COALESCE((SELECT MAX(id_proveedor) FROM proveedor), 1));
SELECT setval('producto_id_producto_seq', COALESCE((SELECT MAX(id_producto) FROM producto), 1));
