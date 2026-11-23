from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from models import Proveedor, db

bp = Blueprint("proveedores", __name__)


@bp.route("/proveedores")
@login_required
def listado():
    lista = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template("proveedores.html", proveedores=lista)


@bp.route("/proveedores/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        contacto = request.form.get("contacto", "").strip()

        if not nombre:
            flash("El nombre es obligatorio.", "danger")
            return redirect(url_for("proveedores.nuevo"))

        try:
            db.session.add(Proveedor(nombre=nombre, contacto=contacto))
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo guardar el proveedor.", "danger")
            return redirect(url_for("proveedores.nuevo"))

        flash("Proveedor guardado.", "success")
        return redirect(url_for("proveedores.listado"))

    return render_template("proveedor_nuevo.html")