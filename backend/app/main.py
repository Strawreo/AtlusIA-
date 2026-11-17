"""Ponto de entrada da API FastAPI."""

from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.health import router as health_router
from app.routes.recommendations import router as recommendations_router
from app.recommendation_service import RecommendationService


def create_app(
    recommendation_service_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    service_factory = recommendation_service_factory or RecommendationService

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # O modelo e o cache são carregados uma vez ao iniciar o servidor.
        app.state.recommendation_service = service_factory()
        yield

    app = FastAPI(
        title="AtlusIA API",
        version="0.1.0",
        description="API do protótipo de recomendação do AtlusIA.",
        lifespan=lifespan,
    )

    # Restringe chamadas do navegador às origens configuradas no ambiente.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(recommendations_router, prefix="/api/v1")
    return app


app = create_app()
