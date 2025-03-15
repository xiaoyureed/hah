from app.routers.handlers.binance import BinanceWatchHandler
from app.routers.handlers.bybit import BybitWatchHandler
from app.routers.handlers.okx import OkxWatchHandler

# @dataclass
# class Exchange:
#     pass

# @dataclass
# class Market:
#     pass


# @dataclass
# class Ds:
#     exchanges: list
#     markets: list


datasource = {
    "exchanges": [
        {"id": "binance", "label": "币安", "handler": BinanceWatchHandler},
        {"id": "okx", "label": "欧易", "handler": OkxWatchHandler},
        {
            "id": "bybit",
            "label": "Bybit",
            "handler": BybitWatchHandler,
        },
    ],
    "markets": [
        {
            "id": "swap",
            "label": "合约",
        },
        {
            "id": "spot",
            "label": "现货",
        },
    ],
}
