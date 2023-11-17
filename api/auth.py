from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel

from api.dependencies import app_db, set_cookie
from database import Account, DBSessionType
from security import create_jwt
from security.encryption import verify_password
from security.jwt_utils import validate_tokens

auth_router = APIRouter(
    dependencies=[
        Depends(app_db),
        Depends(set_cookie)
    ])


class Credentials(BaseModel):
    email: str
    password: str


@auth_router.post("/login")
async def login(
        response: Response,
        credentials: Credentials,
        db: DBSessionType = Depends(app_db),
        cookie=Depends(set_cookie)
):
    """
    An asynchronous API endpoint that logs a user in.
    """
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400)

    user: Optional[Account] = db.query(Account) \
        .filter(Account.email == credentials.email) \
        .first()

    if not user:
        raise HTTPException(status_code=401)

    if not verify_password(user.password, credentials.password):
        raise HTTPException(status_code=401)

    at, csrf = create_jwt(user.account_id)
    cookie(response, key="at", value=at)
    return {"message": "success", 'csrf': csrf}


@auth_router.get("/")
async def is_logged_in(request: Request):
    """
    An asynchronous API endpoint that checks if a user is logged in.
    """

    try:
        _ = validate_tokens(request)
        return {'logged_in': True}
    except HTTPException:
        return {'logged_in': False}


@auth_router.get("/logout")
async def logout(response: Response):
    """
    An asynchronous API endpoint that logs a user out.
    """
    response.delete_cookie(key="at")
    return {"message": "success"}
