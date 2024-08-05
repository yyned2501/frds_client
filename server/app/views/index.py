import datetime
from app.init import app
from flask import request, jsonify
import time

states = {}


def delete_old_states():
    for k in states:
        if time.time() - states[k]["next_time"] > 20:
            del states[k]


@app.route("/", methods=["POST"])
def index():
    state = {}
    for k, v in request.form.lists():
        v = v[0]
        try:
            state[k] = int(v)
        except ValueError:
            state[k] = v
    if "sleep" in state:
        state["next_time"] = int(time.time()) + state["sleep"]
    state["next_date"] = datetime.datetime.fromtimestamp(state["next_time"]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    states[state["userid"]] = state
    delete_old_states()
    return jsonify(states)


@app.route("/", methods=["GET"])
def index_():
    delete_old_states()
    return jsonify(states)
