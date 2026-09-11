from datetime import date, datetime
from decimal import Decimal
from ..extensions import db


class CategoriaProducto(db.Model):
    __tablename__ = "categoria_producto"

    id_categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    prefijo = db.Column(db.String(10), nullable=False)
    siguiente_numero = db.Column(db.Integer, default=1)
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "idCategoria": self.id_categoria,
            "id_categoria": self.id_categoria,
            "nombre": self.nombre,
            "prefijo": self.prefijo,
            "activo": self.activo,
        }


class Proveedor(db.Model):
    __tablename__ = "proveedor"

    id_proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "idProveedor": self.id_proveedor,
            "id_proveedor": self.id_proveedor,
            "nombre": self.nombre,
            "activo": self.activo,
        }


class Producto(db.Model):
    __tablename__ = "producto"

    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey("categoria_producto.id_categoria"), nullable=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey("proveedor.id_proveedor"), nullable=True)
    unidad = db.Column(db.String(20), nullable=False)
    stock_minimo = db.Column(db.Numeric(10, 3), default=0)
    stock_actual = db.Column(db.Numeric(10, 3), nullable=True, default=0)
    presentacion = db.Column(db.Numeric(10, 3), default=1)
    activo = db.Column(db.Boolean, default=True)

    categoria = db.relationship("CategoriaProducto", lazy="joined")
    proveedor = db.relationship("Proveedor", lazy="joined")

    def to_dict(self):
        s_act = float(self.stock_actual) if self.stock_actual is not None else float(self.stock_minimo or 0) * 2.5 + 5.0
        return {
            "idProducto": self.id_producto,
            "id_producto": self.id_producto,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "idCategoria": self.id_categoria,
            "categoriaNombre": self.categoria.nombre if self.categoria else "General",
            "idProveedor": self.id_proveedor,
            "proveedorNombre": self.proveedor.nombre if self.proveedor else "Sin proveedor",
            "unidad": self.unidad,
            "stockMinimo": float(self.stock_minimo) if self.stock_minimo is not None else 0.0,
            "stock_minimo": float(self.stock_minimo) if self.stock_minimo is not None else 0.0,
            "stockActual": round(s_act, 2),
            "stock_actual": round(s_act, 2),
            "presentacion": float(self.presentacion) if self.presentacion is not None else 1.0,
            "activo": self.activo,
        }


class MovimientoInventario(db.Model):
    __tablename__ = "movimiento_inventario"

    id_movimiento_inventario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), nullable=False)
    tipo_movimiento = db.Column(db.String(50), nullable=False)  # ENTRADA, SALIDA, AJUSTE
    motivo_movimiento = db.Column(db.String(100), nullable=False)
    fecha_movimiento = db.Column(db.Date, default=date.today, nullable=False)
    usuario_registro = db.Column(db.Integer, nullable=True)
    local_relacionado = db.Column(db.String(100), nullable=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey("proveedor.id_proveedor"), nullable=True)
    observacion = db.Column(db.String(255), nullable=True)

    detalles = db.relationship("MovimientoInventarioDetalle", backref="movimiento", cascade="all, delete-orphan", lazy="joined")
    proveedor = db.relationship("Proveedor", lazy="joined")

    def to_dict(self):
        return {
            "idMovimiento": self.id_movimiento_inventario,
            "codigo": self.codigo,
            "tipoMovimiento": self.tipo_movimiento,
            "motivoMovimiento": self.motivo_movimiento,
            "fechaMovimiento": self.fecha_movimiento.isoformat() if self.fecha_movimiento else None,
            "usuarioRegistro": self.usuario_registro,
            "localRelacionado": self.local_relacionado or "",
            "idProveedor": self.id_proveedor,
            "proveedorNombre": self.proveedor.nombre if self.proveedor else "",
            "observacion": self.observacion or "",
            "detalles": [d.to_dict() for d in self.detalles],
        }


class MovimientoInventarioDetalle(db.Model):
    __tablename__ = "movimiento_inventario_detalle"

    id_movimiento_inventario_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_movimiento_inventario = db.Column(db.Integer, db.ForeignKey("movimiento_inventario.id_movimiento_inventario"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey("producto.id_producto"), nullable=False)
    cantidad = db.Column(db.Numeric(10, 3), nullable=False)

    producto = db.relationship("Producto", lazy="joined")

    def to_dict(self):
        return {
            "idDetalle": self.id_movimiento_inventario_detalle,
            "idProducto": self.id_producto,
            "productoNombre": self.producto.nombre if self.producto else "Producto",
            "productoCodigo": self.producto.codigo if self.producto else "",
            "unidad": self.producto.unidad if self.producto else "Und",
            "cantidad": float(self.cantidad),
        }


class OrdenCompra(db.Model):
    __tablename__ = "orden_compra"

    id_orden_compra = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), nullable=False)
    estado_orden_compra = db.Column(db.String(50), default="PENDIENTE")
    usuario_registro = db.Column(db.Integer, nullable=True)
    fecha_registro = db.Column(db.Date, default=date.today)

    detalles = db.relationship("OrdenCompraDetalle", backref="orden", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self):
        return {
            "idOrdenCompra": self.id_orden_compra,
            "codigo": self.codigo,
            "estadoOrdenCompra": self.estado_orden_compra,
            "usuarioRegistro": self.usuario_registro,
            "fechaRegistro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "detalles": [d.to_dict() for d in self.detalles],
            "totalItems": len(self.detalles),
        }


