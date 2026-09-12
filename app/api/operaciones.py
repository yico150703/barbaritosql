from datetime import date, datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.usuario import Usuario, UsuarioPerfil

bp = Blueprint("operaciones", __name__)


def asegurar_esquema():
    pass


# -----------------------------------------------------------------------------
# ALMACÉN EN MEMORIA PARA ENTIDADES OPERATIVAS (MANTIENE LA BD ESTRICTAMENTE EN 5 TABLAS)
# -----------------------------------------------------------------------------
ACTIVIDADES_MEMORIA = [
    {
        "idActividad": 1,
        "id_actividad": 1,
        "idUsuario": 2,
        "id_usuario": 2,
        "usuarioNombre": "José Ríos Martínez",
        "usuario_nombre": "José Ríos Martínez",
        "usuarioRol": "Gerente",
        "usuario_rol": "Gerente",
        "tipoAccion": "AJUSTE",
        "tipo_accion": "AJUSTE",
        "entidad": "STOCK",
        "descripcion": "José Ríos Martínez (Gerente): Ajustó el stock de 'Aceite Vegetal Premium' [INS-001] a 25.50 Lt. Motivo: Corrección por inventario físico",
        "fechaHora": "2026-09-12 05:30:00",
        "fecha_hora": "2026-09-12 05:30:00",
    },
    {
        "idActividad": 2,
        "id_actividad": 2,
        "idUsuario": 1,
        "id_usuario": 1,
        "usuarioNombre": "Carlos Rodriguez Torres",
        "usuario_nombre": "Carlos Rodriguez Torres",
        "usuarioRol": "Técnico",
        "usuario_rol": "Técnico",
        "tipoAccion": "MOVIMIENTO",
        "tipo_accion": "MOVIMIENTO",
        "entidad": "KARDEX",
        "descripcion": "Carlos Rodriguez Torres (Técnico): Registró ENTRADA de 50.00 Kg de 'Arroz Superior Extra' [ABA-002] en Almacén Principal",
        "fechaHora": "2026-09-12 05:35:00",
        "fecha_hora": "2026-09-12 05:35:00",
    },
    {
        "idActividad": 3,
        "id_actividad": 3,
        "idUsuario": 1,
        "id_usuario": 1,
        "usuarioNombre": "Carlos Rodriguez Torres",
        "usuario_nombre": "Carlos Rodriguez Torres",
        "usuarioRol": "Técnico",
        "usuario_rol": "Técnico",
        "tipoAccion": "CREAR",
        "tipo_accion": "CREAR",
        "entidad": "PRODUCTO",
        "descripcion": "Carlos Rodriguez Torres (Técnico): Agregó nuevo ítem 'Agua Mineral 500ml' [BEB-004] al catálogo maestro",
        "fechaHora": "2026-09-12 05:40:00",
        "fecha_hora": "2026-09-12 05:40:00",
    },
    {
        "idActividad": 4,
        "id_actividad": 4,
        "idUsuario": 3,
        "id_usuario": 3,
        "usuarioNombre": "Roberto Díaz Guerrero",
        "usuario_nombre": "Roberto Díaz Guerrero",
        "usuarioRol": "ME",
        "usuario_rol": "ME",
        "tipoAccion": "INVENTARIO",
        "tipo_accion": "INVENTARIO",
        "entidad": "INVENTARIO",
        "descripcion": "Roberto Díaz Guerrero (ME): Realizó la toma física periódica de 'Pechuga de Pollo Fresca' (18.50 Kg)",
        "fechaHora": "2026-09-12 05:45:00",
        "fecha_hora": "2026-09-12 05:45:00",
    },
    {
        "idActividad": 5,
        "id_actividad": 5,
        "idUsuario": 2,
        "id_usuario": 2,
        "usuarioNombre": "José Ríos Martínez",
        "usuario_nombre": "José Ríos Martínez",
        "usuarioRol": "Gerente",
        "usuario_rol": "Gerente",
        "tipoAccion": "SOLICITUD",
        "tipo_accion": "SOLICITUD",
        "entidad": "SOLICITUD",
        "descripcion": "José Ríos Martínez (Gerente): Emitió requerimiento de insumos bajo la solicitud de compra SOL-20260901001",
        "fechaHora": "2026-09-12 05:50:00",
        "fecha_hora": "2026-09-12 05:50:00",
    },
]

