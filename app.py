import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix

from models import Categoria, Componente, Proveedor, Usuario, db

load_dotenv()

from proveedores import bp as proveedores_bp

from errores import bp as errores_bp

from servicios import bp as servicios_bp

from movimientos import bp as movimientos_bp

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tienda.db")

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Iniciá sesión para continuar."

app.register_blueprint(proveedores_bp)

app.register_blueprint(errores_bp)

app.register_blueprint(servicios_bp)

app.register_blueprint(movimientos_bp)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

CATEGORIAS_INICIALES = [
    "Procesadores",
    "Placas de video",
    "Memorias RAM",
    "Motherboards",
    "Almacenamiento",
    "Fuentes",
    "Gabinetes",
]

with app.app_context():
    db.create_all()
    if not Categoria.query.first():
        for nombre in CATEGORIAS_INICIALES:
            db.session.add(Categoria(nombre=nombre))
        db.session.commit()


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if Usuario.query.filter_by(email=email).first():
            flash("Ese email ya está registrado.", "danger")
            return redirect(url_for("registro"))

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        usuario = Usuario(nombre=nombre, email=email, password=password_hash)
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        return redirect(url_for("inicio"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.password and bcrypt.check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for("inicio"))

        flash("Email o contraseña incorrectos.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/login/google")
def login_google():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def google_callback():
    try:
        token = google.authorize_access_token()
        info = token["userinfo"]
        email = info["email"].lower()
        nombre = info.get("name", email)
    except Exception:
        flash("No se pudo ingresar con Google. Probá de nuevo.", "danger")
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        usuario = Usuario(nombre=nombre, email=email, password=None)
        db.session.add(usuario)
        db.session.commit()

    login_user(usuario)
    return redirect(url_for("inicio"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/componentes")
@login_required
def componentes():
    busqueda = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", type=int)

    consulta = Componente.query.filter_by(activo=True)
    if busqueda:
        consulta = consulta.filter(Componente.nombre.ilike(f"%{busqueda}%"))
    if categoria_id:
        consulta = consulta.filter(Componente.categoria_id == categoria_id)

    lista = consulta.order_by(Componente.nombre).all()
    return render_template(
        "componentes.html",
        componentes=lista,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        busqueda=busqueda,
        categoria_id=categoria_id,
    )


@app.route("/componentes/nuevo", methods=["GET", "POST"])
@login_required
def componente_nuevo():
    if request.method == "POST":
        try:
            nombre = request.form["nombre"].strip()
            precio = float(request.form["precio"])
            stock = int(request.form["stock"])
            stock_minimo = int(request.form["stock_minimo"])
            categoria_id = int(request.form["categoria_id"])
        except (KeyError, ValueError):
            flash("Revisá los datos ingresados.", "danger")
            return redirect(url_for("componente_nuevo"))

        if not nombre or precio < 0 or stock < 0 or stock_minimo < 0:
            flash("Los datos no son válidos.", "danger")
            return redirect(url_for("componente_nuevo"))

        componente = Componente(
            nombre=nombre,
            precio=precio,
            stock=stock,
            stock_minimo=stock_minimo,
            categoria_id=categoria_id,
        )
        ids = [int(i) for i in request.form.getlist("proveedores")]
        if ids:
            componente.proveedores = Proveedor.query.filter(Proveedor.id.in_(ids)).all()

        try:
            db.session.add(componente)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo guardar el componente.", "danger")
            return redirect(url_for("componente_nuevo"))

        flash("Componente guardado.", "success")
        return redirect(url_for("componentes"))

    return render_template(
        "componente_nuevo.html",
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        proveedores=Proveedor.query.order_by(Proveedor.nombre).all(),
    )


@app.route("/componentes/<int:componente_id>/editar", methods=["GET", "POST"])
@login_required
def componente_editar(componente_id):
    componente = db.session.get(Componente, componente_id)
    if componente is None:
        flash("El componente no existe.", "danger")
        return redirect(url_for("componentes"))

    if request.method == "POST":
        try:
            nombre = request.form["nombre"].strip()
            precio = float(request.form["precio"])
            stock = int(request.form["stock"])
            stock_minimo = int(request.form["stock_minimo"])
            categoria_id = int(request.form["categoria_id"])
        except (KeyError, ValueError):
            flash("Revisá los datos ingresados.", "danger")
            return redirect(url_for("componente_editar", componente_id=componente_id))

        if not nombre or precio < 0 or stock < 0 or stock_minimo < 0:
            flash("Los datos no son válidos.", "danger")
            return redirect(url_for("componente_editar", componente_id=componente_id))

        componente.nombre = nombre
        componente.precio = precio
        componente.stock = stock
        componente.stock_minimo = stock_minimo
        componente.categoria_id = categoria_id
        componente.activo = "activo" in request.form

        ids = [int(i) for i in request.form.getlist("proveedores")]
        componente.proveedores = Proveedor.query.filter(Proveedor.id.in_(ids)).all() if ids else []

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudieron guardar los cambios.", "danger")
            return redirect(url_for("componente_editar", componente_id=componente_id))

        flash("Cambios guardados.", "success")
        return redirect(url_for("componentes"))

    return render_template(
        "componente_editar.html",
        componente=componente,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        proveedores=Proveedor.query.order_by(Proveedor.nombre).all(),
    )


@app.route("/reporte")
@login_required
def reporte():
    activos = Componente.query.filter_by(activo=True).all()

    por_categoria = []
    for categoria in Categoria.query.order_by(Categoria.nombre).all():
        de_la_categoria = [c for c in activos if c.categoria_id == categoria.id]
        por_categoria.append(
            {
                "nombre": categoria.nombre,
                "componentes": len(de_la_categoria),
                "unidades": sum(c.stock for c in de_la_categoria),
                "valor": sum(c.stock * c.precio for c in de_la_categoria),
            }
        )

    return render_template(
        "reporte.html",
        total_componentes=len(activos),
        total_unidades=sum(c.stock for c in activos),
        valor_total=sum(c.stock * c.precio for c in activos),
        stock_bajo=[c for c in activos if c.stock <= c.stock_minimo],
        por_categoria=por_categoria,
    )


if __name__ == "__main__":
    app.run(debug=True)