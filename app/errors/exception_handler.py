from fastapi import Request
from fastapi.responses import JSONResponse

from app.models.http_model import Resp
from app.utils.log_util import Lg


# 通用的异常捕获处理
async def general_exception_handler(request: Request, ex: Exception):
    Lg.error(f"Unexpected error occurred: {ex}")

    return JSONResponse(
        status_code=200, content=Resp.failed(str(ex)).model_dump()
    )
