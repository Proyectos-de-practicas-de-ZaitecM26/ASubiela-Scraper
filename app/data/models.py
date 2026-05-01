from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

sa_db = SQLAlchemy()


class Oposicion(sa_db.Model):
    __tablename__ = 'oposiciones'
    
    id = sa_db.Column(sa_db.Integer, primary_key=True, autoincrement=True)
    identificador = sa_db.Column(sa_db.String)
    control = sa_db.Column(sa_db.String)
    titulo = sa_db.Column(sa_db.String)
    url_html = sa_db.Column(sa_db.String, unique=True)
    url_pdf = sa_db.Column(sa_db.String)
    departamento = sa_db.Column(sa_db.String, index=True)
    fecha = sa_db.Column(sa_db.String, index=True)
    provincia = sa_db.Column(sa_db.String)

    # Relaciones inversas
    usuarios_visitas = sa_db.relationship(
        'Visita', backref='oposicion', cascade="all, delete-orphan"
    )
    usuarios_favoritos = sa_db.relationship(
        'Favorita', backref='oposicion', cascade="all, delete-orphan"
    )


class User(sa_db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = sa_db.Column(sa_db.Integer, primary_key=True, autoincrement=True)
    email = sa_db.Column(sa_db.String, unique=True, nullable=False)
    password_hash = sa_db.Column(sa_db.String, nullable=False)

    # 🔥 ROLE CORRECTO (SOLO UNO)
    ROLES = ('admin', 'manager', 'viewer')
    role = sa_db.Column(sa_db.String(20), nullable=False, default='viewer')

    name = sa_db.Column(sa_db.String)
    apellidos = sa_db.Column(sa_db.String)
    age = sa_db.Column(sa_db.Integer)
    telefono = sa_db.Column(sa_db.String)
    foto_perfil = sa_db.Column(sa_db.String)
    nivel_estudios = sa_db.Column(sa_db.String)
    titulacion = sa_db.Column(sa_db.String)

    # Relaciones
    visitas = sa_db.relationship(
        'Visita', backref='user', cascade="all, delete-orphan"
    )
    favoritas = sa_db.relationship(
        'Favorita', backref='user', cascade="all, delete-orphan"
    )
    suscripcion = sa_db.relationship(
        'Suscripcion', backref='user', uselist=False, cascade="all, delete-orphan"
    )


class Visita(sa_db.Model):
    __tablename__ = 'visitas'
    __table_args__ = (
        sa_db.UniqueConstraint('user_id', 'oposicion_id', name='unique_user_visita'),
    )
    
    id = sa_db.Column(sa_db.Integer, primary_key=True, autoincrement=True)
    user_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('users.id'), nullable=False)
    oposicion_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('oposiciones.id'), nullable=False)
    fecha_visita = sa_db.Column(
        sa_db.String,
        nullable=False,
        default=lambda: datetime.now().isoformat()
    )


class Favorita(sa_db.Model):
    __tablename__ = 'favoritas'
    __table_args__ = (
        sa_db.UniqueConstraint('user_id', 'oposicion_id', name='unique_user_favorito'),
    )
    
    id = sa_db.Column(sa_db.Integer, primary_key=True, autoincrement=True)
    user_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('users.id'), nullable=False)
    oposicion_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('oposiciones.id'), nullable=False)
    fecha_favorito = sa_db.Column(sa_db.String, nullable=False)


class Suscripcion(sa_db.Model):
    __tablename__ = 'suscripciones'
    
    user_id = sa_db.Column(
        sa_db.Integer,
        sa_db.ForeignKey('users.id'),
        primary_key=True
    )
    alerta_diaria = sa_db.Column(sa_db.Integer, default=0)
    alerta_favoritos = sa_db.Column(sa_db.Integer, default=0)
    departamento_filtro = sa_db.Column(sa_db.String)