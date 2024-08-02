from flask import Flask

app = Flask(__name__)


def init_app():
    from .views import register_blueprint

    register_blueprint(app)
    return app
