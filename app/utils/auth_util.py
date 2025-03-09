from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.errors import biz_error

secret_key = "secretkey"
algorithm = "HS256"
# 一周后过期, 单位 s
token_expire_in_second = 7 * 24 * 60 * 60


def parse_token(token: str) -> dict[str, Any]:
    payload = None
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.InvalidTokenError:
        raise biz_error.of("token无效")

    exp_ts: int = payload.get("exp_ts")
    if exp_ts and datetime.fromtimestamp(exp_ts, timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise biz_error.of("token已过期")

    return payload


def gen_token(payload: dict[str, Any]):
    exp_ts = int(
        (datetime.now() + timedelta(seconds=token_expire_in_second)).timestamp()
    )
    payload["exp_ts"] = exp_ts
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, exp_ts
