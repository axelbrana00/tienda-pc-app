from flask import Blueprint, render_template

from models import db

bp = Blueprint("errores", __name__)


@bp.app_errorhandler(404)
def no_encontrado(error):
    return render_template("error.html", codigo=404, mensaje="La página que buscás no existe."), 404


@bp.app_errorhandler(500)
def error_interno(error):
    db.session.rollback()
    return render_template(
        "error.html", codigo=500, mensaje="Ocurrió un error inesperado. Probá de nuevo en un momento."
    ), 500