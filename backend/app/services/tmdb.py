"""Serviço para buscar posteres de filmes na API do TMDB (The Movie Database)."""

from __future__ import annotations

from app.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


async def get_movie_poster(tmdb_id: int | str) -> str | None:
    """Busca o poster_path de um filme na TMDB e monta a URL da imagem.

    Retorna None quando a TMDB_API_KEY não estiver configurada, o filme não
    tiver poster ou ocorrer qualquer erro de rede/parse.
    """
    if not settings.tmdb_api_key:
        return None

    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"api_key": settings.tmdb_api_key, "language": "pt-BR"},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            poster_path = data.get("poster_path")
            if not poster_path:
                return None
            return f"{TMDB_IMAGE_BASE}{poster_path}"
    except Exception:
        return None
