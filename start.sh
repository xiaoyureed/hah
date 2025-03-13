uv sync
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8387 app:fast_app

