from flask import Flask

from fakenodo.routes import create_depositions_blueprint
from fakenodo.services import DepositionStore


def create_app():
    app = Flask(__name__)
    app.register_blueprint(create_depositions_blueprint(DepositionStore()))
    return app
