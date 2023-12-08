import json
from flask import Flask, render_template, request
from flask_basicauth import BasicAuth
import os
import diti
from datetime import datetime
import urllib

from helper import get_initial_filters, prepare_index_page_data

app = Flask(__name__)
MODE = os.environ.get("APP_MODE", "debug")

print(f"MODE = {MODE}")

app.config["BASIC_AUTH_USERNAME"] = os.environ.get("APP_BA_USERNAME", "")
app.config["BASIC_AUTH_PASSWORD"] = os.environ.get("APP_BA_PASSWORD", "")

basic_auth = BasicAuth(app)


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
        data_interval = "15T"

    diti_list, data_dict = prepare_index_page_data(
        from_diti, to_diti, data_interval, data_type
    )
    data_list = [{"name": k, "data": v} for k, v in data_dict.items()]

    from_dt = datetime.fromisoformat(from_diti)
    to_dt = datetime.fromisoformat(to_diti)

    step_size = int(diff / 4)

    prev_from_diti = urllib.parse.quote_plus(
        diti.diti_op(
            from_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, -step_size)]
        ).isoformat()
    )
    prev_to_diti = urllib.parse.quote_plus(
        diti.diti_op(
            to_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, -step_size)]
        ).isoformat()
    )
    next_from_diti = urllib.parse.quote_plus(
        diti.diti_op(
            from_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, step_size)]
        ).isoformat()
    )
    next_to_diti = urllib.parse.quote_plus(
        diti.diti_op(
            to_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, step_size)]
        ).isoformat()
    )
    zin_from_diti = urllib.parse.quote_plus(
        diti.diti_op(
            from_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, step_size)]
        ).isoformat()
    )
    zin_to_diti = urllib.parse.quote_plus(
        diti.diti_op(
            to_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, -step_size)]
        ).isoformat()
    )
    zout_from_diti = urllib.parse.quote_plus(
        diti.diti_op(
            from_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, -step_size)]
        ).isoformat()
    )
    zout_to_diti = urllib.parse.quote_plus(
        diti.diti_op(
            to_dt, [diti.DitiOpAdd(diti.DitiParts.HOURS, step_size)]
        ).isoformat()
    )

    return render_template(
        "index.html",
        diti_list=json.dumps(diti_list),
        data_list=json.dumps(data_list),
        prev_url_params=f"fDiti={prev_from_diti}&tDiti={prev_to_diti}",
        next_url_params=f"fDiti={next_from_diti}&tDiti={next_to_diti}",
        zin_url_params=f"fDiti={zin_from_diti}&tDiti={zin_to_diti}",
        zout_url_params=f"fDiti={zout_from_diti}&tDiti={zout_to_diti}",
        to_diti=to_diti,
    )


if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=(MODE == "debug"))
