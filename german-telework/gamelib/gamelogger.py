import time
from typing import Any

import requests


class GameLogger:
    _start_time: float = time.time()

    @classmethod
    def reset(cls) -> None:
        cls._start_time = time.time()

    @staticmethod
    def format_arg(arg: Any) -> Any:
        if isinstance(arg, requests.Response):
            if arg.status_code >= 400:
                return str(arg) + ' (' + repr(arg.text.split('\n')[0][:1024]) + ')'
        return arg

    @classmethod
    def log(cls, *args: Any):
        formatted_args: list[Any] = [cls.format_arg(a) for a in args]
        t = time.time() - cls._start_time
        print(f'[{t:6.3f}] ', *formatted_args)
