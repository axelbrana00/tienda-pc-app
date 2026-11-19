from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

componente_proveedor = db.Table(
    "componente_proveedor",
    db.Column("componente_id", db.Integer, db.ForeignKey("componente.id"), primary_key=True),
    db.Column("proveedor_id", db.Integer, db.ForeignKey("proveedor.id"), primary_key=True),
)


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200))  # vacío si entra con Google


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)


class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(150))


class Componente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    activo = db.Column(db.Boolean, default=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"))
    categoria = db.relationship("Categoria", backref="componentes")
    proveedores = db.relationship("Proveedor", secondary=componente_proveedor, backref="componentes")


class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    componente_id = db.Column(db.Integer, db.ForeignKey("componente.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # "entrada" o "salida"
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    componente = db.relationship("Componente", backref="movimientos")