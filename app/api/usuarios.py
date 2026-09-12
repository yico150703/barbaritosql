from datetime import datetime, date
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..auth.decorators import requiere_rol
from ..extensions import db
from ..models.perfil import Perfil
from ..models.usuario import Usuario, UsuarioPerfil
from .operaciones import registrar_actividad

bp = Blueprint("usuarios", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def listar_usuarios():
    """
    Listar usuarios con paginación, búsqueda y filtro de EstadoRegistro = 1.
    """
    query_str = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"

    query = Usuario.query
    if not incluir_inactivos:
        query = query.filter(Usuario.EstadoRegistro == 1)

    if query_str:
        filtro = or_(
            Usuario.Nombres.ilike(f"%{query_str}%"),
            Usuario.ApellidoPaterno.ilike(f"%{query_str}%"),
            Usuario.ApellidoMaterno.ilike(f"%{query_str}%"),
            Usuario.CorreoElectronico.ilike(f"%{query_str}%"),
            Usuario.DNI.ilike(f"%{query_str}%")
        )
        query = query.filter(filtro)

    query = query.order_by(Usuario.IdUsuario.asc())
    paginado = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "success": True,
        "usuarios": [u.to_dict(incluir_perfiles=True) for u in paginado.items],
        "total": paginado.total,
        "pagina_actual": paginado.page,
        "total_paginas": paginado.pages
    }), 200


