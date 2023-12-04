import json
from flask import Flask, render_template, request
from flask_basicauth import BasicAuth
import yfinance as yf
import os

app = Flask(__name__)
MODE = os.environ.get("APP_MODE", "debug")

app.config['BASIC_AUTH_USERNAME'] = os.environ.get("APP_BA_USERNAME", "")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get("APP_BA_PASSWORD", "")

basic_auth = BasicAuth(app)

@app.route("/")
@basic_auth.required
def index():
    data_type = request.args.get("dataType", "Close")
    data_period = request.args.get("dataPeriod", "1mo")
    data_interval = request.args.get("dataInterval", "1d")

    data = yf.download(
        "TRY=X XU100.IS GC=F BTC-USD", period=data_period, interval=data_interval
    )
    data = data[
        [
            (data_type, "TRY=X"),
            (data_type, "XU100.IS"),
            (data_type, "GC=F"),
            (data_type, "BTC-USD"),
        ]
    ]
    if data_interval == "1h":
        data.index = data.index.floor("H")
        data = data.groupby(data.index).mean()
    elif data_interval == "15m":
        data.index = data.index.floor("15T")
        data = data.groupby(data.index).mean()
    data = data.dropna()
    data[(data_type, "GC=FxTRY=X")] = (
        data[(data_type, "GC=F")] * data[(data_type, "TRY=X")]
    )
    data[(data_type, "BTC-USDxTRY=X")] = (
        data[(data_type, "BTC-USD")] * data[(data_type, "TRY=X")]
    )

    data = data[
        [
            (data_type, "TRY=X"),
            (data_type, "XU100.IS"),
            (data_type, "GC=FxTRY=X"),
            (data_type, "BTC-USDxTRY=X"),
        ]
    ]
    data = data / data.iloc[0]

    index_mapping = {
        "TRY=X": {"name": "USD", "color": "red"},
        "XU100.IS": {"name": "BIST", "color": "blue"},
        "GC=FxTRY=X": {"name": "GOLD", "color": "green"},
        "BTC-USDxTRY=X": {"name": "BTC", "color": "purple"},
    }

    dates = [e.strftime("%m-%d %H:%M") for e in data.index.to_list()]
    data = data.to_dict(orient="list")
    json_data = []
    for k, v in data.items():
        json_data.append(
            {
                "label": index_mapping[k[1]]["name"],
                "data": v,
                "borderColor": index_mapping[k[1]]["color"],
            }
        )

    return render_template(
        "index.html", dates=json.dumps(dates), data=json.dumps(json_data)
    )

if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=(MODE=="debug"))
