from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Generic, Optional, TypeAlias, TypeVar

from objprint import add_objprint  # type: ignore
from pydantic import BaseModel, computed_field

from app.errors import biz_error

# -------------------------------------------- models for our watching api

# (symbol, market_name, bid, ask, timestamp)
BasicPrice: TypeAlias = tuple[str, str, Decimal, Decimal, int]


class SymbolRow(BaseModel):
    symbol: str

    # 交易所&市场标识
    em_a: str | None = None
    em_b: str | None = None

    bookA: str  # 盘口 a
    bidPriceA: Decimal  # 最高买入价格
    askPriceA: Decimal  # 最低卖出价格

    bookB: str  # 盘口b
    bidPriceB: Decimal
    askPriceB: Decimal

    # 开仓差价
    diffAb: Decimal | None = None  # A -> B
    diffBa: Decimal | None = None  # B -> A

    # 推荐方向
    direction: str | None = None
    directionDesc: str | None = None

    # 清仓差价, opposite to the direction
    qccj: Decimal | None = None

    timestamp: int

    # 盘差 (越小, 深度越好, 流动性越好)
    pc: Decimal | None = None

    # ---------------- 合约 -----------------

    # 资金费率 ,最近更新的资金费率
    lastFundingRate: Decimal | None = None
    # 指数差价
    zscj: Decimal | None = None

    # ---------------- 合约 -----------------


class SymbolRowReq(BaseModel):
    """A row in the table for watching"""

    # 多个则用 ','分割
    symbols: Optional[str] = None
    direction: Optional[str] = None
    # 前 n 条
    topN: int = 200
    # 盘口 a, ',' supported
    bookA: Optional[str] = None
    # 盘口 B, ',' supported
    bookB: Optional[str] = None


class TradeDirection(Enum):
    """trading direction"""

    A_B = "A买B卖"
    B_A = "A卖B买"



class BookOptions(BaseModel):
    """盘口-可选项"""

    id: str
    label: str

# ----------------------------------------------------------------- bybit models

class BybitTicker(BaseModel):
    ask1Price: Decimal
    bid1Price: Decimal
    symbol: str
    

class BybitResult(BaseModel):
    category: str
    list: list[BybitTicker]



class BybitRespWrapper(BaseModel):
    retCode: int
    retExtInfo: dict
    retMsg: str
    time: int
    result: BybitResult

# ------------------------------------------------------------------  okx models


T = TypeVar("T")


class RespWrapper(BaseModel, Generic[T]):
    code: str
    msg: str
    data: list[T]


class Ticker(BaseModel):
    # LTC-USD-SWAP
    instId: str
    # 卖 1
    askPx: str
    bidPx: str
    # ms
    ts: str

    @computed_field
    def symbol(self) -> str:
        # instId = self.instId
        # if instId and instId.strip():
        #     return instId.rsplit("-", 1)[0]
        # return ""
        return self.instId


# --------------------------------------------- binance model

class MarkPrice(BaseModel):
    symbol: str
    # 标记价格
    markPrice: Decimal
    # 指数价格
    indexPrice: Decimal
    # 最近更新的资金费率
    lastFundingRate: Decimal
    # 更新时间
    time: int



# ----------------------------------------------------------  todo


@add_objprint
class ExchangeMarket:
    """交易所-市场"""

    def __init__(self, id: str):
        # avoid circular import
        from app.config import datasource

        if not id or not id.strip():
            raise ValueError("id is empty")

        e, m = id.split("-", maxsplit=1)
        self.exchange = e
        self.market = m

        exchanges: list = datasource.get("exchanges")  # type: ignore
        handler_cls = next(
            (ele.get("handler") for ele in exchanges if ele.get("id") == self.exchange),
            None,
        )
        if not handler_cls:
            raise biz_error.of(
                f"can't resolve handler, exchange: {self.exchange}, market: {self.market}"
            )

        self.handler_cls = handler_cls

    def __eq__(self, other):
        if not isinstance(other, ExchangeMarket):
            return False

        return other.exchange == self.exchange and other.market == self.market

    def get_mark_price(self, params: SymbolRowReq) -> list[MarkPrice]:
        """only for swap market"""

        if self.market != "swap":
            return []
        return self.handler_cls(params).get_mark_price()
        # get_mark_price_caller = methodcaller("get_mark_price")
        # return get_mark_price_caller(self.handler_cls())

    def get_basic_price(self, params: SymbolRowReq):
        handler = self.handler_cls(params)
        method = getattr(handler, f"get_{self.market}", None)
        if not method:
            raise biz_error.of(
                f"can't resolve handler method, exchange: {self.exchange}, market: {self.market}"
            )
        prices: list[BasicPrice] = method()
        return prices


class WatchMapping:
    def __init__(self, a: ExchangeMarket, b: ExchangeMarket):
        self.a = a
        self.b = b

    def get_watch_res(self, params: SymbolRowReq):
        res = []

        source_a = self.a.get_basic_price(params)
        source_b = self.b.get_basic_price(params)

        # if no symbols specified in the params
        # then take all symbols from the spot data
        symbols = params.symbols if params.symbols else [ele[0] for ele in source_a]

        for sy in symbols:
            a = next((x for x in source_a if x[0] == sy), None)
            b = next((x for x in source_b if x[0] == sy), None)
            if not a or not b:
                continue

            (a_symbol, a_em, a_bid, a_ask, a_ts) = a
            (b_symbol, b_em, b_bid, b_ask, b_ts) = b

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
                bookA=a_em,
                bidPriceA=a_bid,
                askPriceA=a_ask,
                bookB=b_em,
                bidPriceB=b_bid,
                askPriceB=b_ask,
                timestamp=ts,
            )

            self.calc_direction(row)

            # 若传递direction，则根据direction过滤
            if params.direction and params.direction.strip():
                if row.direction and row.direction.upper() == params.direction.upper():
                    res.append(row)
            else:
                res.append(row)

        resolved_top_n = self.get_top_n(res, params.topN)

        # mark_prices_a = self.a.get_mark_price(params)
        # mark_prices_b = self.b.get_mark_price(params)

        # todo
        #
        # for row in resolved_top_n:
        #     price = next((x for x in prices if x.symbol == row.symbol), None)
        #     if price:
        #         # 资金费率
        #         row.lastFundingRate = self._adjust_precision(
        #             price.lastFundingRate * 100
        #         )
        #         row.zscj = self._adjust_precision(
        #             ((price.markPrice - price.indexPrice) / price.markPrice) * 100
        #         )

        return resolved_top_n

    def get_top_n(self, rows: list[SymbolRow], top_n: int) -> list[SymbolRow]:
        # 排序
        def sort_attr(x: SymbolRow):
            if x.direction == TradeDirection.A_B.name:
                return x.diffAb
            else:
                return x.diffBa

        res_sorted = sorted(rows, key=sort_attr, reverse=True)

        if top_n and top_n > 0:
            if top_n < len(res_sorted):
                res_sorted = res_sorted[:top_n]

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
