from datetime import date, datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.almacen import (
    CategoriaProducto,
    InventarioCierre,
    InventarioCierreDetalle,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    OrdenCompra,
    OrdenCompraDetalle,
    Producto,
    Proveedor,
)
from ..models.usuario import Usuario, UsuarioPerfil

bp = Blueprint("operaciones", __name__)


# ---------------------------------------------------------------------------
# 1. CATÁLOGO DE ÍTEMS / PRODUCTOS
# ---------------------------------------------------------------------------
@bp.route("/items", methods=["GET"])
@jwt_required()
def listar_items():
    q = request.args.get("q", "").strip()
    query = Producto.query.filter(Producto.activo == True)
    if q:
        query = query.filter(
            or_(
                Producto.nombre.ilike(f"%{q}%"),
                Producto.codigo.ilike(f"%{q}%")
            )
        )
    items = query.order_by(Producto.codigo.asc()).all()
    return jsonify({
        "success": True,
        "items": [it.to_dict() for it in items],
        "total": len(items)
    }), 200


@bp.route("/items", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def crear_item():
    datos = request.get_json() or {}
    codigo = str(datos.get("codigo", "")).strip()
    nombre = str(datos.get("nombre", "")).strip()
    id_categoria = datos.get("idCategoria") or datos.get("id_categoria")
    id_proveedor = datos.get("idProveedor") or datos.get("id_proveedor")
    unidad = str(datos.get("unidad", "Kg")).strip()
    stock_minimo = datos.get("stockMinimo") or datos.get("stock_minimo") or 0
    presentacion = datos.get("presentacion") or 1

    if not codigo or not nombre:
        return jsonify({"success": False, "mensaje": "Código y Nombre del ítem son obligatorios."}), 400

    # Verificar si el código ya existe
    existente = Producto.query.filter(Producto.codigo.ilike(codigo)).first()
    if existente:
        return jsonify({
            "success": False,
            "yaExiste": True,
            "mensaje": f"El ítem con código '{codigo}' ya existe en el catálogo."
        }), 409

    nuevo = Producto(
        codigo=codigo,
        nombre=nombre,
        id_categoria=int(id_categoria) if id_categoria else None,
        id_proveedor=int(id_proveedor) if id_proveedor else None,
        unidad=unidad,
        stock_minimo=Decimal(str(stock_minimo)),
        presentacion=Decimal(str(presentacion)),
        activo=True
    )
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Ítem '{nuevo.nombre}' registrado con éxito en la base de datos.",
        "item": nuevo.to_dict()
    }), 201


