from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from models import Componente, Movimiento, db

bp = Blueprint("movimientos", __name__)


@bp.app_template_filter("hora_ar")
def hora_ar(fecha):
    return (fecha - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")


@bp.route("/movimientos")
@login_required
def listado():
    lista = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(100).all()
    return render_template("movimientos.html", movimientos=lista)


@bp.route("/movimientos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        try:
            componente_id = int(request.form["componente_id"])
            cantidad = int(request.form["cantidad"])
        except (KeyError, ValueError):
            flash("Revisá los datos ingresados.", "danger")
            return redirect(url_for("movimientos.nuevo"))

        tipo = request.form.get("tipo")
        componente = db.session.get(Componente, componente_id)

        if componente is None or tipo not in ("entrada", "salida") or cantidad <= 0:
            flash("Los datos no son válidos.", "danger")
            return redirect(url_for("movimientos.nuevo"))

        if tipo == "salida" and cantidad > componente.stock:
            flash(f"No hay stock suficiente. Stock actual: {componente.stock}.", "danger")
            return redirect(url_for("movimientos.nuevo"))

        if tipo == "entrada":
            componente.stock += cantidad
        else:
            componente.stock -= cantidad

        try:
            db.session.add(Movimiento(componente_id=componente.id, tipo=tipo, cantidad=cantidad))
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo registrar el movimiento.", "danger")
            return redirect(url_for("movimientos.nuevo"))

        flash("Movimiento registrado.", "success")
        if componente.stock <= componente.stock_minimo:
            flash(f"Atención: {componente.nombre} quedó con stock bajo ({componente.stock}).", "warning")
        return redirect(url_for("movimientos.listado"))

    componentes = Componente.query.filter_by(activo=True).order_by(Componente.nombre).all()
    return render_template("movimiento_nuevo.html", componentes=componentes)