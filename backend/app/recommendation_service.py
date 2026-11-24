"""Coordena Steam, catálogo de jogos e recomendador de filmes."""

import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import PROJECT_ROOT, settings
from app.game_catalog import GameCatalog
from app.schemas.recommendations import (
    Movie,
    Profile,
    ProfileGame,
    RecommendationsResponse,
)
from app.steam import SteamService, SteamServiceError

ML_SOURCE_PATH = PROJECT_ROOT / "ml" / "src"
ML_ARTIFACTS_PATH = PROJECT_ROOT / "ml" / "artifacts"
MAX_GAMES_FOR_PROFILE = 20
PROFILE_PREVIEW_SIZE = 5
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w342"

if str(ML_SOURCE_PATH) not in sys.path:
    sys.path.insert(0, str(ML_SOURCE_PATH))

from recomendador.filmes_hibrido import RecomendadorHibrido  # noqa: E402
from recomendador.filmes_semantico import RecomendadorSemantico  # noqa: E402
from recomendador.filmes_tfidf import RecomendadorFilmes  # noqa: E402
from recomendador.mapeamentos import tags_para_texto  # noqa: E402


class RecommendationService:
    """Carrega o modelo uma vez e gera recomendações a partir de um perfil Steam."""

    def __init__(
        self,
        steam_service: SteamService | None = None,
        game_catalog: GameCatalog | None = None,
        recommender: RecomendadorSemantico | RecomendadorHibrido | None = None,
    ) -> None:
        self.steam_service = steam_service or SteamService(settings.steam_api_key)
        self.game_catalog = game_catalog or GameCatalog()
        self.recommender = recommender or self._load_recommender()

    @staticmethod
    def _load_recommender() -> RecomendadorSemantico | RecomendadorHibrido:
        # 1. Verifica se os artefatos do modelo semântico (modelo_final) estão disponíveis
        semantic_dir = settings.model_dir_path
        required_semantic_files = [
            "X_jogos.npz",
            "X_filmes.npz",
            "G_jogos.npy",
            "G_filmes.npy",
            "artefatos_modelo.joblib",
            "catalogo_jogos.parquet",
            "catalogo_filmes.parquet",
        ]
        has_semantic = semantic_dir.is_dir() and all(
            (semantic_dir / f).is_file() for f in required_semantic_files
        )

        if has_semantic:
            return RecomendadorSemantico(caminho_modelo=semantic_dir)

        # 2. Fallback para o modelo legado caso modelo_final não esteja presente
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
        owned_games = await self.steam_service.get_owned_games(steam_url)
        enriched_games = await self.game_catalog.enrich(
            owned_games,
            limit=MAX_GAMES_FOR_PROFILE,
        )

        if isinstance(self.recommender, RecomendadorSemantico):
            model_games = [
                {
                    "appid": game.appid,
                    "nome": game.name,
                    "horas": game.hours_played,
                }
                for game in enriched_games
                if game.hours_played > 0
            ]
            if not model_games:
                raise SteamServiceError(
                    422,
                    "EMPTY_PROFILE",
                    "Não encontramos jogos com tempo jogado neste perfil.",
                )
            try:
                movies = self.recommender.recomendar(model_games, top_k=top_k)
            except ValueError as err:
                raise SteamServiceError(
                    422,
                    "EMPTY_PROFILE",
                    "Nenhum jogo jogado deste perfil foi encontrado no catálogo do modelo.",
                ) from err
        else:
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

        return RecommendationsResponse(
            profile=Profile(
                games_total=len(owned_games),
                games_matched=len(model_games),
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
            movies=[self._to_movie(row) for row in movies.to_dict(orient="records")],
        )

    @classmethod
    def _to_movie(cls, row: dict[str, Any]) -> Movie:
        movie_id = cls._optional_string(row.get("imdb_id"))
        if movie_id is None:
            movie_id = cls._required_string(row.get("id"), "id")

        poster_path = cls._optional_string(row.get("poster_path"))
        poster_url = (
            f"{TMDB_POSTER_BASE_URL}{poster_path}"
            if poster_path is not None
            else cls._optional_string(row.get("poster_url"))
        )

        score = cls._optional_float(row.get("score"))
        if score is None:
            raise ValueError(f"O recomendador retornou um score inválido para {row.get('title')}.")

        because_raw = row.get("because") or row.get("por_que") or row.get("porque")
        if isinstance(because_raw, list):
            because = [str(b).strip() for b in because_raw if str(b).strip()]
        elif isinstance(because_raw, str):
            because = [b.strip() for b in because_raw.split(" | ") if b.strip()]
        else:
            because = []

        raw_year = row.get("year")
        year = int(raw_year) if isinstance(raw_year, (int, float)) and math.isfinite(raw_year) else cls._year(row.get("release_date"))

        return Movie(
            id=movie_id,
            title=cls._required_string(row.get("title"), "title"),
            year=year,
            genres=cls._string_list(row.get("genres") or row.get("generos")),
            rating=cls._optional_float(row.get("rating") or row.get("vote_average")),
            poster_url=poster_url,
            score=score,
            because=because,
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
