"""Cria um catálogo local de gêneros e categorias dos jogos mais jogados."""

import argparse
import asyncio

from app.game_catalog import GAME_TAGS_PATH, GameCatalog
from app.config import settings
from app.schemas.steam import EnrichedGame
from app.steam import SteamService, SteamServiceError

async def build_catalog(profile_url: str, limit: int) -> list[EnrichedGame]:
    """Seleciona os jogos mais jogados e adiciona metadados ao cache compartilhado."""
    if limit < 1:
        raise ValueError("O limite precisa ser pelo menos 1.")
    if not settings.steam_api_key:
        raise SteamServiceError(
            503,
            "STEAM_API_KEY_MISSING",
            "Configure STEAM_API_KEY no arquivo .env antes de criar o catálogo.",
        )

    owned_games = await SteamService(settings.steam_api_key).get_owned_games(profile_url)
    catalog = GameCatalog()
    enriched_games = await catalog.enrich(owned_games, limit=limit)
    if not enriched_games:
        raise ValueError("O perfil não retornou jogos com tempo jogado para catalogar.")
    return enriched_games


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um Parquet com gêneros e categorias dos jogos mais jogados."
    )
    parser.add_argument(
        "--profile-url",
        required=True,
        help="Link público do perfil Steam usado para selecionar os jogos.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Máximo de jogos com horas jogadas a catalogar (padrão: 20).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = asyncio.run(build_catalog(args.profile_url, args.limit))
    with_genres = sum(bool(game.genres) for game in games)
    with_categories = sum(bool(game.categories) for game in games)
    print(f"\nCatálogo atualizado em: {GAME_TAGS_PATH}")
    print(f"Jogos selecionados: {len(games)}")
    print(f"Com gêneros: {with_genres}; com categorias: {with_categories}")
    print("A coluna 'tags' contém gêneros da Store, não tags comunitárias.")


if __name__ == "__main__":
    main()
