import os

from dotenv import load_dotenv
from flask import Flask

from models import db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tienda.db")

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def inicio():
    return "Tienda PC funcionando"


if __name__ == "__main__":
    app.run(debug=True)