class OrdenCompraDetalle(db.Model):
    __tablename__ = "orden_compra_detalle"

    id_orden_compra_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_orden_compra = db.Column(db.Integer, db.ForeignKey("orden_compra.id_orden_compra"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey("producto.id_producto"), nullable=False)
    cantidad_solicitada = db.Column(db.Numeric(10, 3), nullable=False)

    producto = db.relationship("Producto", lazy="joined")

    def to_dict(self):
        return {
            "idDetalle": self.id_orden_compra_detalle,
            "idProducto": self.id_producto,
            "productoNombre": self.producto.nombre if self.producto else "Producto",
            "productoCodigo": self.producto.codigo if self.producto else "",
            "unidad": self.producto.unidad if self.producto else "Und",
            "cantidadSolicitada": float(self.cantidad_solicitada),
        }


class InventarioCierre(db.Model):
    __tablename__ = "inventario_cierre"

    id_inventario_cierre = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_inventario = db.Column(db.Date, default=date.today, nullable=False)
    estado_inventario = db.Column(db.String(50), default="CERRADO")
    usuario_registro = db.Column(db.Integer, nullable=True)
    fecha_registro = db.Column(db.Date, default=date.today)
    usuario_revision = db.Column(db.Integer, nullable=True)
    motivo_revision = db.Column(db.String(255), nullable=True)
    observacion = db.Column(db.String(255), nullable=True)

    detalles = db.relationship("InventarioCierreDetalle", backref="inventario", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self):
        return {
            "idInventario": self.id_inventario_cierre,
            "fechaInventario": self.fecha_inventario.isoformat() if self.fecha_inventario else None,
            "estadoInventario": self.estado_inventario,
            "usuarioRegistro": self.usuario_registro,
            "fechaRegistro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "observacion": self.observacion or "",
            "detalles": [d.to_dict() for d in self.detalles],
            "totalContados": len(self.detalles),
        }


class InventarioCierreDetalle(db.Model):
    __tablename__ = "inventario_cierre_detalle"

    id_inventario_cierre_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_inventario_cierre = db.Column(db.Integer, db.ForeignKey("inventario_cierre.id_inventario_cierre"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey("producto.id_producto"), nullable=False)
    stock_contado = db.Column(db.Numeric(10, 3), nullable=False)

    producto = db.relationship("Producto", lazy="joined")

    def to_dict(self):
        return {
            "idDetalle": self.id_inventario_cierre_detalle,
            "idProducto": self.id_producto,
            "productoNombre": self.producto.nombre if self.producto else "Producto",
            "productoCodigo": self.producto.codigo if self.producto else "",
            "unidad": self.producto.unidad if self.producto else "Und",
            "stockContado": float(self.stock_contado),
        }


class ActividadSistema(db.Model):
    __tablename__ = "actividad_sistema"

    id_actividad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, nullable=True)
    usuario_nombre = db.Column(db.String(150), nullable=False, default="Usuario")
    usuario_rol = db.Column(db.String(100), nullable=False, default="Operativo")
    tipo_accion = db.Column(db.String(50), nullable=False)  # CREAR, EDITAR, ELIMINAR, AJUSTE, MOVIMIENTO, INVENTARIO, SOLICITUD
    entidad = db.Column(db.String(50), nullable=False)      # USUARIO, PRODUCTO, STOCK, KARDEX, SOLICITUD, INVENTARIO, MIEMBRO
    descripcion = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            "idActividad": self.id_actividad,
            "idUsuario": self.id_usuario,
            "usuarioNombre": self.usuario_nombre,
            "usuarioRol": self.usuario_rol,
            "tipoAccion": self.tipo_accion,
            "entidad": self.entidad,
            "descripcion": self.descripcion,
            "fechaHora": self.fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_hora else "",
            "fechaFormateada": self.fecha_hora.strftime("%d/%m/%Y %H:%M") if self.fecha_hora else "",
        }

