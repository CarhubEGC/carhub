from click import ClickException
from flask import Flask
from sqlalchemy import inspect

from fakenodo.database import DepositionService, deposits
from fakenodo.routes import create_depositions_blueprint


def create_app():
    app = Flask(__name__)
    store = DepositionService.from_environment()
    app.register_blueprint(create_depositions_blueprint(store))

    @app.cli.command("init-db")
    def init_db():
        """Create the FakeNodo schema in an empty database."""
        deposits.create(store.engine, checkfirst=True)
        columns = {column["name"] for column in inspect(store.engine).get_columns(deposits.name)}
        if missing := set(deposits.c.keys()) - columns:
            raise ClickException(f"The deposits table needs a migration for: {', '.join(sorted(missing))}")

    return app
