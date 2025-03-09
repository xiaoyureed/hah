import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.errors.exception_handler import general_exception_handler
from app.middlewares import auth_middleware
from app.routers.auth import router as auth_router
from app.routers.watch import router as watch_router
from app.utils.log_util import Lg

app = FastAPI()

app.include_router(watch_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8387", "localhost:8387"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(auth_middleware.AuthMiddleware)

app.add_exception_handler(Exception, general_exception_handler)

# mount the static files generated from the frontend
if os.path.exists("./dist"):
    app.mount("/", StaticFiles(directory="./dist", html=True), name="static")
else:
    Lg.warning("frontend resources not found!")

# app.include_router(static_router)
