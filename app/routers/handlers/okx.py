from decimal import Decimal

from okx.MarketData import MarketAPI  # type: ignore

from app.models.watch_models import (
    BasicPrice,
    MarkPrice,
    RespWrapper,
    SymbolRowReq,
    Ticker,
)
from app.routers.handlers.watch_handler_interface import IWatchHandler


class OkxWatchHandler(IWatchHandler):
    def __init__(self, params: SymbolRowReq):
        super().__init__(
            params.topN if params else None,
            params.direction if params else None,
            params.symbols if params else None,
        )
        self.market_api = MarketAPI()

    def _get_prices(self, instType: str) -> list[BasicPrice]:
        res: list[BasicPrice] = []

        tickers: list[Ticker] = []
        if self.symbols:
            for sy in self.symbols:
                # todo
                wrap = RespWrapper[Ticker].model_validate(
                    self.market_api.get_ticker(sy + "-" + instType)
                )
                tickers.append(wrap.data[0])
        else:
            wrap = RespWrapper[Ticker].model_validate(
                self.market_api.get_tickers(instType=instType)
            )
            tickers += wrap.data

        for ele in tickers:
            if ele.bidPx and ele.askPx and ele.ts:
                symbol: str = ele.symbol  # type: ignore

                market = ""

                # spot : "ZIL-USDT-SWAP"
                # swap: "ZIL-USDT"
                if instType == "SWAP":
                    symbol = symbol.rsplit("-", 1)[0]
                    market = "永续合约"
                elif instType == "SPOT":
                    market = "现货"
                symbol = symbol.replace("-", "", 1)

                to_add = (
                    symbol,
                    f"欧易-{market}",
                    Decimal(ele.bidPx),
                    Decimal(ele.askPx),
                    int(ele.ts),
                )
                res.append(to_add)  # type: ignore

        return res

    def get_spot(self):
        return self._get_prices("SPOT")

    def get_swap(self) -> list[BasicPrice]:
        return self._get_prices("SWAP")

    def get_mark_price(self) -> list[MarkPrice]:
        return []
