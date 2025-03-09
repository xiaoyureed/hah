import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.models.http_model import Resp

logger = logging.getLogger(__name__)

# 通用的异常捕获处理
async def general_exception_handler(request: Request, ex: Exception):
    logger.error(f"Unexpected error occurred: {ex}")
    
    return JSONResponse(
        status_code=200, content=Resp.failed(f"biz Error: {ex}").model_dump()
    )
