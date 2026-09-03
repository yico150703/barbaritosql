-- =============================================================================
-- SCRIPT DE INICIALIZACIÓN Y SEED DE BASE DE DATOS (POSTGRESQL)
-- Sistema de Almacén con RBAC (3 Roles: Técnico, Gerente, Miembro de equipo)
-- =============================================================================

-- 1. CREACIÓN DE TABLAS
-- Tabla Usuario
CREATE TABLE IF NOT EXISTS Usuario (
    IdUsuario SERIAL PRIMARY KEY,
    DNI INTEGER NOT NULL,
    Nombres VARCHAR(100) NOT NULL,
    ApellidoPaterno VARCHAR(100) NOT NULL,
    ApellidoMaterno VARCHAR(100),
    Celular BIGINT,
    CorreoElectronico VARCHAR(150) NOT NULL UNIQUE,
    Clave VARCHAR(255) NOT NULL, -- almacenar SIEMPRE hasheada
    UsuarioCreacion INTEGER,
    FechaCreacion TIMESTAMP DEFAULT NOW(),
    UsuarioModificacion INTEGER,
    FechaModificacion TIMESTAMP,
    EstadoRegistro SMALLINT DEFAULT 1
);

-- Tabla Perfiles (roles): 1=Técnico, 2=Gerente, 3=Miembro de equipo
CREATE TABLE IF NOT EXISTS Perfiles (
    IdPerfil SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Descripcion VARCHAR(255),
    EstadoRegistro SMALLINT DEFAULT 1
);

-- Tabla intermedia Usuario_Perfiles (un usuario puede tener varios perfiles)
CREATE TABLE IF NOT EXISTS Usuario_Perfiles (
    IdUsuario INTEGER REFERENCES Usuario(IdUsuario),
    IdPerfil INTEGER REFERENCES Perfiles(IdPerfil),
    UsuarioAsignacion INTEGER,
    FechaAsignacion TIMESTAMP DEFAULT NOW(),
    UsuarioModificacion INTEGER,
    FechaModificacion TIMESTAMP,
    EstadoRegistro SMALLINT DEFAULT 1,
    PRIMARY KEY (IdUsuario, IdPerfil)
);

-- Tabla OpcionesMenu (jerárquica: IdPadre = NULL si es opción raíz)
CREATE TABLE IF NOT EXISTS OpcionesMenu (
    IdOpcionMenu SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    UrlMenu VARCHAR(150) NOT NULL,
    Descripcion VARCHAR(255),
    IdPadre INTEGER REFERENCES OpcionesMenu(IdOpcionMenu),
    EstadoRegistro SMALLINT DEFAULT 1
);

-- Tabla intermedia OpcionesMenu_Perfiles (qué opciones ve cada perfil, con orden)
CREATE TABLE IF NOT EXISTS OpcionesMenu_Perfiles (
    IdOpcionMenu INTEGER REFERENCES OpcionesMenu(IdOpcionMenu),
    IdPerfil INTEGER REFERENCES Perfiles(IdPerfil),
    Orden INTEGER,
    EstadoRegistro SMALLINT DEFAULT 1,
    PRIMARY KEY (IdOpcionMenu, IdPerfil)
);

-- -----------------------------------------------------------------------------
-- 2. CARGA DE PERFILES (ROLES)
-- -----------------------------------------------------------------------------
INSERT INTO Perfiles (IdPerfil, Nombre, Descripcion, EstadoRegistro)
VALUES 
    (1, 'Técnico', 'Maneja la base de datos', 1),
    (2, 'Gerente', 'Encargado de supervisar y administrar los recursos', 1),
    (3, 'Miembro de equipo', 'Usuario menor que podrá recepcionar y verificar el inventario', 1)
ON CONFLICT (IdPerfil) DO UPDATE 
SET Nombre = EXCLUDED.Nombre, Descripcion = EXCLUDED.Descripcion, EstadoRegistro = EXCLUDED.EstadoRegistro;

