from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Optional

from binance.spot import Spot  # type: ignore
from binance.um_futures import UMFutures  # type: ignore
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.exchange import BookOptions, Exchange, Market
from app.models.http_model import Resp

router = APIRouter(prefix="/api/watch", tags=["watch"])



class SymbolRow(BaseModel):
    symbol: str

    bookA: str  # 盘口 a
    bidPriceA: Decimal  # 最高买入价格
    askPriceA: Decimal  # 最低卖出价格

    bookB: str  # 盘口b
    bidPriceB: Decimal
    askPriceB: Decimal

    # 差价
    diffAb: Decimal | None = None  # A -> B
    diffBa: Decimal | None = None  # B -> A

    # 推荐方向
    direction: str | None = None
    timestamp: int

    # 盘差 , 衡量市场买卖双方出价差距 (%)
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
    # 盘口 a
    bookA: Optional[str] = None
    # 盘口 B
    bookB: Optional[str] = None


class TradeDirection(Enum):
    """trading direction"""

    A_B = "a->b"
    B_A = "b->a"


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
                    res.append((symbol, Decimal(bid_price), Decimal(ask_price)))

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
                    res.append((symbol, Decimal(bid_price), Decimal(ask_price), time))

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
                    row.pc = self._adjust_precision(
                        (
                            abs(
                                row.askPriceA
                                + row.askPriceB
                                - row.bidPriceA
                                - row.bidPriceB
                            )
                            / (row.askPriceA + row.askPriceB)
                        )
                        * 100
                    )

                    self._fill_direction(row)

                    # 若传递direction，则根据direction过滤
                    if direction and direction.strip():
                        if row.direction != direction:
                            continue

                    res.append(row)

                    break
                break

        self.res = res

    def _adjust_precision(self, val: Decimal):
        if not val:
            return Decimal("0")

        return val.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _fill_direction(self, row: SymbolRow):
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
            row.direction = TradeDirection.A_B.value

        elif row.diffAb < 0:
            row.direction = TradeDirection.B_A.value

        else:
            row.direction = "equal"

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
                    row.lastFundingRate = self._adjust_precision(p.lastFundingRate * 100)
                    row.zscj = self._adjust_precision(
                        ((p.markPrice - p.indexPrice) / p.markPrice) * 100
                    )
                    break

    def handle_top_n(self, top_n: int | None):
        # 排序
        def sort_attr(x: SymbolRow):
            if x.direction == TradeDirection.A_B.value:
                return x.diffAb
            else:
                return x.diffBa

        res_sorted = sorted(self.res, key=sort_attr, reverse=True)

        if top_n and top_n > 0:
            if top_n < len(res_sorted):
                res_sorted = res_sorted[:top_n]

        self.res = res_sorted



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
