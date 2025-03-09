from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore

from app.routers.watch import WatchHandler


# pytest -sk "test_WatchHandler_fill_mark_price"
def test_WatchHandler_fill_mark_price():
    handler = WatchHandler(Spot(base_url="https://api.binance.com"), UMFutures())
    handler.handle_mark_price(["BTCUSDT"])