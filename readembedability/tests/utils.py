import asyncio
from functools import wraps


def async_test(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(func(*args, **kwargs))
        loop.close()
        return result
    return wrapper


class FakeResponse:
    def __init__(self, body, url=None):
        self.body = body
        self.url = url

    # pylint: disable=no-self-use
    def is_text(self):
        return False
