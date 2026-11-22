"""Carrega o catálogo global de jogos da Steam (Parquet) e enriquece perfis."""

import ast
import logging
import math
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd

from app.config import settings
from app.schemas.steam import EnrichedGame, OwnedGame

logger = logging.getLogger(__name__)

PARQUET_MAGIC_BYTES = b"PAR1"


def download_catalog(
    url: str,
    destination: Path,
    client: httpx.Client | None = None,
) -> None:
    """Baixa o catálogo Parquet via stream e valida os magic bytes antes de salvar."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_name(f"{destination.name}.tmp")

    logger.info("Baixando catálogo global de jogos de %s para %s...", url, destination)

    def _stream(c: httpx.Client) -> None:
        with c.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            with open(temp_path, "wb") as file:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    file.write(chunk)

    try:
        if client is not None:
            _stream(client)
        else:
            with httpx.Client(timeout=180.0) as default_client:
                _stream(default_client)

        with open(temp_path, "rb") as file:
            header = file.read(4)
            if header != PARQUET_MAGIC_BYTES:
                raise ValueError(
                    f"O arquivo baixado não é um Parquet válido (magic bytes recebidos: {header!r})."
                )

        temp_path.replace(destination)
        logger.info("Catálogo global de jogos baixado e validado com sucesso!")
    finally:
        if temp_path.exists():
            temp_path.unlink()


def ensure_catalog_exists(
    catalog_path: Path | None = None,
    download_url: str | None = None,
    client: httpx.Client | None = None,
) -> Path:
    """Garante que o catálogo exista localmente, realizando o download se necessário."""
    path = Path(catalog_path or settings.game_catalog_path)
    url = download_url or settings.steam_catalog_url

    if not path.exists():
        if not url:
            raise FileNotFoundError(
                f"Catálogo de jogos não encontrado em {path} e nenhuma URL configurada."
            )
        download_catalog(url, path, client=client)
    return path


def _parse_list(val: object) -> list[str]:
    """Normaliza coleções para list[str], tratando arrays, strings literais ou nulos."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return []
    if isinstance(val, (list, tuple, np.ndarray)):
        return [str(item).strip() for item in val if str(item).strip()]
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return []
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, (list, tuple)):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (ValueError, SyntaxError):
            pass
        return [val]
    return []


class GameCatalog:
    """Catálogo em memória de metadados da Steam indexado por appid."""

    def __init__(
        self,
        catalog_path: Path | None = None,
        download_url: str | None = None,
        auto_download: bool = True,
    ) -> None:
        self.catalog_path = Path(catalog_path or settings.game_catalog_path)
        self.download_url = download_url or settings.steam_catalog_url

        if auto_download and not self.catalog_path.exists():
            ensure_catalog_exists(self.catalog_path, self.download_url)

        self._catalog = self._load_catalog()

    def _load_catalog(self) -> dict[int, dict[str, Any]]:
        """Carrega e indexa o Parquet em memória."""
        if not self.catalog_path.exists():
            logger.warning("Catálogo de jogos não encontrado em %s.", self.catalog_path)
            return {}

        # Identifica colunas disponíveis para carregar apenas o necessário
        schema_df = pd.read_parquet(self.catalog_path)
        cols = schema_df.columns.tolist()

        id_col = "appID" if "appID" in cols else "appid"
        if id_col not in cols:
            raise ValueError(f"O catálogo {self.catalog_path} não contém a coluna de identificador (appID/appid).")

        needed_cols = [id_col, "name"]
        for opt in ("genres", "tags", "categories", "header_image"):
            if opt in cols:
                needed_cols.append(opt)

        df = schema_df[needed_cols].copy()
        df = df.dropna(subset=[id_col])
        df[id_col] = pd.to_numeric(df[id_col], errors="coerce").fillna(-1).astype(int)
        df = df[df[id_col] > 0].drop_duplicates(subset=[id_col])

        catalog: dict[int, dict[str, Any]] = {}
        for row in df.to_dict(orient="records"):
            appid = int(row[id_col])
            genres = _parse_list(row.get("genres"))
            tags = _parse_list(row.get("tags")) if "tags" in row else []
            categories = _parse_list(row.get("categories")) if "categories" in row else []
            header_image = row.get("header_image")
            if not isinstance(header_image, str) or not header_image.strip():
                header_image = None

            catalog[appid] = {
                "name": str(row.get("name") or ""),
                "genres": genres,
                "categories": categories,
                # Se não houver coluna 'tags' separada, gêneros fornecem os sinais básicos
                "tags": tags if tags else genres.copy(),
                "header_image": header_image,
            }

        logger.info("Catálogo global de jogos carregado com %d títulos.", len(catalog))
        return catalog

    @property
    def total_games(self) -> int:
        return len(self._catalog)

    def get_game(self, appid: int) -> dict[str, Any] | None:
        return self._catalog.get(appid)

    async def enrich(
        self,
        owned_games: list[OwnedGame],
        limit: int = 20,
    ) -> list[EnrichedGame]:
        """Cruza os jogos mais jogados com o catálogo global em memória."""
        if limit < 1:
            raise ValueError("O limite precisa ser pelo menos 1.")

        selected_games = sorted(
            (game for game in owned_games if game.hours_played > 0),
            key=lambda game: game.hours_played,
            reverse=True,
        )[:limit]

        if not selected_games:
            return []

        enriched: list[EnrichedGame] = []
        for game in selected_games:
            entry = self._catalog.get(game.appid)
            if entry:
                enriched.append(
                    EnrichedGame(
                        appid=game.appid,
                        name=entry["name"] or game.name,
                        hours_played=game.hours_played,
                        genres=entry["genres"],
                        categories=entry["categories"],
                        tags=entry["tags"],
                        header_image=entry["header_image"],
                        metadata_status="ok",
                    )
                )
            else:
                enriched.append(
                    EnrichedGame(
                        appid=game.appid,
                        name=game.name,
                        hours_played=game.hours_played,
                        genres=[],
                        categories=[],
                        tags=[],
                        header_image=None,
                        metadata_status="not_found",
                    )
                )
        return enriched
