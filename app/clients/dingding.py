import httpx


class DingDing:
    def __init__(self, webhook: str):
        self.webhook = webhook
    
    async def send(self, msg: str):
        data = {
            "msgtype": "text",
            "text": {
                "content": msg
            }

        }
        client = httpx.AsyncClient()
        
        while 1:
            try:
                await client.post(self.webhook, json=data)
                break
            except Exception as _e:
                # raise e
                pass
            finally:
                await client.aclose()