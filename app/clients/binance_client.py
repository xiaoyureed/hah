from app.utils.log_util import Lg
from datetime import datetime, timezone
import hashlib
import hmac
from urllib.parse import urlencode
import httpx


class BinanceF:
    """币安合约"""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = "https://fapi.binance.com",
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

        self.session = httpx.AsyncClient()

        # resend the request
        self.err_codes_resend = [-1000, -1001, -1021, -5028, -2010, -2011, -2022]
        # stop the request
        self.err_codes_stop = [-2013, -4046, -4059, -5026, -5027]

    async def close(self):
        if self.session:
            await self.session.aclose()

    def _hash(self, query: str):
        if not self.api_secret:
            raise ValueError("api_secret is required")

        return hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()

    def _timestamp(self):
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    async def _send_signed(
        self, http_method, path, params: dict = {}, full_log: bool = True
    ):
        headers = {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json;charset=utf-8",
        }

        times_retry = 5
        for i in range(times_retry):
            ts = self._timestamp()

            params["timestamp"] = ts
            params["recvWindow"] = 3500  # 3.5s
            url_params = urlencode(params).replace("%27", "%22")  # 单引号替换为双引号
            url = (
                self.base_url
                + path
                + "?"
                + url_params
                + "&signature="
                + self._hash(url_params)
            )
            req_args = {
                "url": url,
                "headers": headers,
                "method": http_method,
                # 最大超时
                "timeout": 5,
            }

            try:
                res = await self.session.request(**req_args)
            except httpx.TimeoutException:
                Lg.error(f"request timeout, args: {req_args}")
                continue

            if res is None:
                continue

            if res.status_code == 200:
                if full_log:
                    Lg.info(
                        f"<200> request:{ts},{req_args}; response:{self._timestamp()}"
                    )
                return res
            else:
                err_code = res.json()["code"]
                Lg.error(
                    f"<{res.status_code}> {err_code} request:{ts},{req_args}; response:{self._timestamp()},{res.text}"
                )

                if err_code in self.err_codes_resend:
                    pass
                elif err_code in self.err_codes_stop:
                    return res
                else:
                    Lg.error(f"unknown error code: {err_code}")
                    return res

            if i == times_retry - 1:
                Lg.error("request failed, reached the max retry times")

    async def _send_public(self, path, params: dict = {}):
        url_params = urlencode(params, True)
        url = self.base_url + path
        if url_params:
            url += "?" + url_params
        req_args = {
            "url": url,
            "timeout": 5,
        }

        times_retry = 5
        for i in range(times_retry):
            try:
                res = await self.session.get(**req_args)
                if res.status_code == 200:
                    return res
                else:
                    Lg.error(
                        f"<{res.status_code}> {res.json()['code']} request:{req_args}; response:{self._timestamp()}"
                    )
            except httpx.TimeoutException:
                Lg.error(f"request timeout, args: {req_args}")

            if i == times_retry - 1:
                Lg.error("request failed, reached the max retry times")

    async def listen_key(self) :
        """获取listenKey

        同一个 listen key 有效期 60min
        """
        path = "/fapi/v1/listenKey"
        res = await self._send_signed("POST", path)

        if res:
            return res.json()["listenKey"]

    async def listen_key_re(self):
        """更新listenKey"""
        path = "/fapi/v1/listenKey"
        res = await self._send_signed("PUT", path)
        if res:
            return res.json()["listenKey"]


class BinanceS:
    """币安现货"""

    pass


class Binance:
    """杠杆"""

    pass
