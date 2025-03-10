

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SymbolRow(BaseModel):
    symbol: str

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
    # 盘口 a
    bookA: Optional[str] = None
    # 盘口 B
    bookB: Optional[str] = None


class TradeDirection(Enum):
    """trading direction"""

    A_B = "A买B卖"
    B_A = "A卖B买"


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