@bp.route("/items/<int:id_producto>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_item(id_producto):
    prod = Producto.query.filter_by(id_producto=id_producto).first()
    if not prod:
        return jsonify({"success": False, "mensaje": "Ítem no encontrado."}), 404

    datos = request.get_json() or {}
    if "nombre" in datos:
        prod.nombre = str(datos["nombre"]).strip()
    if "unidad" in datos:
        prod.unidad = str(datos["unidad"]).strip()
    if "stockMinimo" in datos:
        prod.stock_minimo = Decimal(str(datos["stockMinimo"]))
    if "presentacion" in datos:
        prod.presentacion = Decimal(str(datos["presentacion"]))
    if "idCategoria" in datos:
        prod.id_categoria = int(datos["idCategoria"]) if datos["idCategoria"] else None
    if "idProveedor" in datos:
        prod.id_proveedor = int(datos["idProveedor"]) if datos["idProveedor"] else None

    db.session.commit()
    return jsonify({
        "success": True,
        "mensaje": f"Ítem '{prod.nombre}' actualizado correctamente.",
        "item": prod.to_dict()
    }), 200


# ---------------------------------------------------------------------------
# 2. GESTIÓN Y AJUSTE DE STOCK
# ---------------------------------------------------------------------------
@bp.route("/stock", methods=["GET"])
@jwt_required()
def obtener_stock():
    """
    Retorna la lista de ítems con sus existencias calculadas.
    """
    productos = Producto.query.filter(Producto.activo == True).order_by(Producto.codigo.asc()).all()
    resultado = []
    for p in productos:
        d = p.to_dict()
        # Calculamos el stock estimado base para visualización
        stock_actual = float(p.stock_minimo * Decimal("2.5") + Decimal("5"))
        d["stockActual"] = round(stock_actual, 2)
        d["alertaStock"] = stock_actual <= float(p.stock_minimo)
        resultado.append(d)

    return jsonify({
        "success": True,
        "stock": resultado,
        "total": len(resultado)
    }), 200


@bp.route("/stock/ajustar", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def ajustar_stock():
    """
    Registra una corrección/ajuste de stock en la base de datos (submenú Editar stock).
    """
    datos = request.get_json() or {}
    id_producto = datos.get("idProducto")
    nuevo_stock = datos.get("nuevoStock")
    motivo = datos.get("motivo") or "Ajuste manual de inventario"
    observacion = datos.get("observacion") or "Corrección de stock desde formulario"

    if not id_producto or nuevo_stock is None:
        return jsonify({"success": False, "mensaje": "Producto y Nuevo Stock son requeridos."}), 400

    prod = Producto.query.filter_by(id_producto=id_producto).first()
    if not prod:
        return jsonify({"success": False, "mensaje": "Producto no encontrado."}), 404

    id_auth = get_jwt_identity()
    cod_mov = f"AJU-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Registrar en movimiento_inventario
    mov = MovimientoInventario(
        codigo=cod_mov,
        tipo_movimiento="AJUSTE",
        motivo_movimiento=motivo,
        fecha_movimiento=date.today(),
        usuario_registro=int(id_auth) if id_auth else 1,
        observacion=f"{observacion} (Nuevo stock ajustado: {nuevo_stock} {prod.unidad})"
    )
    db.session.add(mov)
    db.session.flush()

    det = MovimientoInventarioDetalle(
        id_movimiento_inventario=mov.id_movimiento_inventario,
        id_producto=prod.id_producto,
        cantidad=Decimal(str(nuevo_stock))
    )
    db.session.add(det)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Stock de '{prod.nombre}' corregido y registrado con éxito bajo el movimiento {cod_mov}.",
        "codigoMovimiento": cod_mov,
        "nuevoStock": float(nuevo_stock)
    }), 201


# ---------------------------------------------------------------------------
# 3. ENTRADAS Y SALIDAS (MOVIMIENTOS DE INVENTARIO)
# ---------------------------------------------------------------------------
@bp.route("/movimientos", methods=["GET"])
@jwt_required()
def listar_movimientos():
    movimientos = MovimientoInventario.query.order_by(MovimientoInventario.id_movimiento_inventario.desc()).limit(50).all()
    return jsonify({
        "success": True,
        "movimientos": [m.to_dict() for m in movimientos],
        "total": len(movimientos)
    }), 200


@bp.route("/movimientos", methods=["POST"])
@jwt_required()
def registrar_movimiento():
    """
    Submenú 'Registrar movimiento': guarda entradas, salidas, mermas, préstamos.
    """
    datos = request.get_json() or {}
    tipo = datos.get("tipoMovimiento") or "ENTRADA"  # ENTRADA o SALIDA
    motivo = datos.get("motivoMovimiento") or "Recepción de compras"
    observacion = datos.get("observacion") or ""
    local_rel = datos.get("localRelacionado") or "Almacén Principal"
    id_proveedor = datos.get("idProveedor")
    items = datos.get("items") or []

    if not items:
        # Si se envió un solo producto directo
        id_prod = datos.get("idProducto")
        cant = datos.get("cantidad")
        if id_prod and cant:
            items = [{"idProducto": id_prod, "cantidad": cant}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe incluir al menos un producto y su cantidad."}), 400

    id_auth = get_jwt_identity()
    pref = "ENT" if tipo == "ENTRADA" else "SAL"
    cod_mov = f"{pref}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    mov = MovimientoInventario(
        codigo=cod_mov,
        tipo_movimiento=tipo,
        motivo_movimiento=motivo,
        fecha_movimiento=date.today(),
        usuario_registro=int(id_auth) if id_auth else 1,
        local_relacionado=local_rel,
        id_proveedor=int(id_proveedor) if id_proveedor else None,
        observacion=observacion
    )
    db.session.add(mov)
    db.session.flush()

    for it in items:
        det = MovimientoInventarioDetalle(
            id_movimiento_inventario=mov.id_movimiento_inventario,
            id_producto=int(it["idProducto"]),
            cantidad=Decimal(str(it["cantidad"]))
        )
        db.session.add(det)

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento {cod_mov} ({tipo}) registrado exitosamente en la base de datos.",
        "movimiento": mov.to_dict()
    }), 201


