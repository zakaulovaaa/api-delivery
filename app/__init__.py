import os
from flask import Flask
from .database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])
    db.init_app(app)
    with app.test_request_context():
        db.create_all()
    import app.delivery.controllers as delivery
    app.register_blueprint(delivery.module)
    return app