-- -----------------------------------------------------------------------------
-- 3. CARGA DE USUARIOS
-- Contraseña hasheada (pbkdf2:sha256) correspondiente a: password123
-- -----------------------------------------------------------------------------
INSERT INTO Usuario (IdUsuario, DNI, Nombres, ApellidoPaterno, ApellidoMaterno, Celular, CorreoElectronico, Clave, EstadoRegistro)
VALUES
    (1, 90999999, 'Carlos', 'Rodríguez', 'García', 999111222, 'crodriguez@gmail.com', 'scrypt:32768:8:1$m9b3xJ7c9X0Z$7b21fb37cb8d3b8412efaa87bb9cfb297b83ec50bcba4b54e7d189f7836b701c40ad17f300c3c52e448b26e2e5c8e3caecb0625470d0615566cf2c0be47c7c34', 1),
    (2, 56879826, 'José', 'Ríos', 'Pérez', 988222333, 'jrios@gmail.com', 'scrypt:32768:8:1$m9b3xJ7c9X0Z$7b21fb37cb8d3b8412efaa87bb9cfb297b83ec50bcba4b54e7d189f7836b701c40ad17f300c3c52e448b26e2e5c8e3caecb0625470d0615566cf2c0be47c7c34', 1),
    (3, 90157845, 'Roberto', 'Díaz', 'Castro', 977333444, 'rdiaz@gmail.com', 'scrypt:32768:8:1$m9b3xJ7c9X0Z$7b21fb37cb8d3b8412efaa87bb9cfb297b83ec50bcba4b54e7d189f7836b701c40ad17f300c3c52e448b26e2e5c8e3caecb0625470d0615566cf2c0be47c7c34', 1)
ON CONFLICT (IdUsuario) DO UPDATE
SET DNI = EXCLUDED.DNI, Nombres = EXCLUDED.Nombres, ApellidoPaterno = EXCLUDED.ApellidoPaterno, CorreoElectronico = EXCLUDED.CorreoElectronico, Clave = EXCLUDED.Clave, EstadoRegistro = EXCLUDED.EstadoRegistro;

-- Sincronizar secuencia de Usuario
SELECT setval('usuario_idusuario_seq', COALESCE((SELECT MAX(IdUsuario) FROM Usuario), 1));
SELECT setval('perfiles_idperfil_seq', COALESCE((SELECT MAX(IdPerfil) FROM Perfiles), 1));

-- Asignación de Roles a Usuarios
-- Carlos: Técnico (1), José: Gerente (2), Roberto: Miembro de equipo (3)
INSERT INTO Usuario_Perfiles (IdUsuario, IdPerfil, EstadoRegistro)
VALUES 
    (1, 1, 1),
    (2, 2, 1),
    (3, 3, 1)
ON CONFLICT (IdUsuario, IdPerfil) DO UPDATE SET EstadoRegistro = EXCLUDED.EstadoRegistro;

-- -----------------------------------------------------------------------------
-- 4. CARGA DE OPCIONES DE MENÚ JERÁRQUICAS
-- -----------------------------------------------------------------------------
INSERT INTO OpcionesMenu (IdOpcionMenu, Nombre, UrlMenu, Descripcion, IdPadre, EstadoRegistro)
VALUES
    (1, 'Home', '/dashboard', 'Inicio del sistema', NULL, 1),
    (2, 'Técnico', '/dashboard/tecnico', 'Módulo técnico del sistema', 1, 1),
    (3, 'Mantenimiento de Perfiles', '/dashboard/perfiles', 'Gestión de roles y perfiles', 2, 1),
    (4, 'Mantenimiento de Opciones de Menú', '/dashboard/opciones-menu', 'Gestión jerárquica de menús', 2, 1),
    (5, 'Gerencial', '/dashboard/gerencial', 'Vista ejecutiva general', 1, 1),
    (6, 'ME (Miembro de Equipo)', '/dashboard/miembro-equipo', 'Acceso operativo', 1, 1),
    (7, 'Gestión de usuarios', '/dashboard/usuarios', 'Mantenimiento de cuentas de usuario', 1, 1),
    (8, 'Editar usuario', '/dashboard/usuarios/editar', 'Formulario de edición de usuario', 7, 1),
    (9, 'Actividades', '/dashboard/actividades', 'Seguimiento de actividades y bitácora', 1, 1),
    (10, 'Stock', '/dashboard/stock', 'Consulta de existencias e inventario', 1, 1),
    (11, 'Editar stock', '/dashboard/stock/editar', 'Ajuste y modificación de existencias', 10, 1),
    (12, 'Ítems', '/dashboard/items', 'Catálogo de productos y artículos', 1, 1),
    (13, 'Agregar ítem', '/dashboard/items/agregar', 'Registro de nuevos artículos', 12, 1),
    (14, 'Editar ítem', '/dashboard/items/editar', 'Modificación de catálogo de ítems', 12, 1),
    (15, 'Reportes', '/dashboard/reportes', 'Generación de métricas y reportes ejecutivos', 1, 1),
    (16, 'Entrada y salida', '/dashboard/movimientos', 'Kardex de entradas y salidas de almacén', 1, 1),
    (17, 'Registrar entrada/salida', '/dashboard/movimientos/registrar', 'Formulario de registro de movimientos', 16, 1),
    (18, 'Editar entrada/salida', '/dashboard/movimientos/editar', 'Corrección de transacciones de almacén', 16, 1),
    (19, 'Gestionar miembros de equipo', '/dashboard/miembros', 'Administración del personal operativo', 1, 1),
    (20, 'Agregar miembro de equipo', '/dashboard/miembros/agregar', 'Alta de nuevo personal', 19, 1),
    (21, 'Editar miembro de equipo', '/dashboard/miembros/editar', 'Edición de fichas del personal', 19, 1),
    (22, 'Estado de solicitud', '/dashboard/solicitudes', 'Monitoreo de solicitudes y compras', 1, 1),
    (23, 'Detalle de orden de compra', '/dashboard/solicitudes/detalle-oc', 'Visualización de órdenes de compra', 22, 1),
    (24, 'Editar solicitud', '/dashboard/solicitudes/editar', 'Modificación de solicitudes de compra', 22, 1),
    (25, 'Realizar inventario', '/dashboard/inventario', 'Toma física de inventario cíclico', 1, 1),
    (26, 'Orden de compra', '/dashboard/orden-compra', 'Emisión de órdenes de aprovisionamiento', 1, 1)
