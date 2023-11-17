import os
from typing import Tuple
from uuid import uuid4

import arrow
import jwt
from fastapi import Request, HTTPException


def validate_tokens(request: Request):
    at, csrf = get_tokens_from_request(request)
    if not at or not csrf:
        raise HTTPException(status_code=401)
    data = decode_jwt(at)
    at_csrf = data.get('csrf')
    if not at_csrf:
        raise HTTPException(status_code=401)
    if at_csrf != csrf:
        raise HTTPException(status_code=401)
    if arrow.get(data.get('expires')).to('UTC') < arrow.utcnow():
        raise HTTPException(status_code=401)
    return data


def get_tokens_from_request(request):
    """
    A helper function that extracts the access token and csrf token from a request.
    """
    access_token = request.cookies.get("at")
    csrf_token = request.headers.get("X-CSRF-Token")
    return access_token, csrf_token


def create_jwt(user_id) -> Tuple[str, str]:
    csrf = str(uuid4())
    _now = arrow.utcnow()
    expires = _now.shift(hours=1).isoformat()
    created = _now.isoformat()
    data = {
        "user_id": user_id,
        "csrf": csrf,
        "expires": expires,
        "created": created
    }
    return jwt.encode(data, os.getenv('JWT_SECRET'), algorithm="HS256"), csrf


def decode_jwt(token):
    return jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
