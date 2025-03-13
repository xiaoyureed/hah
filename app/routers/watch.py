from fastapi import APIRouter, Depends

from app.config import datasource
from app.models.http_model import Resp
from app.models.watch_models import (
    BookOptions,
    ExchangeMarket,
    SymbolRowReq,
    WatchMapping,
)

router = APIRouter(prefix="/api/watch", tags=["watch"])


def resolve_exchange_markets(book: str) -> list[ExchangeMarket]:
    """
    'binance-spot,binance-future' -> ExchangeMarket
    """

    arr = book.split(",")

    return [ExchangeMarket(ele) for ele in arr]


def resolve_ab_mappings(book_a: str | None, book_b: str | None) -> list[WatchMapping]:
    book_a = book_a or "binance-spot"
    book_b = book_b or "binance-swap"

    res: list[WatchMapping] = []
    a_arr = resolve_exchange_markets(book_a)
    b_arr = resolve_exchange_markets(book_b)

    # 1
    # 2 2
    # 3 3
    #   4
    #
    # 12 13 14
    # 22 23 24
    # 32 33 34
    # a b 相等的映射需要排除, 位置仅仅交换的也需要排除

    for ele_a in a_arr:
        for ele_b in b_arr:
            if ele_a == ele_b:
                continue

            repeat_with_exist = False
            for res_ele in res:
                if (ele_a == res_ele.b) and (ele_b == res_ele.a):
                    repeat_with_exist = True
                    break
            if repeat_with_exist:
                continue

            res.append(WatchMapping(ele_a, ele_b))

    return res


@router.get("/book-tickers")
def watch(params: SymbolRowReq = Depends()):
    res = []
    
    mappings = resolve_ab_mappings(params.bookA, params.bookB)

    for ele in mappings:
        rows = ele.get_watch_res(params)
        res += rows


    return Resp.ok(res)


@router.get("/book-options")
def gen_book_options():
    """生成盘口可选项"""
    res = []

    exchanges: list[dict] = datasource.get("exchanges")
    markets: list[dict] = datasource.get("markets")
    for ex in exchanges:
        for ma in markets:
            id = f"{ex.get('id')}-{ma.get('id')}"
            label = f"{ex.get('label')}-{ma.get('label')}"
            res.append(BookOptions(id=id, label=label))

    return Resp.ok(res)
