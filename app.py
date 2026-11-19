import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tienda.db")

db = SQLAlchemy(app)


@app.route("/")
def inicio():
    return "Tienda PC funcionando"


if __name__ == "__main__":
    app.run(debug=True)