@bp.route("/<int:id_usuario>", methods=["GET"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def obtener_usuario(id_usuario):
    usuario = Usuario.query.filter_by(IdUsuario=id_usuario).first()
    if not usuario:
        return jsonify({"success": False, "mensaje": "Usuario no encontrado."}), 404

    return jsonify({
        "success": True,
        "usuario": usuario.to_dict(incluir_perfiles=True)
    }), 200


@bp.route("", methods=["POST"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def crear_usuario():
    """
    Creación de usuario con validación estricta de existencia previa:
    'una inserción de datos para añadir usuario si es que ya existe no lo hagas'.
    """
    datos = request.get_json() or {}
    dni = str(datos.get("dni") or datos.get("DNI") or "").strip()
    nombres = str(datos.get("nombres") or datos.get("Nombres") or "").strip()
    ap_paterno = str(datos.get("apellidoPaterno") or datos.get("ApellidoPaterno") or "").strip()
    ap_materno = str(datos.get("apellidoMaterno") or datos.get("ApellidoMaterno") or "").strip()
    celular = str(datos.get("celular") or datos.get("Celular") or "").strip()
    correo = str(datos.get("correoElectronico") or datos.get("correo") or datos.get("CorreoElectronico") or "").strip().lower()
    clave = datos.get("clave") or datos.get("password") or datos.get("Clave") or "password123"
    perfiles_ids = datos.get("perfiles_ids") or datos.get("perfilesIds") or []
    omitir_si_existe = datos.get("omitir_si_existe", False) or datos.get("si_existe_no_hacer", False)

    if not all([dni, nombres, ap_paterno, correo]):
        return jsonify({
            "success": False,
            "mensaje": "Los campos DNI, Nombres, Apellido Paterno y Correo Electrónico son obligatorios."
        }), 400

    # VALIDACIÓN: Si el usuario ya existe por DNI o Correo, NO INSERTAR
    usuario_existente = Usuario.query.filter(
        or_(
            Usuario.DNI == dni,
            Usuario.CorreoElectronico.ilike(correo)
        )
    ).first()

    if usuario_existente:
        if omitir_si_existe:
            return jsonify({
                "success": True,
                "omitido": True,
                "yaExiste": True,
                "mensaje": f"El usuario con DNI '{dni}' o correo '{correo}' ya existe en el sistema. Se omitió la inserción sin duplicar.",
                "usuario": usuario_existente.to_dict(incluir_perfiles=True)
            }), 200
        else:
            return jsonify({
                "success": False,
                "yaExiste": True,
                "error": "USUARIO_YA_EXISTE",
                "mensaje": f"El usuario con DNI '{dni}' o correo '{correo}' ya se encuentra registrado. No se volverá a insertar."
            }), 409

    id_auth = get_jwt_identity()
    usuario_creador = int(id_auth) if id_auth else None

    nuevo_usuario = Usuario(
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
    nuevo_usuario.set_clave(clave)

    db.session.add(nuevo_usuario)
    db.session.flush()

    # Asignar perfiles seleccionados
    if perfiles_ids:
        for pid in set(perfiles_ids):
            perfil = Perfil.query.filter_by(IdPerfil=int(pid), EstadoRegistro=1).first()
            if perfil:
                asig = UsuarioPerfil(
                    IdUsuario=nuevo_usuario.IdUsuario,
                    IdPerfil=perfil.IdPerfil,
                    UsuarioAsignacion=usuario_creador or 1,
                    FechaAsignacion=date.today(),
                    EstadoRegistro=1
                )
                db.session.add(asig)
    else:
        # Por defecto Miembro de equipo (3)
        asig = UsuarioPerfil(
            IdUsuario=nuevo_usuario.IdUsuario,
            IdPerfil=3,
            UsuarioAsignacion=usuario_creador or 1,
            FechaAsignacion=date.today(),
            EstadoRegistro=1
        )
        db.session.add(asig)

    registrar_actividad("CREAR", "USUARIO", f"Creó al usuario '{nuevo_usuario.nombre_completo}' (DNI: {nuevo_usuario.DNI}, Correo: {nuevo_usuario.CorreoElectronico})", usuario_creador)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Usuario creado y registrado exitosamente en la base de datos.",
        "usuario": nuevo_usuario.to_dict(incluir_perfiles=True)
    }), 201


@bp.route("/<int:id_usuario>", methods=["PUT"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def actualizar_usuario(id_usuario):
    usuario = Usuario.query.filter_by(IdUsuario=id_usuario).first()
    if not usuario:
        return jsonify({"success": False, "mensaje": "Usuario no encontrado."}), 404

    datos = request.get_json() or {}
    dni = datos.get("dni") or datos.get("DNI")
    nombres = datos.get("nombres") or datos.get("Nombres")
    ap_paterno = datos.get("apellidoPaterno") or datos.get("ApellidoPaterno")
    ap_materno = datos.get("apellidoMaterno") or datos.get("ApellidoMaterno")
    celular = datos.get("celular") or datos.get("Celular")
    correo = datos.get("correoElectronico") or datos.get("correo") or datos.get("CorreoElectronico")
    clave = datos.get("clave") or datos.get("password") or datos.get("Clave")
    perfiles_ids = datos.get("perfiles_ids") or datos.get("perfilesIds")
    estado = datos.get("estadoRegistro")
    if estado is None:
        estado = datos.get("estado_registro")

    # Validar correo único en otros usuarios
    if correo and str(correo).strip().lower() != usuario.CorreoElectronico.lower():
        duplicado = Usuario.query.filter(
            Usuario.CorreoElectronico.ilike(str(correo).strip()),
            Usuario.IdUsuario != id_usuario
        ).first()
        if duplicado:
            return jsonify({
                "success": False,
                "mensaje": "El correo electrónico ya pertenece a otro usuario."
            }), 409
        usuario.CorreoElectronico = str(correo).strip().lower()

    if dni:
        usuario.DNI = str(dni).strip()[:8]
    if nombres:
        usuario.Nombres = str(nombres).strip()[:100]
    if ap_paterno:
        usuario.ApellidoPaterno = str(ap_paterno).strip()[:100]
    if ap_materno is not None:
        usuario.ApellidoMaterno = str(ap_materno).strip()[:100] if ap_materno else None
    if celular is not None:
        usuario.Celular = str(celular).strip()[:9] if celular else None
    if clave:
        usuario.set_clave(clave)
    if estado is not None:
        usuario.EstadoRegistro = int(estado)

    id_auth = get_jwt_identity()
    usuario.UsuarioModificacion = int(id_auth) if id_auth else None
    usuario.FechaModificacion = date.today()

    # Actualizar asignaciones de perfil si se enviaron
    if perfiles_ids is not None:
        UsuarioPerfil.query.filter_by(IdUsuario=id_usuario).delete()
        for pid in set(perfiles_ids):
            perfil = Perfil.query.filter_by(IdPerfil=int(pid)).first()
            if perfil:
                asig = UsuarioPerfil(
                    IdUsuario=id_usuario,
                    IdPerfil=perfil.IdPerfil,
                    UsuarioAsignacion=usuario.UsuarioModificacion or 1,
                    FechaAsignacion=date.today(),
                    EstadoRegistro=1
                )
                db.session.add(asig)

    registrar_actividad("EDITAR", "USUARIO", f"Actualizó los datos del usuario '{usuario.nombre_completo}' (DNI: {usuario.DNI})", id_auth)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Usuario actualizado exitosamente en la base de datos.",
        "usuario": usuario.to_dict(incluir_perfiles=True)
    }), 200


@bp.route("/<int:id_usuario>", methods=["DELETE"])
@jwt_required()
@requiere_rol(1, 2, "Técnico", "Gerente")
def desactivar_usuario(id_usuario):
    """
    Eliminación lógica (Soft Delete) cambiando EstadoRegistro = 0.
    """
    usuario = Usuario.query.filter_by(IdUsuario=id_usuario).first()
    if not usuario:
        return jsonify({"success": False, "mensaje": "Usuario no encontrado."}), 404

    usuario.EstadoRegistro = 0
    id_auth = get_jwt_identity()
    usuario.UsuarioModificacion = int(id_auth) if id_auth else None
    usuario.FechaModificacion = date.today()

    registrar_actividad("ELIMINAR", "USUARIO", f"Desactivó la cuenta del usuario '{usuario.nombre_completo}' (DNI: {usuario.DNI})", id_auth)
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": f"Usuario '{usuario.nombre_completo}' desactivado correctamente (EstadoRegistro = 0)."
    }), 200
