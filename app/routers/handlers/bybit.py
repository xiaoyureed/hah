from decimal import Decimal

from pybit.unified_trading import HTTP  # type: ignore

from app.models.watch_models import (
    BasicPrice,
    BybitRespWrapper,
    BybitTicker,
    MarkPrice,
    SymbolRowReq,
)
from app.routers.handlers.watch_handler_interface import IWatchHandler
from app.utils.log_util import Lg


class BybitWatchHandler(IWatchHandler):
    def __init__(self, params: SymbolRowReq | None = None):
        super().__init__(
            top_n=params.topN if params else None,
            direction=params.direction if params else None,
            symbols=params.symbols if params else None,
        )

        self.session = HTTP()

    def _get_prices(self, cate: str) -> list[BasicPrice]:
        res: list[BasicPrice] = []

        tickers: list[BybitTicker] = []
        ts = 0
        if self.symbols:
            for sy in self.symbols:
                res_wrapper = BybitRespWrapper.model_validate(
                    self.session.get_tickers(category=cate, symbol=sy)
                )

                if not ts:
                    ts = res_wrapper.time

                if res_wrapper and res_wrapper.result and res_wrapper.result.list:
                    one = res_wrapper.result.list[0]
                    tickers.append(one)
        else:
            wrapper = BybitRespWrapper.model_validate(
                self.session.get_tickers(category=cate)
            )
            if not ts:
                ts = wrapper.time

            if wrapper and wrapper.result and wrapper.result.list:
                tickers = wrapper.result.list

        for ele in tickers:
            market = "现货" if cate == "spot" else "永续"

            bid = None
            ask = None
            try:
                bid = Decimal(ele.bid1Price)
                ask = Decimal(ele.ask1Price)
            except Exception as e:
                Lg.error(
                    f"bybit best price invalid, bid1Pricd: {ele.bid1Price}, ask2Price: {ele.ask1Price}, symbol: {ele.symbol}. ex: {e}"
                )

            if bid and ask:
                res.append(
                    (
                        ele.symbol,
                        f"Bybit-{market}",
                        Decimal(ele.bid1Price),
                        Decimal(ele.ask1Price),
                        ts,
                    )
                )

        return res

    def get_spot(self) -> list[BasicPrice]:
        return self._get_prices("spot")

    def get_swap(self) -> list[BasicPrice]:
        return self._get_prices("linear")

    def get_mark_price(self) -> list[MarkPrice]:
        return []
