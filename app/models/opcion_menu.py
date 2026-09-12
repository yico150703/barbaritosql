from ..extensions import db


class OpcionMenu(db.Model):
    """
    Modelo de la tabla 'OpcionesMenu'.
    """
    __tablename__ = "OpcionesMenu"

    IdOpcionMenu = db.Column("id_opcion_menu", db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column("nombre", db.String(100), nullable=False)
    UrlMenu = db.Column("url_menu", db.String(150), nullable=False)
    Descripcion = db.Column("descripcion", db.String(255), nullable=True)
    IdPadre = db.Column(
        "id_padre",
        db.Integer,
        db.ForeignKey("OpcionesMenu.id_opcion_menu", ondelete="CASCADE"),
        nullable=True,
    )
    EstadoRegistro = db.Column("estado_registro", db.SmallInteger, default=1, nullable=False)

    hijos = db.relationship(
        "OpcionMenu",
        backref=db.backref("padre", remote_side=[IdOpcionMenu]),
        cascade="all",
        lazy="select",
    )

    @property
    def id_opcion_menu(self):
        return self.IdOpcionMenu

    @property
    def nombre(self):
        return self.Nombre

    @property
    def url_menu(self):
        return self.UrlMenu

    @property
    def id_padre(self):
        return self.IdPadre

    def to_dict(self, incluir_hijos=False):
        data = {
            "idOpcionMenu": self.IdOpcionMenu,
            "id_opcion_menu": self.IdOpcionMenu,
            "nombre": self.Nombre,
            "urlMenu": self.UrlMenu,
            "url_menu": self.UrlMenu,
            "descripcion": self.Descripcion or "",
            "idPadre": self.IdPadre,
            "id_padre": self.IdPadre,
            "padreNombre": self.padre.Nombre if self.padre else None,
            "estadoRegistro": self.EstadoRegistro,
            "estado_registro": self.EstadoRegistro,
        }
        if incluir_hijos:
            data["hijos"] = [
                h.to_dict(incluir_hijos=True)
                for h in self.hijos
                if h.EstadoRegistro == 1
            ]
        return data


class OpcionMenuPerfil(db.Model):
    """
    Modelo de la tabla intermedia 'OpcionesMenu_Perfiles'.
    """
    __tablename__ = "OpcionesMenu_Perfiles"

    IdPerfil = db.Column(
        "id_perfil",
        db.Integer,
        db.ForeignKey("perfiles.id_perfil", ondelete="CASCADE"),
        primary_key=True,
    )
    IdOpcionMenu = db.Column(
        "id_opcion_menu",
        db.Integer,
        db.ForeignKey("OpcionesMenu.id_opcion_menu", ondelete="CASCADE"),
        primary_key=True,
    )
    Orden = db.Column("orden", db.SmallInteger, default=1, nullable=False)
    EstadoRegistro = db.Column("estado_registro", db.SmallInteger, default=1, nullable=False)

    @property
    def PuedeConsultar(self):
        return True

    @property
    def PuedeCrear(self):
        return True

    @property
    def PuedeEditar(self):
        return True

    @property
    def PuedeRevisar(self):
        return True

    @property
    def PuedeCerrar(self):
        return True

    opcion_menu = db.relationship("OpcionMenu", lazy="joined")
    perfil = db.relationship("Perfil", lazy="joined")

    def to_dict(self):
        return {
            "idOpcionMenu": self.IdOpcionMenu,
            "idPerfil": self.IdPerfil,
            "orden": self.Orden,
            "puedeConsultar": True,
            "puedeCrear": True,
            "puedeEditar": True,
            "puedeRevisar": True,
            "puedeCerrar": True,
            "estadoRegistro": self.EstadoRegistro,
            "opcion": self.opcion_menu.to_dict() if self.opcion_menu else None,
            "perfil": self.perfil.to_dict() if self.perfil else None,
        }
