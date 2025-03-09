import threading


class SingletonMeta(type):
    _instance_mapping: dict = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance_mapping:
            with cls._lock:
                if cls not in cls._instance_mapping:
                    cls._instance_mapping[cls] = super().__call__(*args, **kwargs)

        return cls._instance_mapping[cls]
