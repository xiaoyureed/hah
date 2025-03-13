from decimal import Decimal

from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore

from app.models.watch_models import BasicPrice, MarkPrice, SymbolRowReq
from app.routers.handlers.watch_handler_interface import IWatchHandler


class BinanceWatchHandler(IWatchHandler):
    def __init__(self, params: SymbolRowReq):
        super().__init__(params.topN, params.direction, params.symbols)
        self.spot_client = Spot(base_url="https://api.binance.com")
        self.um_futures_client = UMFutures()


    def get_spot(
        self,
    ) -> list[BasicPrice]:
        """Spot market, 最优挂单 (买一卖一)

        Args:
            symbol (Optional[str], optional): the pair. Defaults to None.
                ',' supported, e.g. 'BTCUSDT,BNBUSDT'

        Returns:
            symbol 买一价，卖一价
        """
        tickers: list[dict] = self.spot_client.book_ticker(symbols=self.symbols)
        # logging.info(spot_client.book_ticker(symbols=["BTCUSDT", "BNBUSDT"]))

        if tickers is None:
            raise Exception("spot - 获取市场最优挂单失败")

        res: list[BasicPrice] = []

        for item in tickers:
            symbol = item.get("symbol")
            bid_price = item.get("bidPrice")
            ask_price = item.get("askPrice")
            if symbol is not None and bid_price is not None and ask_price is not None:
                if float(bid_price) > 0 and float(ask_price) > 0:
                    res.append(
                        (
                            symbol,
                            "币安-现货",
                            Decimal(bid_price).normalize(),
                            Decimal(ask_price).normalize(),
                            0,
                        )
                    )

        return res

    def get_swap(self) -> list[BasicPrice]:
        """期货市场最优挂单 (买一卖一)

        Args:
            symbols (Optional[list[str]], optional): 交易对集合

        Returns:
            symbol, 买一价，卖一价
        """

        tickers = []
        if self.symbols is None:
            tickers = self.um_futures_client.book_ticker()
        else:
            for sy in self.symbols:
                ticker = self.um_futures_client.book_ticker(symbol=sy)
                tickers.append(ticker)

        if not tickers:
            raise Exception("swap - 获取市场最优挂单失败")

        res: list[BasicPrice] = []

        for item in tickers:
            symbol = item.get("symbol")
            bid_price = item.get("bidPrice")
            ask_price = item.get("askPrice")
            time = item.get("time")
            if symbol is not None and bid_price is not None and ask_price is not None:
                if float(bid_price) > 0 and float(ask_price) > 0:
                    res.append(
                        (
                            symbol,
                            "币安-永续合约",
                            Decimal(bid_price).normalize(),
                            Decimal(ask_price).normalize(),
                            time,
                        )
                    )

        return res

    def get_mark_price(self):
        symbols = self.symbols
        prices = []
        if not symbols:
            for ele in self.um_futures_client.mark_price():
                parsed = MarkPrice.model_validate(ele)
                prices.append(parsed)
        else:
            for sy in symbols:
                price = MarkPrice.model_validate(self.um_futures_client.mark_price(sy))
                prices.append(price)

        return prices
