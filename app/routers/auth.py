from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.errors import biz_error
from app.models.http_model import Resp
from app.utils import auth_util
from app.utils.auth_util import gen_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginReq(BaseModel):
    password: str


class LoginResp(BaseModel):
    access_token: str
    exp_ts: int


@router.post("/token")
def login(params: LoginReq):
    if params.password != "123456":
        raise biz_error.of("密码错误")

    token, exp_ts = gen_token({"id": 1, "name": "admin"})
    return Resp.ok({"accessToken": token, "tokenType": "bearer", "exp_ts": exp_ts})


@router.get("/me")
def me(auth_header: str = Header(None, alias="Authorization")):
    token = auth_header.split(" ")[-1]
    parsed = auth_util.parse_token(token)

    return Resp.ok(
        {
            "id": parsed.get("id"),
            "name": parsed.get("name"),
            "exp_ts": parsed.get("exp_ts"),
        }
    )


@router.post("/logout")
def logout():
    return ""
