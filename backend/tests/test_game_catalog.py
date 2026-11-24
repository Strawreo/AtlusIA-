"""Testes unitários do catálogo global de jogos da Steam."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx
import pandas as pd

from app.game_catalog import (
    GameCatalog,
    download_catalog,
    ensure_catalog_exists,
    PARQUET_MAGIC_BYTES,
)
from app.schemas.steam import OwnedGame


class GameCatalogTests(unittest.TestCase):
    def test_enrich_matches_games_by_appid(self) -> None:
        with TemporaryDirectory() as temp_dir:
            parquet_path = Path(temp_dir) / "test_catalog.parquet"
            data = pd.DataFrame(
                [
                    {
                        "appID": 620,
                        "name": "Portal 2",
                        "genres": ["Action", "Adventure"],
                        "categories": ["Single-player", "Co-op"],
                        "header_image": "https://example.com/portal2.jpg",
                    },
                    {
                        "appID": 1245620,
                        "name": "ELDEN RING",
                        "genres": ["Action", "RPG"],
                        "categories": ["Single-player", "Online PvP"],
                        "header_image": "https://example.com/eldenring.jpg",
                    },
                ]
            )
            data.to_parquet(parquet_path, index=False)

            catalog = GameCatalog(catalog_path=parquet_path, auto_download=False)
            self.assertEqual(catalog.total_games, 2)

            owned = [
                OwnedGame(appid=620, name="Portal 2", hours_played=15.0),
                OwnedGame(appid=999999, name="Unknown Game", hours_played=5.0),
            ]

            enriched = asyncio.run(catalog.enrich(owned))
            self.assertEqual(len(enriched), 2)

            # Primeiro jogo: encontrado
            portal = enriched[0]
            self.assertEqual(portal.appid, 620)
            self.assertEqual(portal.name, "Portal 2")
            self.assertEqual(portal.genres, ["Action", "Adventure"])
            self.assertEqual(portal.tags, ["Action", "Adventure"])
            self.assertEqual(portal.header_image, "https://example.com/portal2.jpg")
            self.assertEqual(portal.metadata_status, "ok")

            # Segundo jogo: ausente do catálogo
            unknown = enriched[1]
            self.assertEqual(unknown.appid, 999999)
            self.assertEqual(unknown.genres, [])
            self.assertEqual(unknown.tags, [])
            self.assertEqual(unknown.metadata_status, "not_found")

    def test_download_catalog_rejects_corrupted_or_html_files(self) -> None:
        def fake_html_responder(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>Download quota exceeded</html>")

        with TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "steam_tratado.parquet"
            client = httpx.Client(transport=httpx.MockTransport(fake_html_responder))

            with self.assertRaises(ValueError) as context:
                download_catalog("https://fake.url/catalog.parquet", dest_path, client=client)

            self.assertIn("magic bytes", str(context.exception))
            self.assertFalse(dest_path.exists())

    def test_download_catalog_saves_valid_parquet(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sample_parquet = Path(temp_dir) / "sample.parquet"
            pd.DataFrame([{"appID": 10, "name": "Counter-Strike"}]).to_parquet(sample_parquet)
            valid_bytes = sample_parquet.read_bytes()

            dest_path = Path(temp_dir) / "downloaded.parquet"
            client = httpx.Client(
                transport=httpx.MockTransport(lambda req: httpx.Response(200, content=valid_bytes))
            )

            download_catalog("https://fake.url/catalog.parquet", dest_path, client=client)
            self.assertTrue(dest_path.exists())
            self.assertEqual(dest_path.read_bytes()[:4], PARQUET_MAGIC_BYTES)

    def test_ensure_catalog_exists_skips_download_if_already_present(self) -> None:
        with TemporaryDirectory() as temp_dir:
            parquet_path = Path(temp_dir) / "existing.parquet"
            parquet_path.write_bytes(b"PAR1dummydata")

            # Se tentar baixar, o mock vai falhar
            fail_client = httpx.Client(
                transport=httpx.MockTransport(lambda req: self.fail("Não deveria fazer download."))
            )

            result = ensure_catalog_exists(parquet_path, "https://fake.url", client=fail_client)
            self.assertEqual(result, parquet_path)


if __name__ == "__main__":
    unittest.main()
