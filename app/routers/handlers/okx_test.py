
from objprint import op

from app.routers.handlers.okx import OkxWatchHandler


def test_okx():
    
    handler = OkxWatchHandler(None)
    prices = handler.get_spot()
    op(prices)
