import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
from typing import Optional

from app.utils import file_util



class App_Logger(logging.Logger):
    def __init__(
        self,
        name: str = "my_logger",
        # eg. logs/app.log
        # 如果不指定，则不输出到文件
        log_path: Optional[str] = None,
        level: int = logging.DEBUG,
        fmt: str = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    ):
        super().__init__(name, level)

        if self.handlers:
            return

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(fmt))
        self.addHandler(console_handler)

        if log_path:
            log_dir, log_file = os.path.split(log_path)
            if not log_file:
                log_file = "app.log"
            if not log_dir:
                log_dir = "logs"
            
            log_path = os.path.join(log_dir, log_file)

            # 自动创建日志目录
            if os.path.exists(log_dir):
                file_util.clear_dir(log_dir)
            else:
                os.makedirs(log_dir)

            # 按大小滚动日志（例如：最多3个备份，每个10MB）
            # file_handler = RotatingFileHandler(
            #     log_path, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
            # )

            # 按时间滚动日志（例如：每天零点滚动，保留7天）
            file_handler = TimedRotatingFileHandler(
                log_path, when="midnight", interval=1, backupCount=7, encoding="utf-8"
            )

            file_handler.setFormatter(logging.Formatter(fmt))
            self.addHandler(file_handler)

Lg = App_Logger()

def init_app_log(debug: bool = False):
    global Lg 
    level = logging.DEBUG if debug else logging.INFO
    Lg.setLevel(level)