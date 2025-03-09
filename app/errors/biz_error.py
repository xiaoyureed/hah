class BizException(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(self.message)


def of(err: str):
    return BizException(1, err)

