from app.utils.log_util import init_app_log


def main():
    import uvicorn

    init_app_log(True)

    uvicorn.run("app:app", host="0.0.0.0", port=8387, reload=True)

    pass


if __name__ == "__main__":
    main()