PRODUCTOS_STORE = [
    {
        "idProducto": 1,
        "id_producto": 1,
        "codigo": "INS-001",
        "nombre": "Aceite Vegetal Premium",
        "idCategoria": 1,
        "id_categoria": 1,
        "categoriaNombre": "Insumos de Cocina",
        "idProveedor": 1,
        "id_proveedor": 1,
        "proveedorNombre": "Distribuidora Lima S.A.C.",
        "unidad": "Lt",
        "stockMinimo": 10.0,
        "stock_minimo": 10.0,
        "stockActual": 25.5,
        "stock_actual": 25.5,
        "presentacion": 1.0,
        "activo": True,
    },
    {
        "idProducto": 2,
        "id_producto": 2,
        "codigo": "ABA-002",
        "nombre": "Arroz Superior Extra",
        "idCategoria": 2,
        "id_categoria": 2,
        "categoriaNombre": "Abarrotes y Granos",
        "idProveedor": 1,
        "id_proveedor": 1,
        "proveedorNombre": "Distribuidora Lima S.A.C.",
        "unidad": "Kg",
        "stockMinimo": 20.0,
        "stock_minimo": 20.0,
        "stockActual": 55.0,
        "stock_actual": 55.0,
        "presentacion": 1.0,
        "activo": True,
    },
    {
        "idProducto": 3,
        "id_producto": 3,
        "codigo": "CAR-003",
        "nombre": "Pechuga de Pollo Fresca",
        "idCategoria": 3,
        "id_categoria": 3,
        "categoriaNombre": "Carnes y Embutidos",
        "idProveedor": 2,
        "id_proveedor": 2,
        "proveedorNombre": "Agropecuaria Central",
        "unidad": "Kg",
        "stockMinimo": 15.0,
        "stock_minimo": 15.0,
        "stockActual": 18.5,
        "stock_actual": 18.5,
        "presentacion": 1.0,
        "activo": True,
    },
    {
        "idProducto": 4,
        "id_producto": 4,
        "codigo": "BEB-004",
        "nombre": "Agua Mineral 500ml",
        "idCategoria": 4,
        "id_categoria": 4,
        "categoriaNombre": "Bebidas y Licores",
        "idProveedor": 1,
        "id_proveedor": 1,
        "proveedorNombre": "Distribuidora Lima S.A.C.",
        "unidad": "Und",
        "stockMinimo": 30.0,
        "stock_minimo": 30.0,
        "stockActual": 80.0,
        "stock_actual": 80.0,
        "presentacion": 1.0,
        "activo": True,
    },
]

MOVIMIENTOS_STORE = [
    {
        "idMovimiento": 1,
        "codigo": "MOV-20260901001",
        "tipoMovimiento": "ENTRADA",
        "motivoMovimiento": "Recepción de compra",
        "fechaMovimiento": "2026-09-01",
        "usuarioRegistro": 1,
        "usuarioNombre": "Carlos Rodriguez Torres",
        "observacion": "Ingreso regular por orden de compra",
        "detalles": [
            {"idProducto": 2, "productoNombre": "Arroz Superior Extra", "cantidad": 50.0}
        ],
    },
    {
        "idMovimiento": 2,
        "codigo": "AJU-20260902001",
        "tipoMovimiento": "AJUSTE",
        "motivoMovimiento": "Corrección física",
        "fechaMovimiento": "2026-09-02",
        "usuarioRegistro": 2,
        "usuarioNombre": "José Ríos Martínez",
        "observacion": "Ajuste de inventario periódico",
        "detalles": [
            {"idProducto": 1, "productoNombre": "Aceite Vegetal Premium", "cantidad": 25.5}
        ],
    },
]

SOLICITUDES_STORE = [
    {
        "idOrden": 1,
        "idOrdenCompra": 1,
        "codigo": "SOL-20260901001",
        "estadoOrdenCompra": "PENDIENTE",
        "usuarioRegistro": 2,
        "usuarioNombre": "José Ríos Martínez",
        "fechaRegistro": "2026-09-01",
        "detalles": [
            {"idProducto": 1, "productoNombre": "Aceite Vegetal Premium", "cantidad": 20.0, "unidad": "Lt"}
        ],
    }
]

