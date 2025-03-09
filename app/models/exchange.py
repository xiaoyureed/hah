from enum import Enum

from pydantic import BaseModel


# 现货期货市场
class Market(Enum):
    """市场"""

    spot = "现货"
    future = "期货"


# 交易所
class Exchange(Enum):
    """交易所"""

    binance = "币安"


class BookOptions(BaseModel):
    """盘口-可选项"""

    id: str
    label: str

