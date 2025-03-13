debugMode = True


def main() -> int:
    import uvicorn

    host = "0.0.0.0"
    port = 8387
    print(f"Starting server at http://{host}:{port}")

    uvicorn.run("app:fast_app", host=host, port=port, reload=debugMode, log_config=None)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
