"""Coordena Steam, catálogo de jogos e recomendador de filmes."""

import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import PROJECT_ROOT, settings
from app.game_catalog import GameCatalog
from app.schemas.recommendations import (
    Game,
    Movie,
    Profile,
    ProfileGame,
    RecommendationsResponse,
)
from app.schemas.steam import PlayerSummary
from app.steam import SteamService, SteamServiceError
from app.services.tmdb import get_movie_poster

ML_SOURCE_PATH = PROJECT_ROOT / "ml" / "src"
ML_ARTIFACTS_PATH = PROJECT_ROOT / "ml" / "artifacts"
MAX_GAMES_FOR_PROFILE = 20
PROFILE_PREVIEW_SIZE = 5
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w342"

if str(ML_SOURCE_PATH) not in sys.path:
    sys.path.insert(0, str(ML_SOURCE_PATH))

from recomendador.filmes_hibrido import RecomendadorHibrido  # noqa: E402
from recomendador.filmes_tfidf import RecomendadorFilmes  # noqa: E402
from recomendador.mapeamentos import tags_para_texto  # noqa: E402


class RecommendationService:
    """Carrega o modelo uma vez e gera recomendações a partir de um perfil Steam."""

    def __init__(
        self,
        steam_service: SteamService | None = None,
        game_catalog: GameCatalog | None = None,
        recommender: RecomendadorHibrido | None = None,
    ) -> None:
        self.steam_service = steam_service or SteamService(settings.steam_api_key)
        self.game_catalog = game_catalog or GameCatalog()
        self.recommender = recommender or self._load_recommender()

    @staticmethod
    def _load_recommender() -> RecomendadorHibrido:
        movies_path = ML_ARTIFACTS_PATH / "filmes.parquet"
        factors_path = ML_ARTIFACTS_PATH / "fatores_filmes.npz"
        missing_paths = [path for path in (movies_path, factors_path) if not path.is_file()]
        if missing_paths:
            missing = ", ".join(str(path) for path in missing_paths)
            raise FileNotFoundError(f"Artefatos necessários ao recomendador não encontrados: {missing}")

        tfidf = RecomendadorFilmes(caminho=movies_path)
        return RecomendadorHibrido(
            tfidf=tfidf,
            caminho_fatores=factors_path,
        )

    async def recommend(self, steam_url: str, top_k: int) -> RecommendationsResponse:
        try:
            owned_games = await self.steam_service.get_owned_games(steam_url)
            enriched_games = await self.game_catalog.enrich(
                owned_games,
                limit=MAX_GAMES_FOR_PROFILE,
            )

            # Busca a foto de perfil pública do Steam (avatarfull).
            avatar_url: str | None = None
            try:
                player_summary = await self.steam_service.get_player_summary(steam_url)
                avatar_url = player_summary.avatarfull
            except SteamServiceError:
                # Não quebra a recomendação se a foto do perfil não estiver disponível.
                avatar_url = None

            model_games = [
                {
                    "nome": game.name,
                    "tags": game.tags,
                    "horas": game.hours_played,
                }
                for game in enriched_games
                if game.hours_played > 0 and tags_para_texto(game.tags).strip()
            ]
            if not model_games:
                raise SteamServiceError(
                    422,
                    "EMPTY_PROFILE",
                    "Não encontramos gêneros reconhecidos nos jogos mais jogados deste perfil.",
                )

            movies = self.recommender.recomendar(model_games, n=top_k)
            movie_rows = movies.to_dict(orient="records")
            movie_items = [self._to_movie(row) for row in movie_rows]

            # Preenche posteres faltantes buscando dinamicamente na TMDB API.
            if settings.tmdb_api_key:
                for movie, row in zip(movie_items, movie_rows):
                    if movie.poster_url is None:
                        # O parquet armazena o ID numérico da TMDB em "id";
                        # o campo "movie.id" pode ser um IMDb ID (ex: tt0082766).
                        tmdb_id_raw = row.get("id")
                        tmdb_id = str(tmdb_id_raw) if tmdb_id_raw is not None else None
                        if tmdb_id is not None and tmdb_id.isdigit():
                            try:
                                dynamic_poster = await get_movie_poster(tmdb_id)
                                if dynamic_poster is not None:
                                    movie.poster_url = dynamic_poster
                            except Exception:
                                # Falha na TMDB não deve quebrar a recomendação.
                                pass

            return RecommendationsResponse(
                profile=Profile(
                    games_total=len(owned_games),
                    games_matched=len(model_games),
                    avatar_url=avatar_url,
                    top_games=[
                        ProfileGame(
                            appid=game.appid,
                            name=game.name,
                            hours_played=game.hours_played,
                            genres=game.genres,
                        )
                        for game in enriched_games[:PROFILE_PREVIEW_SIZE]
                    ],
                ),
                movies=movie_items,
                games=[
                    Game(
                        appid=game.appid,
                        name=game.name,
                        genres=game.genres,
                        header_image_url=game.header_image_url,
                        hours_played=game.hours_played,
                        score=0.0,
                        because=[],
                    )
                    for game in enriched_games
                ],
            )
        except SteamServiceError:
            raise
        except Exception as error:
            raise SteamServiceError(
                502,
                "INTERNAL_ERROR",
                f"Erro interno ao gerar recomendações: {error}",
            ) from error

    @classmethod
    def _to_movie(cls, row: dict[str, Any]) -> Movie:
        movie_id = cls._optional_string(row.get("imdb_id"))
        if movie_id is None:
            movie_id = cls._required_string(row.get("id"), "id")

        poster_path = cls._optional_string(row.get("poster_path"))
        poster_url = (
            f"{TMDB_POSTER_BASE_URL}{poster_path}"
            if poster_path is not None
            else None
        )

        score = cls._optional_float(row.get("score"))
        if score is None:
            raise ValueError(f"O recomendador retornou um score inválido para {row.get('title')}.")

        because = cls._optional_string(row.get("porque"))
        return Movie(
            id=movie_id,
            title=cls._required_string(row.get("title"), "title"),
            year=cls._year(row.get("release_date")),
            genres=cls._string_list(row.get("generos")),
            rating=cls._optional_float(row.get("vote_average")),
            poster_url=poster_url,
            score=score,
            because=because.split(" | ") if because else [],
        )

    @staticmethod
    def _required_string(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"O recomendador retornou '{field}' inválido.")
        return value

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _optional_float(value: object) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if hasattr(value, "tolist"):
            value = value.tolist()
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    @staticmethod
    def _year(value: object) -> int | None:
        if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])
        if hasattr(value, "year"):
            year = value.year
            return int(year) if isinstance(year, (int, float)) and math.isfinite(year) else None
        return None