ON CONFLICT (IdOpcionMenu) DO UPDATE
SET Nombre = EXCLUDED.Nombre, UrlMenu = EXCLUDED.UrlMenu, Descripcion = EXCLUDED.Descripcion, IdPadre = EXCLUDED.IdPadre, EstadoRegistro = EXCLUDED.EstadoRegistro;

SELECT setval('opcionesmenu_idopcionmenu_seq', COALESCE((SELECT MAX(IdOpcionMenu) FROM OpcionesMenu), 1));

-- -----------------------------------------------------------------------------
-- 5. ASIGNACIÓN DE MENÚS POR ROL (OpcionesMenu_Perfiles)
-- -----------------------------------------------------------------------------
-- ROL 1: TÉCNICO
INSERT INTO OpcionesMenu_Perfiles (IdOpcionMenu, IdPerfil, Orden, EstadoRegistro)
VALUES
    (1, 1, 1, 1),  -- Home
    (2, 1, 2, 1),  -- Home / Técnico
    (3, 1, 1, 1),  -- Mantenimiento de Perfiles (hijo de Técnico)
    (4, 1, 2, 1),  -- Mantenimiento de Opciones de Menú (hijo de Técnico)
    (5, 1, 3, 1),  -- Home / Gerencial
    (6, 1, 4, 1)   -- Home / ME (Miembro de Equipo)
ON CONFLICT (IdOpcionMenu, IdPerfil) DO UPDATE SET Orden = EXCLUDED.Orden, EstadoRegistro = EXCLUDED.EstadoRegistro;

-- ROL 2: GERENTE
INSERT INTO OpcionesMenu_Perfiles (IdOpcionMenu, IdPerfil, Orden, EstadoRegistro)
VALUES
    (1, 2, 1, 1),   -- Home
    (7, 2, 2, 1),   -- Gestión de usuarios
    (8, 2, 1, 1),   -- Editar usuario
    (9, 2, 3, 1),   -- Actividades
    (10, 2, 4, 1),  -- Stock
    (11, 2, 1, 1),  -- Editar stock
    (12, 2, 5, 1),  -- Ítems
    (13, 2, 1, 1),  -- Agregar ítem
    (14, 2, 2, 1),  -- Editar ítem
    (15, 2, 6, 1),  -- Reportes
    (16, 2, 7, 1),  -- Entrada y salida
    (17, 2, 1, 1),  -- Registrar entrada/salida
    (18, 2, 2, 1),  -- Editar entrada/salida
    (19, 2, 8, 1),  -- Gestionar miembros de equipo
    (20, 2, 1, 1),  -- Agregar miembro de equipo
    (21, 2, 2, 1),  -- Editar miembro de equipo
    (22, 2, 9, 1),  -- Estado de solicitud
    (23, 2, 1, 1),  -- Detalle orden de compra
    (24, 2, 2, 1),  -- Editar solicitud
    (25, 2, 10, 1), -- Realizar inventario
    (26, 2, 11, 1)  -- Orden de compra
ON CONFLICT (IdOpcionMenu, IdPerfil) DO UPDATE SET Orden = EXCLUDED.Orden, EstadoRegistro = EXCLUDED.EstadoRegistro;

-- ROL 3: MIEMBRO DE EQUIPO
INSERT INTO OpcionesMenu_Perfiles (IdOpcionMenu, IdPerfil, Orden, EstadoRegistro)
VALUES
    (1, 3, 1, 1),  -- Home
    (10, 3, 2, 1), -- Stock
    (16, 3, 3, 1), -- Entrada y salida
    (17, 3, 1, 1), -- Registrar entrada/salida
    (22, 3, 4, 1), -- Estado de solicitud
    (25, 3, 5, 1)  -- Realizar inventario
ON CONFLICT (IdOpcionMenu, IdPerfil) DO UPDATE SET Orden = EXCLUDED.Orden, EstadoRegistro = EXCLUDED.EstadoRegistro;