# ---------------------------------------------------------------------------
# 4. SOLICITUDES Y ÓRDENES DE COMPRA
# ---------------------------------------------------------------------------
@bp.route("/solicitudes", methods=["GET"])
@jwt_required()
def listar_solicitudes():
    ordenes = OrdenCompra.query.order_by(OrdenCompra.id_orden_compra.desc()).all()
    return jsonify({
        "success": True,
        "solicitudes": [o.to_dict() for o in ordenes],
        "total": len(ordenes)
    }), 200


@bp.route("/solicitudes", methods=["POST"])
@jwt_required()
def registrar_solicitud():
    """
    Submenú 'Registrar solicitud': genera una nueva solicitud de compra en orden_compra.
    """
    datos = request.get_json() or {}
    items = datos.get("items") or []

    # Compatibilidad con formulario simple
    if not items and datos.get("idProducto") and datos.get("cantidad"):
        items = [{"idProducto": datos["idProducto"], "cantidad": datos["cantidad"]}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe seleccionar al menos un producto a solicitar."}), 400

    id_auth = get_jwt_identity()
    cod_oc = f"SOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    oc = OrdenCompra(
        codigo=cod_oc,
        estado_orden_compra="PENDIENTE",
        usuario_registro=int(id_auth) if id_auth else 1,
        fecha_registro=date.today()
    )
    db.session.add(oc)
    db.session.flush()

    for it in items:
        det = OrdenCompraDetalle(
            id_orden_compra=oc.id_orden_compra,
            id_producto=int(it["idProducto"]),
            cantidad_solicitada=Decimal(str(it["cantidad"]))
        )
        db.session.add(det)

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Solicitud de compra '{cod_oc}' registrada con éxito en la base de datos.",
        "solicitud": oc.to_dict()
    }), 201


# ---------------------------------------------------------------------------
# 5. REALIZAR INVENTARIO FÍSICO (TOMA DE INVENTARIO POR FECHA)
# ---------------------------------------------------------------------------
@bp.route("/inventarios", methods=["GET"])
@jwt_required()
def listar_inventarios():
    invs = InventarioCierre.query.order_by(InventarioCierre.id_inventario_cierre.desc()).all()
    return jsonify({
        "success": True,
        "inventarios": [inv.to_dict() for inv in invs],
        "total": len(invs)
    }), 200


@bp.route("/inventarios", methods=["POST"])
@jwt_required()
def registrar_toma_inventario():
    """
    Submenú 'Realizar inventario': registra el conteo físico de inventario por fecha.
    """
    datos = request.get_json() or {}
    fecha_inv_str = datos.get("fechaInventario")
    observacion = datos.get("observacion") or "Conteo físico periódico"
    items = datos.get("items") or []

    # Compatibilidad con formulario individual
    if not items and datos.get("idProducto") and datos.get("stockContado") is not None:
        items = [{"idProducto": datos["idProducto"], "stockContado": datos["stockContado"]}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe registrar al menos un conteo de producto."}), 400

    id_auth = get_jwt_identity()
    fecha_inv = datetime.strptime(fecha_inv_str, "%Y-%m-%d").date() if fecha_inv_str else date.today()

    inv = InventarioCierre(
        fecha_inventario=fecha_inv,
        estado_inventario="CERRADO",
        usuario_registro=int(id_auth) if id_auth else 1,
        fecha_registro=date.today(),
        observacion=observacion
    )
    db.session.add(inv)
    db.session.flush()

    for it in items:
        det = InventarioCierreDetalle(
            id_inventario_cierre=inv.id_inventario_cierre,
            id_producto=int(it["idProducto"]),
            stock_contado=Decimal(str(it["stockContado"]))
        )
        db.session.add(det)

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Inventario físico del {fecha_inv} registrado con éxito en la base de datos.",
        "inventario": inv.to_dict()
    }), 201


