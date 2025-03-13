from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore

from app.routers.handlers.binance import (
    BinanceWatchHandler,
)


# pytest -sk "test_WatchHandler_fill_mark_price"
def test_WatchHandler_fill_mark_price():
    handler = BinanceWatchHandler()(Spot(base_url="https://api.binance.com"), UMFutures())
    handler.handle_mark_price(["BTCUSDT"])