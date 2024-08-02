from app.init import app
from flask import request

states = {}


@app.route("/", methods=["POST"])
def index():
    state = {k: v[0] for k, v in request.form.lists()}
    states[state["userid"]] = state
    return states


@app.route("/", methods=["GET"])
def index_():
    return states
