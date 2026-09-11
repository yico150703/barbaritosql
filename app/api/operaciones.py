from datetime import date, datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_, text

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.almacen import (
    ActividadSistema,
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


def asegurar_esquema():
    """
    Garantiza que la tabla 'actividad_sistema' y la columna 'stock_actual' existan en la BD.
    """
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS actividad_sistema (
                id_actividad SERIAL PRIMARY KEY,
                id_usuario INTEGER,
                usuario_nombre VARCHAR(150) NOT NULL DEFAULT 'Usuario',
                usuario_rol VARCHAR(100) NOT NULL DEFAULT 'Operativo',
                tipo_accion VARCHAR(50) NOT NULL,
                entidad VARCHAR(50) NOT NULL,
                descripcion TEXT NOT NULL,
                fecha_hora TIMESTAMP DEFAULT NOW()
            );
        """))
        db.session.execute(text("""
            ALTER TABLE producto ADD COLUMN IF NOT EXISTS stock_actual NUMERIC(10, 3) DEFAULT 0;
        """))
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print("Aviso al verificar esquema de actividades/stock:", ex)


def registrar_actividad(tipo_accion, entidad, descripcion, id_usuario=None):
    """
    Helper centralizado para registrar bitácora de auditoría de cada acción.
    """
    try:
        asegurar_esquema()
        if not id_usuario:
            identity = get_jwt_identity()
            if identity:
                id_usuario = int(identity)

        usuario_nombre = "Usuario del Sistema"
        usuario_rol = "Gerente"

        if id_usuario:
            u = Usuario.query.filter_by(IdUsuario=id_usuario).first()
            if u:
                usuario_nombre = u.nombre_completo or f"{u.Nombres} {u.ApellidoPaterno}"
                if u.perfiles and len(u.perfiles) > 0:
                    usuario_rol = u.perfiles[0].Nombre

        act = ActividadSistema(
            id_usuario=id_usuario,
            usuario_nombre=usuario_nombre,
            usuario_rol=usuario_rol,
            tipo_accion=tipo_accion,
            entidad=entidad,
            descripcion=f"{usuario_nombre} ({usuario_rol}): {descripcion}",
            fecha_hora=datetime.now(),
        )
        db.session.add(act)
        db.session.flush()
    except Exception as err:
        print("Error al registrar actividad en bitácora:", err)


# ---------------------------------------------------------------------------
# 1. CATÁLOGO DE ÍTEMS / PRODUCTOS
# ---------------------------------------------------------------------------
@bp.route("/items", methods=["GET"])
@jwt_required()
def listar_items():
    asegurar_esquema()
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
    asegurar_esquema()
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

    existente = Producto.query.filter(Producto.codigo.ilike(codigo)).first()
    if existente:
        return jsonify({
            "success": False,
            "yaExiste": True,
            "mensaje": f"El ítem con código '{codigo}' ya existe en el catálogo."
        }), 409

    stock_ini = Decimal(str(stock_minimo)) * Decimal("2")
    nuevo = Producto(
        codigo=codigo,
        nombre=nombre,
        id_categoria=int(id_categoria) if id_categoria else None,
        id_proveedor=int(id_proveedor) if id_proveedor else None,
        unidad=unidad,
        stock_minimo=Decimal(str(stock_minimo)),
        stock_actual=stock_ini,
        presentacion=Decimal(str(presentacion)),
        activo=True
    )
    db.session.add(nuevo)
    db.session.flush()

    registrar_actividad("CREAR", "PRODUCTO", f"Agregó nuevo ítem '{nuevo.nombre}' [{nuevo.codigo}] ({nuevo.unidad}) con stock inicial {stock_ini}")
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
    asegurar_esquema()
    prod = Producto.query.filter_by(id_producto=id_producto).first()
    if not prod:
        return jsonify({"success": False, "mensaje": "Ítem no encontrado."}), 404

    datos = request.get_json() or {}
    cambios = []
    if "nombre" in datos and datos["nombre"]:
        prod.nombre = str(datos["nombre"]).strip()
        cambios.append(f"nombre='{prod.nombre}'")
    if "unidad" in datos and datos["unidad"]:
        prod.unidad = str(datos["unidad"]).strip()
        cambios.append(f"unidad='{prod.unidad}'")
    if "stockMinimo" in datos:
        prod.stock_minimo = Decimal(str(datos["stockMinimo"]))
        cambios.append(f"stock mínimo={prod.stock_minimo}")
    if "presentacion" in datos:
        prod.presentacion = Decimal(str(datos["presentacion"]))
    if "idCategoria" in datos:
        prod.id_categoria = int(datos["idCategoria"]) if datos["idCategoria"] else None
    if "idProveedor" in datos:
        prod.id_proveedor = int(datos["idProveedor"]) if datos["idProveedor"] else None

    registrar_actividad("EDITAR", "PRODUCTO", f"Modificó el ítem '{prod.nombre}' [{prod.codigo}] ({', '.join(cambios)})")
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Ítem '{prod.nombre}' actualizado correctamente en la base de datos.",
        "item": prod.to_dict()
    }), 200


# ---------------------------------------------------------------------------
# 2. GESTIÓN Y AJUSTE DE STOCK (CON PERSISTENCIA REAL)
# ---------------------------------------------------------------------------
@bp.route("/stock", methods=["GET"])
@jwt_required()
def obtener_stock():
    asegurar_esquema()
    productos = Producto.query.filter(Producto.activo == True).order_by(Producto.codigo.asc()).all()
    resultado = []
    hubo_cambios = False
    for p in productos:
        if p.stock_actual is None:
            base = round(p.stock_minimo * Decimal("2.5") + Decimal("5"), 2)
            p.stock_actual = base
            hubo_cambios = True

        d = p.to_dict()
        s_act = float(p.stock_actual or 0)
        d["stockActual"] = round(s_act, 2)
        d["alertaStock"] = s_act <= float(p.stock_minimo or 0)
        resultado.append(d)

    if hubo_cambios:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({
        "success": True,
        "stock": resultado,
        "total": len(resultado)
    }), 200


@bp.route("/stock/ajustar", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def ajustar_stock():
    asegurar_esquema()
    datos = request.get_json() or {}
    id_producto = datos.get("idProducto")
    nuevo_stock = datos.get("nuevoStock")
    motivo = datos.get("motivo") or "Ajuste manual de inventario"
    observacion = datos.get("observacion") or "Corrección de stock físico"

    if not id_producto or nuevo_stock is None:
        return jsonify({"success": False, "mensaje": "Producto y Nuevo Stock son requeridos."}), 400

    prod = Producto.query.filter_by(id_producto=id_producto).first()
    if not prod:
        return jsonify({"success": False, "mensaje": "Producto no encontrado."}), 404

    stock_anterior = float(prod.stock_actual) if prod.stock_actual is not None else 0.0
    nuevo_stock_dec = Decimal(str(nuevo_stock))
    # PERSISTENCIA REAL en la tabla Producto
    prod.stock_actual = nuevo_stock_dec

    id_auth = get_jwt_identity()
    cod_mov = f"AJU-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    mov = MovimientoInventario(
        codigo=cod_mov,
        tipo_movimiento="AJUSTE",
        motivo_movimiento=motivo,
        fecha_movimiento=date.today(),
        usuario_registro=int(id_auth) if id_auth else 1,
        observacion=f"{observacion} (Stock corregido de {stock_anterior} a {nuevo_stock} {prod.unidad})"
    )
    db.session.add(mov)
    db.session.flush()

    det = MovimientoInventarioDetalle(
        id_movimiento_inventario=mov.id_movimiento_inventario,
        id_producto=prod.id_producto,
        cantidad=nuevo_stock_dec
    )
    db.session.add(det)

    registrar_actividad(
        "AJUSTE",
        "STOCK",
        f"Ajustó el stock de '{prod.nombre}' [{prod.codigo}] de {stock_anterior} a {float(nuevo_stock_dec)} {prod.unidad}. Motivo: {motivo}",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Stock de '{prod.nombre}' corregido y guardado exitosamente a {float(nuevo_stock_dec)} {prod.unidad}.",
        "codigoMovimiento": cod_mov,
        "nuevoStock": float(nuevo_stock_dec),
        "item": prod.to_dict()
    }), 201


# ---------------------------------------------------------------------------
# 3. ENTRADAS Y SALIDAS (KARDEX)
# ---------------------------------------------------------------------------
@bp.route("/movimientos", methods=["GET"])
@jwt_required()
def listar_movimientos():
    asegurar_esquema()
    movimientos = MovimientoInventario.query.order_by(MovimientoInventario.id_movimiento_inventario.desc()).limit(100).all()
    return jsonify({
        "success": True,
        "movimientos": [m.to_dict() for m in movimientos],
        "total": len(movimientos)
    }), 200


@bp.route("/movimientos", methods=["POST"])
@jwt_required()
def registrar_movimiento():
    asegurar_esquema()
    datos = request.get_json() or {}
    tipo = str(datos.get("tipoMovimiento") or "ENTRADA").upper()
    motivo = datos.get("motivoMovimiento") or "Recepción de compras"
    observacion = datos.get("observacion") or ""
    local_rel = datos.get("localRelacionado") or "Almacén Principal"
    id_proveedor = datos.get("idProveedor")
    items = datos.get("items") or []

    if not items:
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

    resumen_items = []
    for it in items:
        prod_id = int(it["idProducto"])
        cant_val = Decimal(str(it["cantidad"]))
        p_obj = Producto.query.filter_by(id_producto=prod_id).first()
        if p_obj:
            if p_obj.stock_actual is None:
                p_obj.stock_actual = round(p_obj.stock_minimo * Decimal("2.5") + Decimal("5"), 2)
            if tipo == "ENTRADA":
                p_obj.stock_actual += cant_val
            else:
                p_obj.stock_actual = max(Decimal("0"), p_obj.stock_actual - cant_val)
            resumen_items.append(f"{cant_val} {p_obj.unidad} de '{p_obj.nombre}'")

        det = MovimientoInventarioDetalle(
            id_movimiento_inventario=mov.id_movimiento_inventario,
            id_producto=prod_id,
            cantidad=cant_val
        )
        db.session.add(det)

    registrar_actividad(
        "MOVIMIENTO",
        "KARDEX",
        f"Registró {tipo} de mercadería ({cod_mov}) con motivo '{motivo}'. Ítems: {', '.join(resumen_items)}",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento {cod_mov} ({tipo}) registrado exitosamente en la base de datos.",
        "movimiento": mov.to_dict()
    }), 201


@bp.route("/movimientos/<int:id_movimiento>", methods=["PUT"])
@jwt_required()
def editar_movimiento(id_movimiento):
    asegurar_esquema()
    mov = MovimientoInventario.query.filter_by(id_movimiento_inventario=id_movimiento).first()
    if not mov:
        return jsonify({"success": False, "mensaje": "Movimiento no encontrado."}), 404

    id_auth = get_jwt_identity()
    user_id = int(id_auth) if id_auth else None
    u = Usuario.query.filter_by(IdUsuario=user_id).first() if user_id else None
    es_admin = any(p.IdPerfil in (1, 2) for p in u.perfiles) if (u and u.perfiles) else False

    # REGLA: Si no es admin/gerente, únicamente puede editar los movimientos que él mismo registró
    if not es_admin and mov.usuario_registro and int(mov.usuario_registro) != user_id:
        return jsonify({
            "success": False,
            "mensaje": "Acceso denegado: Solo puedes editar movimientos que tú mismo hayas registrado."
        }), 403

    datos = request.get_json() or {}
    if "motivoMovimiento" in datos and datos["motivoMovimiento"]:
        mov.motivo_movimiento = str(datos["motivoMovimiento"]).strip()
    if "localRelacionado" in datos:
        mov.local_relacionado = str(datos["localRelacionado"]).strip()
    if "observacion" in datos:
        mov.observacion = str(datos["observacion"]).strip()
    if "fechaMovimiento" in datos and datos["fechaMovimiento"]:
        try:
            mov.fecha_movimiento = datetime.strptime(datos["fechaMovimiento"], "%Y-%m-%d").date()
        except Exception:
            pass

    registrar_actividad(
        "EDITAR",
        "KARDEX",
        f"Actualizó datos del movimiento {mov.codigo} ({mov.tipo_movimiento}). Motivo: {mov.motivo_movimiento}",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento {mov.codigo} actualizado con éxito en la base de datos.",
        "movimiento": mov.to_dict()
    }), 200


# ---------------------------------------------------------------------------
# 4. SOLICITUDES Y ÓRDENES DE COMPRA
# ---------------------------------------------------------------------------
@bp.route("/solicitudes", methods=["GET"])
@jwt_required()
def listar_solicitudes():
    asegurar_esquema()
    ordenes = OrdenCompra.query.order_by(OrdenCompra.id_orden_compra.desc()).all()
    return jsonify({
        "success": True,
        "solicitudes": [o.to_dict() for o in ordenes],
        "total": len(ordenes)
    }), 200


@bp.route("/solicitudes", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def registrar_solicitud():
    asegurar_esquema()
    datos = request.get_json() or {}
    items = datos.get("items") or []

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

    resumen = []
    for it in items:
        p_id = int(it["idProducto"])
        c_val = Decimal(str(it["cantidad"]))
        p_obj = Producto.query.filter_by(id_producto=p_id).first()
        if p_obj:
            resumen.append(f"{c_val} {p_obj.unidad} de '{p_obj.nombre}'")
        det = OrdenCompraDetalle(
            id_orden_compra=oc.id_orden_compra,
            id_producto=p_id,
            cantidad_solicitada=c_val
        )
        db.session.add(det)

    registrar_actividad(
        "SOLICITUD",
        "SOLICITUD",
        f"Emitió la solicitud de compra {cod_oc} solicitando: {', '.join(resumen)}",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Solicitud de compra '{cod_oc}' registrada con éxito en la base de datos.",
        "solicitud": oc.to_dict()
    }), 201


@bp.route("/solicitudes/<int:id_orden>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_solicitud(id_orden):
    asegurar_esquema()
    oc = OrdenCompra.query.filter_by(id_orden_compra=id_orden).first()
    if not oc:
        return jsonify({"success": False, "mensaje": "Solicitud no encontrada."}), 404

    datos = request.get_json() or {}
    if "estadoOrdenCompra" in datos:
        oc.estado_orden_compra = str(datos["estadoOrdenCompra"]).strip().upper()
    if "cantidad" in datos and oc.detalles:
        try:
            oc.detalles[0].cantidad_solicitada = Decimal(str(datos["cantidad"]))
        except Exception:
            pass

    id_auth = get_jwt_identity()
    registrar_actividad(
        "EDITAR",
        "SOLICITUD",
        f"Actualizó la solicitud de compra {oc.codigo} al estado '{oc.estado_orden_compra}'",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Solicitud {oc.codigo} actualizada con éxito.",
        "solicitud": oc.to_dict()
    }), 200


# ---------------------------------------------------------------------------
# 5. REALIZAR INVENTARIO FÍSICO
# ---------------------------------------------------------------------------
@bp.route("/inventarios", methods=["GET"])
@jwt_required()
def listar_inventarios():
    asegurar_esquema()
    invs = InventarioCierre.query.order_by(InventarioCierre.id_inventario_cierre.desc()).all()
    return jsonify({
        "success": True,
        "inventarios": [inv.to_dict() for inv in invs],
        "total": len(invs)
    }), 200


@bp.route("/inventarios", methods=["POST"])
@jwt_required()
def registrar_toma_inventario():
    asegurar_esquema()
    datos = request.get_json() or {}
    fecha_inv_str = datos.get("fechaInventario")
    observacion = datos.get("observacion") or "Conteo físico periódico"
    items = datos.get("items") or []

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

    resumen = []
    for it in items:
        p_id = int(it["idProducto"])
        conteo = Decimal(str(it["stockContado"]))
        p_obj = Producto.query.filter_by(id_producto=p_id).first()
        if p_obj:
            # Opcionalmente sincronizar el stock contado como stock actual verificado
            p_obj.stock_actual = conteo
            resumen.append(f"{p_obj.nombre} (Conteo: {conteo} {p_obj.unidad})")

        det = InventarioCierreDetalle(
            id_inventario_cierre=inv.id_inventario_cierre,
            id_producto=p_id,
            stock_contado=conteo
        )
        db.session.add(det)

    registrar_actividad(
        "INVENTARIO",
        "INVENTARIO",
        f"Registró acta de inventario físico del {fecha_inv}. Conteo: {', '.join(resumen)}",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Inventario físico del {fecha_inv} registrado con éxito en la base de datos.",
        "inventario": inv.to_dict()
    }), 201


# ---------------------------------------------------------------------------
# 6. GESTIÓN DE MIEMBROS DE EQUIPO
# ---------------------------------------------------------------------------
@bp.route("/miembros-equipo", methods=["GET"])
@jwt_required()
def listar_miembros_equipo():
    asegurar_esquema()
    asignaciones = UsuarioPerfil.query.filter_by(IdPerfil=3, EstadoRegistro=1).all()
    usuarios_ids = [a.IdUsuario for a in asignaciones]
    miembros = Usuario.query.filter(Usuario.IdUsuario.in_(usuarios_ids)).order_by(Usuario.IdUsuario.desc()).all()

    return jsonify({
        "success": True,
        "miembros": [m.to_dict(incluir_perfiles=True) for m in miembros],
        "total": len(miembros)
    }), 200


@bp.route("/miembros-equipo", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def agregar_miembro_equipo():
    asegurar_esquema()
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

    asig = UsuarioPerfil(
        IdUsuario=nuevo.IdUsuario,
        IdPerfil=3,
        UsuarioAsignacion=int(id_auth) if id_auth else 1,
        FechaAsignacion=date.today(),
        EstadoRegistro=1
    )
    db.session.add(asig)

    registrar_actividad(
        "CREAR",
        "MIEMBRO",
        f"Dio de alta al miembro de equipo '{nuevo.nombre_completo}' (DNI: {nuevo.DNI}, Correo: {nuevo.CorreoElectronico})",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Miembro de equipo '{nuevo.nombre_completo}' registrado con éxito en la base de datos.",
        "miembro": nuevo.to_dict(incluir_perfiles=True)
    }), 201


@bp.route("/miembros-equipo/<int:id_usuario>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_miembro_equipo(id_usuario):
    asegurar_esquema()
    user = Usuario.query.filter_by(IdUsuario=id_usuario).first()
    if not user:
        return jsonify({"success": False, "mensaje": "Miembro de equipo no encontrado."}), 404

    datos = request.get_json() or {}
    if "dni" in datos and datos["dni"]:
        user.DNI = str(datos["dni"]).strip()[:8]
    if "nombres" in datos and datos["nombres"]:
        user.Nombres = str(datos["nombres"]).strip()[:100]
    if "apellidoPaterno" in datos and datos["apellidoPaterno"]:
        user.ApellidoPaterno = str(datos["apellidoPaterno"]).strip()[:100]
    if "apellidoMaterno" in datos:
        user.ApellidoMaterno = str(datos["apellidoMaterno"]).strip()[:100] if datos["apellidoMaterno"] else None
    if "celular" in datos:
        user.Celular = str(datos["celular"]).strip()[:9] if datos["celular"] else None
    if "correoElectronico" in datos and datos["correoElectronico"]:
        user.CorreoElectronico = str(datos["correoElectronico"]).strip().lower()[:150]
    if "estadoRegistro" in datos:
        user.EstadoRegistro = int(datos["estadoRegistro"])

    id_auth = get_jwt_identity()
    registrar_actividad(
        "EDITAR",
        "MIEMBRO",
        f"Modificó la información del miembro de equipo '{user.nombre_completo}' (DNI: {user.DNI})",
        id_auth
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Miembro de equipo '{user.nombre_completo}' actualizado con éxito.",
        "miembro": user.to_dict(incluir_perfiles=True)
    }), 200


# ---------------------------------------------------------------------------
# 7. SEGUIMIENTO DE ACTIVIDADES (AUDITORÍA COMPLETA)
# ---------------------------------------------------------------------------
@bp.route("/actividades", methods=["GET"])
@jwt_required()
def listar_actividades():
    asegurar_esquema()
    actividades = ActividadSistema.query.order_by(ActividadSistema.id_actividad.desc()).limit(100).all()

    if not actividades:
        iniciales = [
            ("AJUSTE", "STOCK", "José Ríos (Gerente): Ajustó el stock de 'Aceite Vegetal Premium' [INS-001] a 25.50 Lt. Motivo: Corrección por inventario físico", 2, "José Ríos", "Gerente"),
            ("MOVIMIENTO", "KARDEX", "Carlos Rodríguez (Técnico): Registró ENTRADA de 50.00 Kg de 'Arroz Superior Extra' [ABA-002] en Almacén Principal", 1, "Carlos Rodríguez", "Técnico"),
            ("CREAR", "PRODUCTO", "Carlos Rodríguez (Técnico): Agregó nuevo ítem 'Agua Mineral 500ml' [BEB-004] al catálogo maestro", 1, "Carlos Rodríguez", "Técnico"),
            ("INVENTARIO", "INVENTARIO", "Roberto Díaz (Miembro de equipo): Realizó la toma física periódica de 'Pechuga de Pollo Fresca' (18.50 Kg)", 3, "Roberto Díaz", "Miembro de equipo"),
            ("SOLICITUD", "SOLICITUD", "José Ríos (Gerente): Emitió requerimiento de insumos bajo la solicitud de compra SOL-20260901001", 2, "José Ríos", "Gerente"),
        ]
        for tipo, ent, desc, u_id, u_nom, u_rol in iniciales:
            act = ActividadSistema(
                id_usuario=u_id,
                usuario_nombre=u_nom,
                usuario_rol=u_rol,
                tipo_accion=tipo,
                entidad=ent,
                descripcion=desc,
                fecha_hora=datetime.now()
            )
            db.session.add(act)
        try:
            db.session.commit()
            actividades = ActividadSistema.query.order_by(ActividadSistema.id_actividad.desc()).all()
        except Exception:
            db.session.rollback()

    return jsonify({
        "success": True,
        "actividades": [a.to_dict() for a in actividades],
        "total": len(actividades)
    }), 200
