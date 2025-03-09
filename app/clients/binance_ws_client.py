
import asyncio
import json
from typing import Any

from pydantic import BaseModel
import websockets

from app.clients.binance_client import BinanceF
from app.utils.log_util import Lg

class WsHandle(BaseModel):
    ws: websockets.ClientConnection
    id: str


class BinanceWsF:
    """币安合约 ws"""
    def __init__(self, api_key: str | None = None, api_secret: str | None = None):  
        # 公共行情频道ws连接, 一个策略, 可能有多个
        self.ws_public: list[WsHandle] = []

        # 账户频道的ws连接, 一个策略只可能有一个
        self.ws_account = None

        # 是否正常被用户关闭
        self.closed_normally = False

        self.rest_client = BinanceF(api_key, api_secret)

    async def close(self):
        self.closed_normally = True
        
        if self.ws_public:
            for item in self.ws_public:
                if item.ws.state == websockets.State.OPEN:
                    await item.ws.close()
        
        if self.ws_account and self.ws_account.state == websockets.State.OPEN:
            await self.ws_account.close()

    async def pong_ws(self, ws):
        while 1:
            try:
                await asyncio.sleep(300) # 300秒
                await ws.pong()
            except Exception as e:
                Lg.error(f"ws pont error: {e}")
                break

    async def pong_listen_key(self):
        while 1:
            try:
                await asyncio.sleep(1800) # 30分钟
                await self.rest_client.listen_key_re()
            except Exception as e:
                Lg.error(f"ws pont error: {e}")
                break


    async def subscribe_account(self, callback):
        """订阅账户信息
        
        eg. account balance, order changes...
        """
        listen_key = await self.rest_client.listen_key()

        retry_times = 5
        for i in range(retry_times):
            try:
                async with websockets.connect(f"wss://fstream.binance.com/ws/{listen_key}", ping_interval=None) as ws_account:
                    self.ws_account = ws_account

                    # 保持心跳
                    asyncio.create_task(self.pong_ws(ws_account))
                    asyncio.create_task(self.pong_listen_key())

                    Lg.info("币安: 合约账户频道订阅成功")
                    while 1:
                        account_message = json.loads(await ws_account.recv())
                        callback(account_message)

            except websockets.ConnectionClosed as e:
                if self.closed_normally:
                    Lg.info("币安账户频道连接正常关闭")
                    break
                else:
                    Lg.error(e)
                    Lg.info(f"币安账户频道连接断开，正在第{i+1}次重连.....")
                    continue

    
    async def subscribe_public(self, args, callback):
        """订阅公共行情"""
        retry_times = 5
        for i in range(retry_times):
        
            try:
                async with websockets.connect(f"wss://fstream.binance.com/stream", ping_interval=None) as ws:
                    self.ws_public.append({"ws": ws, "id": args["id"]})

                    asyncio.create_task(self.pong_ws(ws))

                    await ws.send(json.dumps(args))
                    Lg.info("币安: 合约公共频道订阅成功")

                    while 1:
                        res = json.loads(await ws.recv())
                        if "result" in res:
                            Lg.info(res)
                            continue

                        callback(res)

            except websockets.ConnectionClosed as e:
                if self.closed_normally:
                    Lg.info("币安public频道连接正常关闭")
                    break
                else:
                    Lg.error(e)
                    Lg.info(f"币安public频道连接断开，正在第{i+1}次重连.....")
                    continue