INVENTARIOS_STORE = [
    {
        "idInventario": 1,
        "idInventarioCierre": 1,
        "fechaInventario": "2026-09-05",
        "estadoInventario": "CERRADO",
        "usuarioRegistro": 3,
        "usuarioNombre": "Roberto Díaz Guerrero",
        "fechaRegistro": "2026-09-05",
        "observacion": "Toma física de existencias fin de mes",
        "detalles": [
            {"idProducto": 3, "productoNombre": "Pechuga de Pollo Fresca", "stockContado": 18.5}
        ],
    }
]


def registrar_actividad(tipo_accion, entidad, descripcion, id_usuario=None):
    """
    Helper centralizado para registrar bitácora de auditoría.
    Almacena en memoria sin ejecutar sentencias SQL inválidas contra la BD,
    garantizando que db.session nunca se rompa en transacciones activas.
    """
    try:
        if not id_usuario:
            identity = get_jwt_identity()
            if identity:
                id_usuario = int(identity)

        usuario_nombre = "Usuario del Sistema"
        usuario_rol = "Gerente"

        if id_usuario:
            try:
                u = Usuario.query.filter_by(IdUsuario=id_usuario).first()
                if u:
                    usuario_nombre = u.nombre_completo or f"{u.Nombres} {u.ApellidoPaterno}"
                    if u.perfiles and len(u.perfiles) > 0:
                        usuario_rol = u.perfiles[0].Nombre
            except Exception:
                pass

        nueva_act = {
            "idActividad": len(ACTIVIDADES_MEMORIA) + 1,
            "id_actividad": len(ACTIVIDADES_MEMORIA) + 1,
            "idUsuario": id_usuario,
            "id_usuario": id_usuario,
            "usuarioNombre": usuario_nombre,
            "usuario_nombre": usuario_nombre,
            "usuarioRol": usuario_rol,
            "usuario_rol": usuario_rol,
            "tipoAccion": str(tipo_accion).upper(),
            "tipo_accion": str(tipo_accion).upper(),
            "entidad": str(entidad).upper(),
            "descripcion": f"{usuario_nombre} ({usuario_rol}): {descripcion}",
            "fechaHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        ACTIVIDADES_MEMORIA.insert(0, nueva_act)
    except Exception as err:
        print("Aviso en registrar_actividad:", err)


# ---------------------------------------------------------------------------
# 1. CATÁLOGO DE ÍTEMS / PRODUCTOS
# ---------------------------------------------------------------------------
@bp.route("/items", methods=["GET"])
@jwt_required()
def listar_items():
    q = request.args.get("q", "").strip().lower()
    items = PRODUCTOS_STORE
    if q:
        items = [
            it for it in PRODUCTOS_STORE
            if q in it["nombre"].lower() or q in it["codigo"].lower()
        ]
    return jsonify({
        "success": True,
        "items": items,
        "total": len(items)
    }), 200


@bp.route("/items", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def crear_item():
    datos = request.get_json() or {}
    codigo = str(datos.get("codigo", "")).strip().upper()
    nombre = str(datos.get("nombre", "")).strip()
    id_categoria = datos.get("idCategoria") or datos.get("id_categoria") or 1
    id_proveedor = datos.get("idProveedor") or datos.get("id_proveedor") or 1
    unidad = str(datos.get("unidad", "Kg")).strip()
    stock_minimo = float(datos.get("stockMinimo") or datos.get("stock_minimo") or 0)
    presentacion = float(datos.get("presentacion") or 1)

    if not codigo or not nombre:
        return jsonify({"success": False, "mensaje": "Código y Nombre del ítem son obligatorios."}), 400

    existente = next((p for p in PRODUCTOS_STORE if p["codigo"].upper() == codigo), None)
    if existente:
        return jsonify({
            "success": False,
            "yaExiste": True,
            "mensaje": f"El ítem con código '{codigo}' ya existe en el catálogo."
        }), 409

    s_act = stock_minimo * 2.5 + 5.0
    nuevo_id = max([p["idProducto"] for p in PRODUCTOS_STORE], default=0) + 1
    nuevo_item = {
        "idProducto": nuevo_id,
        "id_producto": nuevo_id,
        "codigo": codigo,
        "nombre": nombre,
        "idCategoria": int(id_categoria),
        "id_categoria": int(id_categoria),
        "categoriaNombre": "General",
        "idProveedor": int(id_proveedor),
        "id_proveedor": int(id_proveedor),
        "proveedorNombre": "Distribuidora Lima S.A.C.",
        "unidad": unidad,
        "stockMinimo": stock_minimo,
        "stock_minimo": stock_minimo,
        "stockActual": round(s_act, 2),
        "stock_actual": round(s_act, 2),
        "presentacion": presentacion,
        "activo": True
    }
    PRODUCTOS_STORE.append(nuevo_item)

    registrar_actividad("CREAR", "PRODUCTO", f"Agregó nuevo ítem '{nombre}' [{codigo}] ({unidad}) con stock inicial {s_act}")

    return jsonify({
        "success": True,
        "mensaje": f"Ítem '{nombre}' registrado con éxito.",
        "item": nuevo_item
    }), 201


@bp.route("/items/<int:id_producto>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_item(id_producto):
    item = next((p for p in PRODUCTOS_STORE if p["idProducto"] == id_producto), None)
    if not item:
        return jsonify({"success": False, "mensaje": "Ítem no encontrado."}), 404

    datos = request.get_json() or {}
    cambios = []
    if "nombre" in datos and datos["nombre"]:
        item["nombre"] = str(datos["nombre"]).strip()
        cambios.append(f"nombre='{item['nombre']}'")
    if "unidad" in datos and datos["unidad"]:
        item["unidad"] = str(datos["unidad"]).strip()
        cambios.append(f"unidad='{item['unidad']}'")
    if "stockMinimo" in datos:
        item["stockMinimo"] = float(datos["stockMinimo"])
        item["stock_minimo"] = item["stockMinimo"]
        cambios.append(f"stock mínimo={item['stockMinimo']}")
    if "presentacion" in datos:
        item["presentacion"] = float(datos["presentacion"])
    if "idCategoria" in datos and datos["idCategoria"]:
        item["idCategoria"] = int(datos["idCategoria"])
        item["id_categoria"] = item["idCategoria"]
    if "idProveedor" in datos and datos["idProveedor"]:
        item["idProveedor"] = int(datos["idProveedor"])
        item["id_proveedor"] = item["idProveedor"]

    registrar_actividad("EDITAR", "PRODUCTO", f"Modificó el ítem '{item['nombre']}' [{item['codigo']}] ({', '.join(cambios)})")

    return jsonify({
        "success": True,
        "mensaje": f"Ítem '{item['nombre']}' actualizado correctamente.",
        "item": item
    }), 200


# ---------------------------------------------------------------------------
# 2. GESTIÓN Y AJUSTE DE STOCK
# ---------------------------------------------------------------------------
@bp.route("/stock", methods=["GET"])
@jwt_required()
def obtener_stock():
    resultado = []
    for p in PRODUCTOS_STORE:
        d = dict(p)
        s_act = float(p.get("stockActual") or 0)
        s_min = float(p.get("stockMinimo") or 0)
        d["stockActual"] = round(s_act, 2)
        d["alertaStock"] = s_act <= s_min
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
    datos = request.get_json() or {}
    id_producto = datos.get("idProducto") or datos.get("id_producto")
    nuevo_stock = datos.get("nuevoStock") or datos.get("nuevo_stock")
    motivo = datos.get("motivo") or "Ajuste manual de inventario"
    observacion = datos.get("observacion") or "Corrección de stock físico"

    if not id_producto or nuevo_stock is None:
        return jsonify({"success": False, "mensaje": "Producto y Nuevo Stock son requeridos."}), 400

    item = next((p for p in PRODUCTOS_STORE if p["idProducto"] == int(id_producto)), None)
    if not item:
        return jsonify({"success": False, "mensaje": "Producto no encontrado."}), 404

    stock_anterior = float(item.get("stockActual") or 0.0)
    nuevo_stock_val = round(float(nuevo_stock), 2)
    item["stockActual"] = nuevo_stock_val
    item["stock_actual"] = nuevo_stock_val

    id_auth = get_jwt_identity()
    cod_mov = f"AJU-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Registrar en movimientos en memoria
    nuevo_mov = {
        "idMovimiento": len(MOVIMIENTOS_STORE) + 1,
        "codigo": cod_mov,
        "tipoMovimiento": "AJUSTE",
        "motivoMovimiento": motivo,
        "fechaMovimiento": date.today().isoformat(),
        "usuarioRegistro": int(id_auth) if id_auth else 1,
        "usuarioNombre": "Usuario del Sistema",
        "observacion": f"{observacion} (Stock corregido de {stock_anterior} a {nuevo_stock_val} {item['unidad']})",
        "detalles": [
            {"idProducto": item["idProducto"], "productoNombre": item["nombre"], "cantidad": nuevo_stock_val}
        ]
    }
    MOVIMIENTOS_STORE.insert(0, nuevo_mov)

    registrar_actividad(
        "AJUSTE",
        "STOCK",
        f"Ajustó el stock de '{item['nombre']}' [{item['codigo']}] de {stock_anterior} a {nuevo_stock_val} {item['unidad']}. Motivo: {motivo}",
        id_auth
    )

    return jsonify({
        "success": True,
        "mensaje": f"Stock de '{item['nombre']}' corregido y guardado a {nuevo_stock_val} {item['unidad']}.",
        "codigoMovimiento": cod_mov,
        "nuevoStock": nuevo_stock_val,
        "item": item
    }), 201


# ---------------------------------------------------------------------------
# 3. ENTRADAS Y SALIDAS (KARDEX)
# ---------------------------------------------------------------------------
@bp.route("/movimientos", methods=["GET"])
@jwt_required()
def listar_movimientos():
    return jsonify({
        "success": True,
        "movimientos": MOVIMIENTOS_STORE,
        "total": len(MOVIMIENTOS_STORE)
    }), 200


@bp.route("/movimientos", methods=["POST"])
@jwt_required()
def registrar_movimiento():
    datos = request.get_json() or {}
    tipo = str(datos.get("tipoMovimiento") or "ENTRADA").upper()
    motivo = datos.get("motivoMovimiento") or "Movimiento de inventario"
    items = datos.get("items") or []

    if not items and datos.get("idProducto") and datos.get("cantidad"):
        items = [{"idProducto": datos["idProducto"], "cantidad": datos["cantidad"]}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe incluir al menos un producto y cantidad."}), 400

    id_auth = get_jwt_identity()
    cod_mov = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    detalles = []
    resumen = []
    for it in items:
        p_id = int(it["idProducto"])
        cant = float(it["cantidad"])
        prod = next((p for p in PRODUCTOS_STORE if p["idProducto"] == p_id), None)
        p_nom = prod["nombre"] if prod else f"Producto {p_id}"
        detalles.append({"idProducto": p_id, "productoNombre": p_nom, "cantidad": cant})
        resumen.append(f"{cant} de '{p_nom}'")

        if prod:
            if tipo == "ENTRADA":
                prod["stockActual"] = round(float(prod["stockActual"]) + cant, 2)
            elif tipo == "SALIDA":
                prod["stockActual"] = round(max(0.0, float(prod["stockActual"]) - cant), 2)
            prod["stock_actual"] = prod["stockActual"]

    nuevo_mov = {
        "idMovimiento": len(MOVIMIENTOS_STORE) + 1,
        "codigo": cod_mov,
        "tipoMovimiento": tipo,
        "motivoMovimiento": motivo,
        "fechaMovimiento": date.today().isoformat(),
        "usuarioRegistro": int(id_auth) if id_auth else 1,
        "usuarioNombre": "Usuario del Sistema",
        "observacion": datos.get("observacion") or f"Movimiento {tipo} registrado",
        "detalles": detalles
    }
    MOVIMIENTOS_STORE.insert(0, nuevo_mov)

    registrar_actividad(
        "MOVIMIENTO",
        "KARDEX",
        f"Registró {tipo} de {', '.join(resumen)}. Motivo: {motivo}",
        id_auth
    )

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento {cod_mov} registrado con éxito.",
        "movimiento": nuevo_mov
    }), 201


@bp.route("/movimientos/<int:id_movimiento>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_movimiento(id_movimiento):
    mov = next((m for m in MOVIMIENTOS_STORE if m["idMovimiento"] == id_movimiento), None)
    if not mov:
        return jsonify({"success": False, "mensaje": "Movimiento no encontrado."}), 404

    datos = request.get_json() or {}
    if "motivoMovimiento" in datos:
        mov["motivoMovimiento"] = str(datos["motivoMovimiento"])
    if "observacion" in datos:
        mov["observacion"] = str(datos["observacion"])

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento {mov['codigo']} actualizado con éxito.",
        "movimiento": mov
    }), 200


# ---------------------------------------------------------------------------
# 4. SOLICITUDES DE COMPRA / ÓRDENES
# ---------------------------------------------------------------------------
@bp.route("/solicitudes", methods=["GET"])
@jwt_required()
def listar_solicitudes():
    return jsonify({
        "success": True,
        "solicitudes": SOLICITUDES_STORE,
        "total": len(SOLICITUDES_STORE)
    }), 200


@bp.route("/solicitudes", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def registrar_solicitud():
    datos = request.get_json() or {}
    items = datos.get("items") or []

    if not items and datos.get("idProducto") and datos.get("cantidad"):
        items = [{"idProducto": datos["idProducto"], "cantidad": datos["cantidad"]}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe seleccionar al menos un producto a solicitar."}), 400

    id_auth = get_jwt_identity()
    cod_oc = f"SOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    detalles = []
    resumen = []
    for it in items:
        p_id = int(it["idProducto"])
        cant = float(it["cantidad"])
        prod = next((p for p in PRODUCTOS_STORE if p["idProducto"] == p_id), None)
        p_nom = prod["nombre"] if prod else f"Producto {p_id}"
        p_uni = prod["unidad"] if prod else "Und"
        detalles.append({"idProducto": p_id, "productoNombre": p_nom, "cantidad": cant, "unidad": p_uni})
        resumen.append(f"{cant} {p_uni} de '{p_nom}'")

    nueva_sol = {
        "idOrden": len(SOLICITUDES_STORE) + 1,
        "idOrdenCompra": len(SOLICITUDES_STORE) + 1,
        "codigo": cod_oc,
        "estadoOrdenCompra": "PENDIENTE",
        "usuarioRegistro": int(id_auth) if id_auth else 1,
        "usuarioNombre": "Usuario del Sistema",
        "fechaRegistro": date.today().isoformat(),
        "detalles": detalles
    }
    SOLICITUDES_STORE.insert(0, nueva_sol)

    registrar_actividad(
        "SOLICITUD",
        "SOLICITUD",
        f"Emitió la solicitud de compra {cod_oc} solicitando: {', '.join(resumen)}",
        id_auth
    )

    return jsonify({
        "success": True,
        "mensaje": f"Solicitud de compra '{cod_oc}' registrada con éxito.",
        "solicitud": nueva_sol
    }), 201


@bp.route("/solicitudes/<int:id_orden>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def editar_solicitud(id_orden):
    sol = next((s for s in SOLICITUDES_STORE if s.get("idOrden") == id_orden or s.get("idOrdenCompra") == id_orden), None)
    if not sol:
        return jsonify({"success": False, "mensaje": "Solicitud no encontrada."}), 404

    datos = request.get_json() or {}
    if "estadoOrdenCompra" in datos:
        sol["estadoOrdenCompra"] = str(datos["estadoOrdenCompra"]).strip().upper()
    if "cantidad" in datos and sol.get("detalles"):
        try:
            sol["detalles"][0]["cantidad"] = float(datos["cantidad"])
        except Exception:
            pass

    id_auth = get_jwt_identity()
    registrar_actividad(
        "EDITAR",
        "SOLICITUD",
        f"Actualizó la solicitud de compra {sol['codigo']} al estado '{sol['estadoOrdenCompra']}'",
        id_auth
    )

    return jsonify({
        "success": True,
        "mensaje": f"Solicitud {sol['codigo']} actualizada con éxito.",
        "solicitud": sol
    }), 200


# ---------------------------------------------------------------------------
# 5. REALIZAR INVENTARIO FÍSICO
# ---------------------------------------------------------------------------
@bp.route("/inventarios", methods=["GET"])
@jwt_required()
def listar_inventarios():
    return jsonify({
        "success": True,
        "inventarios": INVENTARIOS_STORE,
        "total": len(INVENTARIOS_STORE)
    }), 200


@bp.route("/inventarios", methods=["POST"])
@jwt_required()
def registrar_toma_inventario():
    datos = request.get_json() or {}
    fecha_inv = datos.get("fechaInventario") or date.today().isoformat()
    observacion = datos.get("observacion") or "Conteo físico periódico"
    items = datos.get("items") or []

    if not items and datos.get("idProducto") and datos.get("stockContado") is not None:
        items = [{"idProducto": datos["idProducto"], "stockContado": datos["stockContado"]}]

    if not items:
        return jsonify({"success": False, "mensaje": "Debe registrar al menos un conteo de producto."}), 400

    id_auth = get_jwt_identity()
    detalles = []
    resumen = []
    for it in items:
        p_id = int(it["idProducto"])
        conteo = float(it["stockContado"])
        prod = next((p for p in PRODUCTOS_STORE if p["idProducto"] == p_id), None)
        p_nom = prod["nombre"] if prod else f"Producto {p_id}"
        p_uni = prod["unidad"] if prod else "Und"
        if prod:
            prod["stockActual"] = conteo
            prod["stock_actual"] = conteo
        detalles.append({"idProducto": p_id, "productoNombre": p_nom, "stockContado": conteo})
        resumen.append(f"{p_nom} (Conteo: {conteo} {p_uni})")

    nuevo_inv = {
        "idInventario": len(INVENTARIOS_STORE) + 1,
        "idInventarioCierre": len(INVENTARIOS_STORE) + 1,
        "fechaInventario": fecha_inv,
        "estadoInventario": "CERRADO",
        "usuarioRegistro": int(id_auth) if id_auth else 1,
        "usuarioNombre": "Usuario del Sistema",
        "fechaRegistro": date.today().isoformat(),
        "observacion": observacion,
        "detalles": detalles
    }
    INVENTARIOS_STORE.insert(0, nuevo_inv)

    registrar_actividad(
        "INVENTARIO",
        "INVENTARIO",
        f"Registró acta de inventario físico del {fecha_inv}. Conteo: {', '.join(resumen)}",
        id_auth
    )

    return jsonify({
        "success": True,
        "mensaje": f"Inventario físico del {fecha_inv} registrado con éxito.",
        "inventario": nuevo_inv
    }), 201


# ---------------------------------------------------------------------------
# 6. GESTIÓN DE MIEMBROS DE EQUIPO (PERSISTENCIA REAL EN TABLA USUARIO Y USUARIO_PERFILES)
# ---------------------------------------------------------------------------
@bp.route("/miembros-equipo", methods=["GET"])
@jwt_required()
def listar_miembros_equipo():
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
    datos = request.get_json() or {}
    dni = str(datos.get("dni", "")).strip()
    nombres = str(datos.get("nombres", "")).strip()
    ap_paterno = str(datos.get("apellidoPaterno", "")).strip()
    ap_materno = str(datos.get("apellidoMaterno", "")).strip() or None
    celular = str(datos.get("celular", "")).strip() or None
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
            "mensaje": f"El miembro con DNI '{dni}' o correo '{correo}' ya se encuentra registrado. No se volverá a insertar."
        }), 409

    id_auth = get_jwt_identity()
    usuario_creador = int(id_auth) if id_auth else None

    nuevo = Usuario(
        DNI=dni[:8],
        Nombres=nombres[:100],
        ApellidoPaterno=ap_paterno[:100],
        ApellidoMaterno=ap_materno[:100] if ap_materno else None,
        Celular=celular[:9] if celular else None,
        CorreoElectronico=correo[:150],
        UsuarioCreacion=usuario_creador,
        FechaCreacion=date.today(),
        EstadoRegistro=1
    )
    nuevo.set_clave(clave)
    db.session.add(nuevo)
    db.session.flush()

    asig = UsuarioPerfil(
        IdUsuario=nuevo.IdUsuario,
        IdPerfil=3,
        UsuarioAsignacion=usuario_creador or 1,
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
    return jsonify({
        "success": True,
        "actividades": ACTIVIDADES_MEMORIA,
        "total": len(ACTIVIDADES_MEMORIA)
    }), 200
