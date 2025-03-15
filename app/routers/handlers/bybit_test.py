

from objprint import op

from app.routers.handlers.bybit import BybitWatchHandler


def test_bybit():
    handler = BybitWatchHandler()
    res = handler._get_prices("spot")
    op(res)