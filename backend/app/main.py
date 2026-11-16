"""Ponto de entrada da API FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.health import router as health_router

app = FastAPI(
    title="AtlusIA API",
    version="0.1.0",
    description="API do protótipo de recomendação do AtlusIA.",
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
