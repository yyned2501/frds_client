from flask import Flask

def register_blueprint(app: Flask):
    from .index import index
