from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore
from fastapi import APIRouter, Depends

from app.models.exchange import BookOptions, Exchange, Market
from app.models.http_model import Resp
from app.routers.handlers.watch_handler import WatchHandler
from app.routers.handlers.watch_models import SymbolRowReq

router = APIRouter(prefix="/api/watch", tags=["watch"])


@router.get("/book-tickers")
def watch(params: SymbolRowReq = Depends()):
    symbolsReq = params.symbols

    symbols: list[str] | None = None
    if symbolsReq and symbolsReq.strip():
        symbols = [s.strip().upper() for s in symbolsReq.split(",")]

    handler = WatchHandler(Spot(base_url="https://api.binance.com"), UMFutures())

    # 现货
    spot = handler.get_spot_price(symbols=symbols)
    # 合约
    fu = handler.get_future_price(symbols=symbols)

    handler.init_res(symbols, spot, fu, params.direction)

    handler.handle_top_n(params.topN)
    handler.handle_mark_price(symbols)

    return Resp.ok(handler.res)


@router.get("/book-options")
def gen_book_options():
    """生成盘口可选项"""
    res = []
    for market in Market:
        for exchange in Exchange:
            option = BookOptions(
                id=f"{exchange.name}-{market.name}",
                label=f"{exchange.value}-{market.value}",
            )
            res.append(option)

    return Resp.ok(res)
