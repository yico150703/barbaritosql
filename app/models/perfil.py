from ..extensions import db


class Perfil(db.Model):
    """
    Modelo de la tabla 'perfiles' en la base de datos barbarito.
    Roles:
      1 = Administrador del sistema (Técnico)
      2 = Gerente
      3 = Supervisor
      4 = Miembro de equipo
    """
    __tablename__ = "perfiles"

    IdPerfil = db.Column("id_perfil", db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column("nombre", db.String(100), nullable=False)
    Descripcion = db.Column("descripcion", db.String(255), nullable=True)
    EstadoRegistro = db.Column("estado_registro", db.SmallInteger, default=1, nullable=False)

    @property
    def id_perfil(self):
        return self.IdPerfil

    @property
    def nombre(self):
        return self.Nombre

    @property
    def descripcion(self):
        return self.Descripcion

    @property
    def estado_registro(self):
        return self.EstadoRegistro

    def to_dict(self):
        return {
            "idPerfil": self.IdPerfil,
            "id_perfil": self.IdPerfil,
            "nombre": self.Nombre,
            "descripcion": self.Descripcion or "",
            "estadoRegistro": self.EstadoRegistro,
            "estado_registro": self.EstadoRegistro,
        }
