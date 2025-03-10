from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore

from app.routers.handlers.watch_models import (
    MarkPrice,
    SymbolRow,
    TradeDirection,
)


class WatchHandler:
    def __init__(self, spot_client: Spot, um_futures_client: UMFutures):
        self.spot_client = spot_client
        self.um_futures_client = um_futures_client
        self.res: list[SymbolRow] = []

    def get_spot_price(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[list[str]] = None,
    ) -> list[tuple[str, Decimal, Decimal]]:
        """Spot market, 最优挂单 (买一卖一)

        Args:
            symbol (Optional[str], optional): the pair. Defaults to None.
            symbols (Optional[list[str]], optional): the pairs. Defaults to None.

        Returns:
            symbol 买一价，卖一价
        """

        tickers: list[dict] = self.spot_client.book_ticker(
            symbol=symbol, symbols=symbols
        )
        # logging.info(spot_client.book_ticker(symbols=["BTCUSDT", "BNBUSDT"]))

        if tickers is None:
            raise Exception("spot - 获取市场最优挂单失败")

        res = []

        for item in tickers:
            symbol = item.get("symbol")
            bid_price = item.get("bidPrice")
            ask_price = item.get("askPrice")
            if symbol is not None and bid_price is not None and ask_price is not None:
                if float(bid_price) > 0 and float(ask_price) > 0:
                    res.append(
                        (
                            symbol,
                            Decimal(bid_price).normalize(),
                            Decimal(ask_price).normalize(),
                        )
                    )

        return res

    def get_future_price(
        self, symbols: Optional[list[str]] = None
    ) -> list[tuple[str, Decimal, Decimal, int]]:
        """期货市场最优挂单 (买一卖一)

        Args:
            symbols (Optional[list[str]], optional): 交易对集合

        Returns:
            symbol, 买一价，卖一价
        """

        tickers = []
        if symbols is None:
            tickers = self.um_futures_client.book_ticker()
        else:
            for sy in symbols:
                ticker = self.um_futures_client.book_ticker(symbol=sy)
                tickers.append(ticker)

        if not tickers:
            raise Exception("future - 获取市场最优挂单失败")

        res = []

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
                            Decimal(bid_price).normalize(),
                            Decimal(ask_price).normalize(),
                            time,
                        )
                    )

        return res

    def init_res(
        self,
        symbols: list[str] | None,
        spot: list[tuple[str, Decimal, Decimal]],
        fu: list[tuple[str, Decimal, Decimal, int]],
        direction: Optional[str] = None,
    ):
        res: list[SymbolRow] = []

        # if no symbols specified in the params
        # then take all symbols from the spot data
        if not symbols:
            symbols = [s[0] for s in spot]

        for sy in symbols:
            for s_symbol, s_bid, s_ask in spot:
                if sy != s_symbol:
                    continue

                for f_symbol, f_bid, f_ask, f_ts in fu:
                    if sy != f_symbol:
                        continue

                    row = SymbolRow(
                        symbol=sy,
                        bookA="spot",
                        bidPriceA=s_bid,
                        askPriceA=s_ask,
                        bookB="future",
                        bidPriceB=f_bid,
                        askPriceB=f_ask,
                        timestamp=f_ts,
                    )

                    # 盘差: ( 卖 - 买 )/ 卖
                    # row.pc = self._adjust_precision(
                    #     (
                    #         abs(
                    #             row.askPriceA
                    #             + row.askPriceB
                    #             - row.bidPriceA
                    #             - row.bidPriceB
                    #         )
                    #         / (row.askPriceA + row.askPriceB)
                    #     )
                    #     * 100
                    # )

                    self.calc_direction(row)

                    # 若传递direction，则根据direction过滤
                    if direction and direction.strip():
                        if not row.direction or (
                            row.direction.upper() != direction.upper()
                        ):
                            continue

                    res.append(row)

                    break
                break

        self.res = res

    def _adjust_precision(self, val: Decimal):
        if not val:
            return Decimal("0")

        return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP).normalize()

    def calc_direction(self, row: SymbolRow):
        # calc the direction
        # a -> b, b买一 - a卖一
        row.diffAb = ((row.bidPriceB - row.askPriceA) / row.bidPriceB) * 100
        # keep 6 decimal places
        row.diffAb = self._adjust_precision(row.diffAb)

        # b -> a
        row.diffBa = ((row.bidPriceA - row.askPriceB) / row.bidPriceA) * 100
        row.diffBa = self._adjust_precision(row.diffBa)

        if not row.diffAb:
            return
        if row.diffAb > 0:
            # a 买 b 卖
            row.direction = TradeDirection.A_B.name
            row.directionDesc = TradeDirection.A_B.value

            # 清仓差价 (a 卖 b买) : (b 卖1 - a 买1) / b 卖 1
            row.qccj = self._adjust_precision(
                (row.askPriceB - row.bidPriceA) / row.askPriceB * 100
            )

        elif row.diffAb < 0:
            # a 卖 b 买
            row.direction = TradeDirection.B_A.name
            row.directionDesc = TradeDirection.B_A.value

            # 清仓差价 (a 买 b卖) : (a 卖1 - b 买1) / a 卖 1
            row.qccj = self._adjust_precision(
                (row.askPriceA - row.bidPriceB) / row.askPriceA * 100
            )

        else:
            row.direction = "equal"
            row.directionDesc = "相等"

        # 盘差 (清仓差价-推荐差价)/清仓差价)
        if (
            row.qccj
            and not row.qccj.is_zero()
            and row.diffAb
            and row.diffBa
            and row.direction != "equal"
        ):
            row.pc = self._adjust_precision(
                abs(
                    (
                        row.qccj
                        - (
                            row.diffBa
                            if row.direction == TradeDirection.B_A.name
                            else row.diffAb
                        )
                    )
                    / row.qccj
                )
                * 100
            )

    def handle_mark_price(self, symbols: Optional[list[str]]):
        prices: list[MarkPrice] = []
        if not symbols:
            for ele in self.um_futures_client.mark_price():
                parsed = MarkPrice.model_validate(ele)
                prices.append(parsed)
        else:
            for sy in symbols:
                price = MarkPrice.model_validate(self.um_futures_client.mark_price(sy))
                prices.append(price)

        if not prices:
            return

        for row in self.res:
            for p in prices:
                if p.symbol == row.symbol:
                    row.lastFundingRate = self._adjust_precision(
                        p.lastFundingRate * 100
                    )
                    row.zscj = self._adjust_precision(
                        ((p.markPrice - p.indexPrice) / p.markPrice) * 100
                    )
                    break

    def handle_top_n(self, top_n: int | None):
        # 排序
        def sort_attr(x: SymbolRow):
            if x.direction == TradeDirection.A_B.name:
                return x.diffAb
            else:
                return x.diffBa

        res_sorted = sorted(self.res, key=sort_attr, reverse=True)

        if top_n and top_n > 0:
            if top_n < len(res_sorted):
                res_sorted = res_sorted[:top_n]

        self.res = res_sorted
