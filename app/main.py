"""FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


def _error_payload(reason: str, details: dict | None = None) -> dict:
    return {
        "status": "error",
        "reason": reason,
        "details": details or {},
    }


def create_app() -> FastAPI:
    app = FastAPI(title="FreshCheck API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")

    from app.routes.analyze import router as analyze_router
    from app.routes.auth import router as auth_router
    from app.routes.classify import router as classify_router
    from app.routes.detect import router as detect_router
    from app.routes.me import router as me_router
    from app.routes.recipe import router as recipe_router

    app.include_router(detect_router, prefix="/api")
    app.include_router(classify_router, prefix="/api")
    app.include_router(analyze_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(me_router, prefix="/api")
    app.include_router(recipe_router, prefix="/api")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            reason = str(exc.detail.get("reason") or exc.detail.get("message") or "HTTP error")
            details = exc.detail
        else:
            reason = str(exc.detail or "HTTP error")
            details = {"status_code": exc.status_code}
        return JSONResponse(status_code=exc.status_code, content=_error_payload(reason, details))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_payload("Validation error", {"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_payload("Internal server error", {"type": exc.__class__.__name__}),
        )

    return app


app = create_app()