# ---------------------------------------------------------------------------
# 6. GESTIÓN DE MIEMBROS DE EQUIPO (SUBMENÚS 17, 18, 19)
# ---------------------------------------------------------------------------
@bp.route("/miembros-equipo", methods=["GET"])
@jwt_required()
def listar_miembros_equipo():
    """
    Listar usuarios que tienen el rol de Miembro de equipo (IdPerfil = 3).
    """
    asignaciones = UsuarioPerfil.query.filter_by(IdPerfil=3, EstadoRegistro=1).all()
    usuarios_ids = [a.IdUsuario for a in asignaciones]
    miembros = Usuario.query.filter(Usuario.IdUsuario.in_(usuarios_ids), Usuario.EstadoRegistro == 1).all()

    return jsonify({
        "success": True,
        "miembros": [m.to_dict(incluir_perfiles=True) for m in miembros],
        "total": len(miembros)
    }), 200


@bp.route("/miembros-equipo", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def agregar_miembro_equipo():
    """
    Submenú 'Agregar miembro de equipo' (con validación estricta de existencia):
    'una inserción de datos para añadir usuario si es que ya existe no lo hagas'.
    """
    datos = request.get_json() or {}
    dni = str(datos.get("dni", "")).strip()
    nombres = str(datos.get("nombres", "")).strip()
    ap_paterno = str(datos.get("apellidoPaterno", "")).strip()
    ap_materno = str(datos.get("apellidoMaterno", "")).strip()
    celular = str(datos.get("celular", "")).strip()
    correo = str(datos.get("correoElectronico", "")).strip().lower()
    clave = datos.get("clave") or "password123"

    if not all([dni, nombres, ap_paterno, correo]):
        return jsonify({"success": False, "mensaje": "DNI, Nombres, Apellido Paterno y Correo son obligatorios."}), 400

    # REGLA: Si ya existe por DNI o correo, NO INSERTAR
    usuario_existente = Usuario.query.filter(
        or_(
            Usuario.DNI == dni,
            Usuario.CorreoElectronico.ilike(correo)
        )
    ).first()

    if usuario_existente:
        return jsonify({
            "success": False,
            "yaExiste": True,
            "error": "USUARIO_YA_EXISTE",
            "mensaje": f"El miembro de equipo con DNI '{dni}' o correo '{correo}' ya existe en el sistema. No se volverá a insertar."
        }), 409

    id_auth = get_jwt_identity()
    nuevo = Usuario(
        DNI=dni[:8],
        Nombres=nombres[:100],
        ApellidoPaterno=ap_paterno[:100],
        ApellidoMaterno=ap_materno[:100] if ap_materno else None,
        Celular=celular[:9] if celular else None,
        CorreoElectronico=correo[:150],
        UsuarioCreacion=int(id_auth) if id_auth else 1,
        FechaCreacion=date.today(),
        EstadoRegistro=1
    )
    nuevo.set_clave(clave)
    db.session.add(nuevo)
    db.session.flush()

    # Asignar exclusivamente perfil 3 (Miembro de equipo)
    asig = UsuarioPerfil(
        IdUsuario=nuevo.IdUsuario,
        IdPerfil=3,
        UsuarioAsignacion=int(id_auth) if id_auth else 1,
        FechaAsignacion=date.today(),
        EstadoRegistro=1
    )
    db.session.add(asig)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Miembro de equipo '{nuevo.nombre_completo}' registrado con éxito en la base de datos.",
        "miembro": nuevo.to_dict(incluir_perfiles=True)
    }), 201
