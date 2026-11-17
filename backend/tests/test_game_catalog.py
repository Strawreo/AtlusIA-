"""Testes da conversão de metadados da Steam Store."""

import unittest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.game_catalog import GameCatalog, parse_store_response
from app.schemas.steam import OwnedGame


class GameCatalogTests(unittest.TestCase):
    def test_store_genres_are_saved_as_coarse_model_tags(self) -> None:
        row = parse_store_response(
            620,
            "Portal 2",
            {
                "620": {
                    "success": True,
                    "data": {
                        "name": "Portal 2",
                        "genres": [{"description": "Action"}, {"description": "Adventure"}],
                        "categories": [{"description": "Single-player"}],
                    },
                }
            },
            "2026-11-16T00:00:00+00:00",
        )

        self.assertEqual(row["genres"], ["Action", "Adventure"])
        self.assertEqual(row["categories"], ["Single-player"])
        self.assertEqual(row["tags"], ["Action", "Adventure"])
        self.assertEqual(row["metadata_status"], "ok")

    def test_unavailable_store_metadata_is_marked_explicitly(self) -> None:
        row = parse_store_response(
            999,
            "Unknown game",
            {"999": {"success": False}},
            "2026-11-16T00:00:00+00:00",
        )

        self.assertEqual(row["metadata_status"], "unavailable")
        self.assertEqual(row["genres"], [])
        self.assertEqual(row["tags"], [])

    def test_metadata_is_cached_and_reused_by_appid(self) -> None:
        responses = 0

        def responder(request: httpx.Request) -> httpx.Response:
            nonlocal responses
            responses += 1
            appid = request.url.params["appids"]
            return httpx.Response(
                200,
                json={
                    appid: {
                        "success": True,
                        "data": {
                            "name": "Portal 2",
                            "genres": [{"description": "Action"}],
                            "categories": [{"description": "Single-player"}],
                        },
                    }
                },
            )

        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "game_tags.parquet"
            transport = httpx.MockTransport(responder)
            games = [OwnedGame(appid=620, name="Portal 2", hours_played=2)]

            first = GameCatalog(
                cache_path=cache_path,
                request_delay=0,
                transport=transport,
            )
            result = asyncio.run(first.enrich(games))
            second = GameCatalog(
                cache_path=cache_path,
                request_delay=0,
                transport=httpx.MockTransport(
                    lambda request: self.fail("O cache deveria evitar outra consulta.")
                ),
            )
            cached_result = asyncio.run(second.enrich(games))

        self.assertEqual(responses, 1)
        self.assertEqual(result[0].genres, ["Action"])
        self.assertEqual(cached_result[0].hours_played, 2)


if __name__ == "__main__":
    unittest.main()
