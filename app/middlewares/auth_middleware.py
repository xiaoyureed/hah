from starlette.middleware.base import BaseHTTPMiddleware

from app.errors import biz_error
from app.utils.auth_util import parse_token
from app.utils.log_util import Lg

white_list = [
    "/api/auth/token",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # body = await request.body()
        # print(json.loads(body))

        url_path = request.url.path
        # 进入验证
        if url_path.startswith("/api") and url_path not in white_list:
            Lg.info(f"auth middleware, url: {url_path}")
            token = request.headers.get("Authorization")
            if not token:
                raise biz_error.of("token不能为空")

            # 假设 token 是以 "Bearer token_value" 的格式传递
            token = token.split(" ")[-1]  # 获取 token 部分
            parse_token(token)

        resp = await call_next(request)
        return resp
