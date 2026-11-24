"""Busca e mantém em cache gêneros/categorias dos jogos por appid."""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from app.schemas.steam import EnrichedGame, OwnedGame
from app.steam import SteamServiceError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GAME_TAGS_PATH = PROJECT_ROOT / "ml" / "artifacts" / "game_tags.parquet"
STORE_API_URL = "https://store.steampowered.com/api/appdetails"
STORE_TIMEOUT_SECONDS = 15.0
SECONDS_BETWEEN_REQUESTS = 1.0
METADATA_SOURCE = "Steam Store API: gêneros e categorias; tags são gêneros"
CACHE_COLUMNS = [
    "appid",
    "name",
    "genres",
    "categories",
    "tags",
    "header_image_url",
    "metadata_source",
    "metadata_status",
    "fetched_at",
]

logger = logging.getLogger(__name__)


def _descriptions(details: dict[str, Any], field: str, appid: int) -> list[str]:
    """Extrai os nomes de gêneros/categorias sem copiar descrições do jogo."""
    entries = details.get(field, [])
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise ValueError(f"A Steam retornou '{field}' inválido para o appid {appid}.")

    descriptions = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("description"), str):
            raise ValueError(f"A Steam retornou um item '{field}' inválido para o appid {appid}.")
        description = entry["description"].strip()
        if description:
            descriptions.append(description)
    return descriptions


def parse_store_response(
    appid: int,
    owned_game_name: str,
    payload: object,
    fetched_at: str,
) -> dict[str, object]:
    """Converte a resposta da Steam Store em uma linha do cache local."""
    if not isinstance(payload, dict):
        raise ValueError(f"A resposta da Steam Store é inválida para o appid {appid}.")

    result = payload.get(str(appid))
    if not isinstance(result, dict):
        raise ValueError(f"A resposta da Steam Store não contém o appid {appid}.")

    if result.get("success") is not True:
        return {
            "appid": appid,
            "name": owned_game_name,
            "genres": [],
            "categories": [],
            "tags": [],
            "metadata_source": METADATA_SOURCE,
            "metadata_status": "unavailable",
            "fetched_at": fetched_at,
        }

    details = result.get("data")
    if not isinstance(details, dict):
        raise ValueError(f"Os detalhes da Steam Store são inválidos para o appid {appid}.")

    genres = _descriptions(details, "genres", appid)
    categories = _descriptions(details, "categories", appid)
    store_name = details.get("name")
    if not isinstance(store_name, str) or not store_name.strip():
        store_name = owned_game_name

    header_image = details.get("header_image")
    if not isinstance(header_image, str) or not header_image.strip():
        header_image = None

    return {
        "appid": appid,
        "name": store_name,
        "genres": genres,
        "categories": categories,
        # A API da Store não fornece tags comunitárias; gêneros servem como sinais básicos.
        "tags": genres.copy(),
        "header_image_url": header_image,
        "metadata_source": METADATA_SOURCE,
        "metadata_status": "ok",
        "fetched_at": fetched_at,
    }


class GameCatalog:
    """Enriquece jogos da biblioteca e persiste os metadados para reuso."""

    def __init__(
        self,
        cache_path: Path = GAME_TAGS_PATH,
        timeout: float = STORE_TIMEOUT_SECONDS,
        request_delay: float = SECONDS_BETWEEN_REQUESTS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.timeout = timeout
        self.request_delay = request_delay
        self.transport = transport
        self._lock = asyncio.Lock()
        self._metadata_by_appid = self._load_cache()

    async def enrich(
        self,
        owned_games: list[OwnedGame],
        limit: int = 20,
    ) -> list[EnrichedGame]:
        """Busca dados ausentes para os jogos mais jogados e retorna o perfil enriquecido."""
        if limit < 1:
            raise ValueError("O limite precisa ser pelo menos 1.")

        selected_games = sorted(
            (game for game in owned_games if game.hours_played > 0),
            key=lambda game: game.hours_played,
            reverse=True,
        )[:limit]
        if not selected_games:
            return []

        async with self._lock:
            missing_games = [
                game for game in selected_games
                if game.appid not in self._metadata_by_appid
            ]
            if missing_games:
                await self._fetch_missing(missing_games)
                self._save_cache()

            return [
                self._to_enriched_game(game, self._metadata_by_appid[game.appid])
                for game in selected_games
            ]

    def _load_cache(self) -> dict[int, dict[str, object]]:
        if not self.cache_path.exists():
            return {}

        frame = pd.read_parquet(self.cache_path)
        missing_columns = set(CACHE_COLUMNS) - set(frame.columns)
        if missing_columns:
            for col in sorted(missing_columns):
                frame[col] = None
        if frame["appid"].duplicated().any():
            raise ValueError(f"O cache {self.cache_path} contém appids duplicados.")

        metadata = {}
        for row in frame[CACHE_COLUMNS].to_dict(orient="records"):
            appid = int(row["appid"])
            metadata[appid] = {
                **row,
                "appid": appid,
                "genres": self._as_string_list(row["genres"], "genres", appid),
                "categories": self._as_string_list(row["categories"], "categories", appid),
                "tags": self._as_string_list(row["tags"], "tags", appid),
            }
        return metadata

    @staticmethod
    def _as_string_list(value: object, field: str, appid: int) -> list[str]:
        if hasattr(value, "tolist"):
            value = value.tolist()
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"O cache contém '{field}' inválido para o appid {appid}.")
        return value

    async def _fetch_missing(self, games: list[OwnedGame]) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            for index, game in enumerate(games):
                if index:
                    await asyncio.sleep(self.request_delay)
                row = await self._fetch_store_metadata(client, game, fetched_at)
                self._metadata_by_appid[game.appid] = row
                if row["metadata_status"] == "unavailable":
                    logger.warning("Metadados da Store indisponíveis para appid %s.", game.appid)

    async def _fetch_store_metadata(
        self,
        client: httpx.AsyncClient,
        game: OwnedGame,
        fetched_at: str,
    ) -> dict[str, object]:
        try:
            response = await client.get(
                STORE_API_URL,
                params={"appids": game.appid, "cc": "us", "l": "en"},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                f"A consulta de metadados do jogo {game.appid} demorou demais.",
            ) from error
        except httpx.HTTPStatusError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                f"A Steam Store não conseguiu consultar o jogo {game.appid}.",
            ) from error
        except httpx.RequestError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                f"Não foi possível consultar os metadados do jogo {game.appid}.",
            ) from error
        except ValueError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                f"A Steam Store retornou JSON inválido para o jogo {game.appid}.",
            ) from error

        try:
            return parse_store_response(game.appid, game.name, payload, fetched_at)
        except ValueError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                f"A Steam Store retornou metadados inválidos para o jogo {game.appid}.",
            ) from error

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [self._metadata_by_appid[appid] for appid in sorted(self._metadata_by_appid)]
        temporary_path = self.cache_path.with_name(f".{self.cache_path.name}.tmp")
        try:
            pd.DataFrame(rows, columns=CACHE_COLUMNS).to_parquet(temporary_path, index=False)
            temporary_path.replace(self.cache_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _to_enriched_game(
        owned_game: OwnedGame,
        metadata: dict[str, object],
    ) -> EnrichedGame:
        return EnrichedGame(
            appid=owned_game.appid,
            name=str(metadata["name"]),
            hours_played=owned_game.hours_played,
            genres=metadata["genres"],
            categories=metadata["categories"],
            tags=metadata["tags"],
            header_image_url=metadata.get("header_image_url"),
            metadata_status=str(metadata["metadata_status"]),
        )
