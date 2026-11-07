# seven_tools_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.proposals.router import router as proposals_router
from app.modules.tool_chat.router import router as tool_chat_router
from app.modules.lead_qualification.router import router as lead_qualification_router
from app.modules.ai.router import router as ai_router
from app.modules.companies.router import router as companies_router
from app.modules.membership.router import router as membership_router

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    app = FastAPI(title="SEVEN Tools API", version="0.1.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(proposals_router, prefix="/api/v1")
    app.include_router(tool_chat_router, prefix="/api/v1")
    app.include_router(lead_qualification_router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(companies_router, prefix="/api/v1")
    app.include_router(membership_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
