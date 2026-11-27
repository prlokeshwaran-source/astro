from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DuplicateKeyError)
    async def duplicate(request: Request, exc: DuplicateKeyError):
        return JSONResponse(status_code=409, content={"detail":"A record with this value already exists"})
