import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user

from models import Usuario, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tienda.db")

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Iniciá sesión para continuar."

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

with app.app_context():
    db.create_all()


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


if __name__ == "__main__":
    app.run(debug=True)