from datetime import datetime, date
import bcrypt
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class Usuario(db.Model):
    """
    Modelo de la tabla 'usuario' en la base de datos barbarito.
    """
    __tablename__ = "usuario"

    IdUsuario = db.Column("id_usuario", db.Integer, primary_key=True, autoincrement=True)
    DNI = db.Column("dni", db.String(20), nullable=False)
    Nombres = db.Column("nombres", db.String(100), nullable=False)
    ApellidoPaterno = db.Column("apellido_paterno", db.String(100), nullable=False)
    ApellidoMaterno = db.Column("apellido_materno", db.String(100), nullable=True)
    Celular = db.Column("celular", db.String(20), nullable=True)
    CorreoElectronico = db.Column(
        "correo_electronico", db.String(150), nullable=False, unique=True, index=True
    )
    Clave = db.Column("clave", db.String(255), nullable=False)
    UsuarioCreacion = db.Column("usuario_creacion", db.Integer, nullable=True)
    FechaCreacion = db.Column(
        "fecha_creacion", db.Date, server_default=db.func.now(), nullable=False
    )
    UsuarioModificacion = db.Column("usuario_modificacion", db.Integer, nullable=True)
    FechaModificacion = db.Column("fecha_modificacion", db.Date, nullable=True)
    EstadoRegistro = db.Column("estado_registro", db.SmallInteger, default=1, nullable=False)

    asignaciones_perfil = db.relationship(
        "UsuarioPerfil",
        backref="usuario",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    @property
    def id_usuario(self):
        return self.IdUsuario

    @property
    def correo(self):
        return self.CorreoElectronico

    @property
    def correo_electronico(self):
        return self.CorreoElectronico

    @property
    def nombre_completo(self):
        ap_materno = f" {self.ApellidoMaterno}" if self.ApellidoMaterno else ""
        return f"{self.Nombres} {self.ApellidoPaterno}{ap_materno}".strip()

    def set_clave(self, clave_plana: str):
        salt = bcrypt.gensalt(12)
        self.Clave = bcrypt.hashpw(clave_plana.encode("utf-8"), salt).decode("utf-8")

    def verificar_clave(self, clave_plana: str) -> bool:
        if not self.Clave or not clave_plana:
            return False

        # Si el hash almacenado es bcrypt ($2a$, $2b$, $2y$)
        if (
            self.Clave.startswith("$2a$")
            or self.Clave.startswith("$2b$")
            or self.Clave.startswith("$2y$")
        ):
            try:
                return bcrypt.checkpw(
                    clave_plana.encode("utf-8"), self.Clave.encode("utf-8")
                )
            except Exception:
                pass

        try:
            return check_password_hash(self.Clave, clave_plana)
        except Exception:
            return False

    @property
    def perfiles_activos(self):
        resultado = []
        for asig in self.asignaciones_perfil:
            if asig.EstadoRegistro == 1 and asig.perfil and asig.perfil.EstadoRegistro == 1:
                resultado.append(asig.perfil)
        return resultado

    @property
    def perfiles(self):
        return self.perfiles_activos

    def to_dict(self, incluir_perfiles=True):
        data = {
            "idUsuario": self.IdUsuario,
            "id_usuario": self.IdUsuario,
            "dni": self.DNI,
            "nombres": self.Nombres,
            "apellidoPaterno": self.ApellidoPaterno,
            "apellidoMaterno": self.ApellidoMaterno or "",
            "nombreCompleto": self.nombre_completo,
            "celular": self.Celular,
            "correoElectronico": self.CorreoElectronico,
            "correo": self.CorreoElectronico,
            "usuarioCreacion": self.UsuarioCreacion,
            "fechaCreacion": self.FechaCreacion.isoformat() if self.FechaCreacion else None,
            "usuarioModificacion": self.UsuarioModificacion,
            "fechaModificacion": self.FechaModificacion.isoformat() if self.FechaModificacion else None,
            "estadoRegistro": self.EstadoRegistro,
            "estado_registro": self.EstadoRegistro,
        }
        if incluir_perfiles:
            data["perfiles"] = [p.to_dict() for p in self.perfiles_activos]
            data["perfiles_ids"] = [p.IdPerfil for p in self.perfiles_activos]
        return data


class UsuarioPerfil(db.Model):
    """
    Tabla intermedia 'usuario_perfiles' en la base de datos barbarito.
    """
    __tablename__ = "usuario_perfiles"

    IdUsuario = db.Column(
        "id_usuario",
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    IdPerfil = db.Column(
        "id_perfil",
        db.Integer,
        db.ForeignKey("perfiles.id_perfil", ondelete="CASCADE"),
        primary_key=True,
    )
    UsuarioAsignacion = db.Column("usuario_asignacion", db.Integer, nullable=False, default=1)
    FechaAsignacion = db.Column(
        "fecha_asignacion", db.Date, server_default=db.func.now(), nullable=False
    )
    UsuarioModificacion = db.Column("usuario_modificacion", db.Integer, nullable=True)
    FechaModificacion = db.Column("fecha_modificacion", db.Date, nullable=True)
    EstadoRegistro = db.Column("estado_registro", db.SmallInteger, default=1, nullable=False)

    perfil = db.relationship("Perfil", lazy="joined")

    def to_dict(self):
        return {
            "idUsuario": self.IdUsuario,
            "idPerfil": self.IdPerfil,
            "usuarioAsignacion": self.UsuarioAsignacion,
            "fechaAsignacion": self.FechaAsignacion.isoformat() if self.FechaAsignacion else None,
            "usuarioModificacion": self.UsuarioModificacion,
            "fechaModificacion": self.FechaModificacion.isoformat() if self.FechaModificacion else None,
            "estadoRegistro": self.EstadoRegistro,
            "perfil": self.perfil.to_dict() if self.perfil else None,
        }
