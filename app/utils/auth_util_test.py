from app.utils.auth_util import gen_token, parse_token


def test_gen_token():
    token, exp = gen_token({"user_id": 1})
    parsed = parse_token(token)
    assert parsed["user_id"] == 1
