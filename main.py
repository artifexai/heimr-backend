from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth import auth_router
from api.paths import is_public_route
from api.routes import router
from api.shared_data import get_search_idx
from security.jwt_utils import validate_tokens

load_dotenv()

app = FastAPI()
app.include_router(router)
app.include_router(auth_router, prefix='/auth')

# TODO: Build this dynamically so that it works in production and locally.

origins = [
    "https://heimr.io",
    "heimr.io",
    "*.heimr.io",
    "heimr.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("https")
async def pre_request_validation(request: Request, call_next):
    # tokens are only validated if the route is not public
    if not is_public_route(request) and request.method != 'OPTIONS':
        try:
            validate_tokens(request)
        except Exception:
            return JSONResponse(status_code=401, content={'detail': 'Invalid Credentials'})
    try:
        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={'detail': e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={'detail': str(e)})


@app.on_event("startup")
def load_startup_data():
    _ = get_search_idx()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        'main:app',
        workers=1,
        port=5000,
        ssl_keyfile=".cert/key.pem",
        ssl_certfile=".cert/cert.pem"
    )
