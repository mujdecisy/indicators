import yfinance as yf
from datetime import datetime
import diti
from typing import Tuple
import urllib


class ActionDiti:
    from_: str
    to: str

    def __init__(self, from_, to) -> None:
        self.from_ = from_
        self.to = to


class ChartActions:
    prev: ActionDiti
    next_: ActionDiti
    zoomin: ActionDiti
    zoomout: ActionDiti


index_mapping = {
    "TRY=X": {"name": "USD"},
    "XU100.IS": {"name": "BIST"},
    "GC=FxTRY=X": {"name": "GOLD"},
    "BTC-USDxTRY=X": {"name": "BTC"},
}


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
        try:
            getattr(data.index, "floor")
        except AttributeError:
            raise ValueError("No data found for")
        data.index = data.index.floor("H")
        data = data.groupby(data.index).mean()
    elif data_interval == "15m":
        try:
            getattr(data.index, "floor")
        except AttributeError:
            raise ValueError("No data found for")
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

    ditis = [
        diti.diti_op(
            e.timestamp(),
            [diti.DitiOpTimezoneChange(diti.DitiTimezone.EUROPE__ISTANBUL)],
        ).isoformat()
        for e in data.index.to_list()
    ]

    data = {
        index_mapping[k[1]]["name"]: v for k, v in data.to_dict(orient="list").items()
    }

    return ditis, data


def prepare_chart_actions(
    from_dt: datetime, to_dt: datetime, step_size: int
) -> ChartActions:
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

    chart_actions = ChartActions()
    chart_actions.prev = ActionDiti(prev_from_diti, prev_to_diti)
    chart_actions.next = ActionDiti(next_from_diti, next_to_diti)
    chart_actions.zoomin = ActionDiti(zin_from_diti, zin_to_diti)
    chart_actions.zoomout = ActionDiti(zout_from_diti, zout_to_diti)

    return chart_actions


def prepare_detail_page_data(
    asset_code: str, from_diti: str, to_diti: str, data_interval: str, data_type: str
) -> Tuple[list, dict]:
    assets_to_download = f"{asset_code} {'TRY=X' if asset_code in ['GC=F', 'BTC-USD'] else ''}"

    data = yf.download(
        assets_to_download,
        start=datetime.fromisoformat(from_diti),
        end=datetime.fromisoformat(to_diti),
        interval=data_interval,
    )
    if len(data) < 1:
        raise ValueError(f"No data found between [{from_diti}] - [{to_diti}]")

    if asset_code in ['GC=F', 'BTC-USD']:
        data = data[[(data_type, "TRY=X"), (data_type, asset_code)]]
    else:
        data = data[[(data_type)]]

    if data_interval == "1h":
        data.index = data.index.floor("H")
        data = data.groupby(data.index).mean()
    elif data_interval == "15m":
        data.index = data.index.floor("15T")
        data = data.groupby(data.index).mean()
    data = data.dropna()

    if len(data) < 1:
        raise ValueError(f"No data found between [{from_diti}] - [{to_diti}]")

    if asset_code == "GC=F":
        data[(data_type, "GC=FxTRY=X")] = (
            data[(data_type, "GC=F")] * data[(data_type, "TRY=X")]
        )
        asset_code = "GC=FxTRY=X"
    elif asset_code == "BTC-USD":
        data[(data_type, "BTC-USDxTRY=X")] = (
            data[(data_type, "BTC-USD")] * data[(data_type, "TRY=X")]
        )
        asset_code = "BTC-USDxTRY=X"

    if asset_code in ['GC=F', 'BTC-USD']:
        data = data[
            [
                (data_type, asset_code),
            ]
        ]
    else:
        data = data[
            [
                (data_type),
            ]
        ]

    ditis = [
        diti.diti_op(
            e.timestamp(),
            [diti.DitiOpTimezoneChange(diti.DitiTimezone.EUROPE__ISTANBUL)],
        ).isoformat()
        for e in data.index.to_list()
    ]

    data = {
        index_mapping[asset_code]["name"]: v for k, v in data.to_dict(orient="list").items()
    }

    return ditis, data
