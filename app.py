import json
from flask import Flask, redirect, render_template, request
from flask_basicauth import BasicAuth
import os
import diti
from datetime import datetime
import urllib

from helper import get_initial_filters, prepare_chart_actions, prepare_index_page_data

app = Flask(__name__)
MODE = os.environ.get("APP_MODE", "debug")

print(f"MODE = {MODE}")

app.config["BASIC_AUTH_USERNAME"] = os.environ.get("APP_BA_USERNAME", "")
app.config["BASIC_AUTH_PASSWORD"] = os.environ.get("APP_BA_PASSWORD", "")

basic_auth = BasicAuth(app)

@app.errorhandler(Exception)
def error_handler(err):
    return render_template("error.html", error_message = str(err))

@app.route("/")
@basic_auth.required
def index():
    init_from, init_to = get_initial_filters()

    data_type = "Close"
    from_diti = request.args.get("fDiti", init_from)
    to_diti = request.args.get("tDiti", init_to)

    diff = diti.diti_calcs.diff(
        datetime.fromisoformat(from_diti),
        datetime.fromisoformat(to_diti),
        diti.DitiParts.HOURS,
    )

    if diff > 8 * 24:
        data_interval = "1d"
    elif diff > 2 * 24:
        data_interval = "1h"
    else:
        data_interval = "15m"

    diti_list, data_dict = prepare_index_page_data(
        from_diti, to_diti, data_interval, data_type
    )

    data_list = [{"name": k, "data": v} for k, v in data_dict.items()]

    from_dt = datetime.fromisoformat(from_diti)
    to_dt = datetime.fromisoformat(to_diti)

    step_size = int(diff / 4)

    chart_actions = prepare_chart_actions(from_dt, to_dt, step_size)

    return render_template(
        "index.html",
        diti_list=json.dumps(diti_list),
        data_list=json.dumps(data_list),
        prev_url_params=f"fDiti={chart_actions.prev.from_}&tDiti={chart_actions.prev.to}",
        next_url_params=f"fDiti={chart_actions.next.from_}&tDiti={chart_actions.next.to}",
        zin_url_params=f"fDiti={chart_actions.zoomin.from_}&tDiti={chart_actions.zoomin.to}",
        zout_url_params=f"fDiti={chart_actions.zoomout.from_}&tDiti={chart_actions.zoomout.to}",
        to_diti=to_diti,
    )


if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=(MODE == "debug"))
