import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.errors.exception_handler import general_exception_handler
from app.middlewares import auth_middleware
from app.routers.auth import router as auth_router
from app.routers.watch import router as watch_router
from app.utils.log_util import Lg, init_app_log
from main import debugMode

init_app_log(debugMode)
# 通过 main.py 启动时, 禁用 gunicorn 和 uvicorn 的默认日志
logging.getLogger("gunicorn").propagate = False
logging.getLogger("uvicorn").propagate = False

fast_app = FastAPI()

fast_app.include_router(watch_router)
fast_app.include_router(auth_router)

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8387", "localhost:8387"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fast_app.add_middleware(auth_middleware.AuthMiddleware)

fast_app.add_exception_handler(Exception, general_exception_handler)

# mount the static files generated from the frontend
if os.path.exists("./dist"):
    fast_app.mount("/", StaticFiles(directory="./dist", html=True), name="static")
else:
    Lg.warning("frontend resources not found!")

# app.include_router(static_router)
