import abc
from decimal import ROUND_HALF_UP, Decimal

from app.models.watch_models import BasicPrice, MarkPrice, SymbolRow, TradeDirection


class IWatchHandler(abc.ABC):
    def __init__(self, top_n: int | None = None, direction: str | None = None, symbols: str | None = None):
        self.top_n = top_n
        self.direction = direction

        sy = None
        if symbols and symbols.strip():
            sy = [s.strip().upper() for s in symbols.split(",")]
            
        self.symbols = sy

    @abc.abstractmethod
    def get_spot(self) -> list[BasicPrice]:
        pass

    @abc.abstractmethod
    def get_swap(self) -> list[BasicPrice]:
        pass

    @abc.abstractmethod
    def get_mark_price(self) -> list[MarkPrice]:
        pass

    def get_res(
        self,
    ):
        res: list[SymbolRow] = []

        source_a = self.get_spot()
        source_b = self.get_swap()

        # if no symbols specified in the params
        # then take all symbols from the spot data
        symbols = self.symbols if self.symbols else [ele[0] for ele in source_a]

        for sy in symbols:
            a = next((x for x in source_a if x[0] == sy), None)
            b = next((x for x in source_b if x[0] == sy), None)
            if a and b:
                (a_symbol, a_bid, a_ask, a_ts) = a
                (b_symbol, b_bid, b_ask, b_ts) = b

                ts = a_ts if a_ts else b_ts
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
                row = SymbolRow(
                    symbol=sy,
                    bookA="spot",
                    bidPriceA=a_bid,
                    askPriceA=a_ask,
                    bookB="future",
                    bidPriceB=b_bid,
                    askPriceB=b_ask,
                    timestamp=ts,
                )

                self.calc_direction(row)

                # 若传递direction，则根据direction过滤
                if self.direction and self.direction.strip():
                    if (
                        row.direction
                        and row.direction.upper() == self.direction.upper()
                    ):
                        res.append(row)
                else:
                    res.append(row)

        resolved_top_n = self.get_top_n(res)

        prices = self.get_mark_price()
        for row in resolved_top_n:
            price = next((x for x in prices if x.symbol == row.symbol), None)
            if price:
                # 资金费率
                row.lastFundingRate = self._adjust_precision(
                    price.lastFundingRate * 100
                )
                row.zscj = self._adjust_precision(
                    ((price.markPrice - price.indexPrice) / price.markPrice) * 100
                )

        return resolved_top_n

    def get_top_n(self, rows: list[SymbolRow]) -> list[SymbolRow]:
        # 排序
        def sort_attr(x: SymbolRow):
            if x.direction == TradeDirection.A_B.name:
                return x.diffAb
            else:
                return x.diffBa

        res_sorted = sorted(rows, key=sort_attr, reverse=True)

        if self.top_n and self.top_n > 0:
            if self.top_n < len(res_sorted):
                res_sorted = res_sorted[: self.top_n]

        return res_sorted

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

    def _adjust_precision(self, val: Decimal):
        if not val:
            return Decimal("0")

        return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP).normalize()
