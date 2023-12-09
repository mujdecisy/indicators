import yfinance as yf
from datetime import datetime
import diti
from typing import Tuple


def get_initial_filters() -> Tuple[str, str]:
    now = diti.diti_op(
        datetime.now(),
        [
            diti.DitiOpTimezoneChange(diti.DitiTimezone.EUROPE__ISTANBUL),
            diti.DitiOpTailOf(diti.DitiParts.DAYS),
        ],
    )
    sevendays_ago = diti.diti_op(
        now,
        [
            diti.DitiOpAdd(diti.DitiParts.DAYS, -7),
            diti.DitiOpHeadOf(diti.DitiParts.DAYS),
        ],
    )
    return sevendays_ago.isoformat(), now.isoformat()


def prepare_index_page_data(
    from_diti: str, to_diti: str, data_interval: str, data_type: str
) -> Tuple[list, dict]:
    data = yf.download(
        "TRY=X XU100.IS GC=F BTC-USD",
        start=datetime.fromisoformat(from_diti),
        end=datetime.fromisoformat(to_diti),
        interval=data_interval,
    )
    if len(data) < 1:
        raise ValueError(f"No data found between [{from_diti}] - [{to_diti}]")

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
    elif data_interval == "15T":
        data.index = data.index.floor("15T")
        data = data.groupby(data.index).mean()
    data = data.dropna()
    if len(data) < 1:
        raise ValueError(f"No data found between [{from_diti}] - [{to_diti}]")


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
        "TRY=X": {"name": "USD"},
        "XU100.IS": {"name": "BIST"},
        "GC=FxTRY=X": {"name": "GOLD"},
        "BTC-USDxTRY=X": {"name": "BTC"},
    }

    ditis = [
        diti.diti_op(
            e.timestamp(),
            [diti.DitiOpTimezoneChange(diti.DitiTimezone.EUROPE__ISTANBUL)],
        ).isoformat()
        for e in data.index.to_list()
    ]

    data = {index_mapping[k[1]]["name"]: v for k, v in data.to_dict(orient="list").items()}

    return ditis, data
