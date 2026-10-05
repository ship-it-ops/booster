from flask import Flask

from teamdocs import auth, db, docs, files
from teamdocs.config import load_config


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        app.config.update(overrides)
    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(docs.bp)
    app.register_blueprint(files.bp)
    return app
