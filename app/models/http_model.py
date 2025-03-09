from typing import Any
from pydantic import BaseModel


class Resp(BaseModel):
    code: int
    message: str
    data: list[Any] | dict[str, Any] | None = None

    @staticmethod
    def ok(data: dict[str, Any] | list[Any] | None = None):
        return Resp(code=0, message="", data=data)
    
    @staticmethod
    def failed(err: str):
        return Resp(code=1, message=err, data=None)
