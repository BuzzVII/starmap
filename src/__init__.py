from flask import Flask, request, redirect, url_for


def create_app():
    app = Flask(__name__, template_folder='templates', static_url_path='', static_folder='static')

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
