from flask import Flask
from controller import controller
from db import db


def create_app():
    app = Flask(__name__)

    app.register_blueprint(controller)

    # Init SqlAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:mysecretpassword@localhost:5432"
    )
    db.init_app(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5001, host="0.0.0.0")
