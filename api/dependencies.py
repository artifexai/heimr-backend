from typing import Callable

from fastapi import Response

from database import build_session, SessFactoryType


# return the session factory as a dependency. This allows dependency injection and mocking
def app_db() -> Callable[[], SessFactoryType]:
    sess = build_session()
    try:
        yield sess
    finally:
        sess.close()


def set_cookie():
    def func(response: Response, key: str, value: str):
        response.set_cookie(key=key, value=value, httponly=True, secure=True, samesite="none")

    yield func
