"""Testes da integração Steam usando respostas simuladas."""

import asyncio
import unittest

import httpx

from app.steam import SteamService, SteamServiceError, parse_profile_url

STEAM_ID = "76561198000000000"


class SteamServiceTests(unittest.TestCase):
    def test_parse_profile_url_accepts_steam_id_and_vanity(self) -> None:
        self.assertEqual(
            parse_profile_url(f"https://steamcommunity.com/profiles/{STEAM_ID}/"),
            ("steamid", STEAM_ID),
        )
        self.assertEqual(
            parse_profile_url("https://steamcommunity.com/id/jogador"),
            ("vanity", "jogador"),
        )

    def test_parse_profile_url_rejects_other_hosts(self) -> None:
        with self.assertRaises(SteamServiceError) as context:
            parse_profile_url("https://example.com/id/jogador")

        self.assertEqual(context.exception.code, "INVALID_STEAM_URL")

    def test_vanity_profile_returns_games_with_hours_converted(self) -> None:
        def responder(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/ResolveVanityURL/v1/"):
                return httpx.Response(
                    200,
                    json={"response": {"success": 1, "steamid": STEAM_ID}},
                )
            return httpx.Response(
                200,
                json={
                    "response": {
                        "game_count": 1,
                        "games": [
                            {
                                "appid": 620,
                                "name": "Portal 2",
                                "playtime_forever": 90,
                            }
                        ],
                    }
                },
            )

        service = SteamService(
            "test-key",
            transport=httpx.MockTransport(responder),
        )
        games = asyncio.run(
            service.get_owned_games("https://steamcommunity.com/id/jogador")
        )

        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].appid, 620)
        self.assertEqual(games[0].hours_played, 1.5)

    def test_invalid_vanity_returns_profile_not_found(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"response": {"success": 42}},
            )
        )
        service = SteamService("test-key", transport=transport)

        with self.assertRaises(SteamServiceError) as context:
            asyncio.run(
                service.get_owned_games("https://steamcommunity.com/id/inexistente")
            )

        self.assertEqual(context.exception.code, "PROFILE_NOT_FOUND")

    def test_missing_api_key_is_reported_without_requesting_steam(self) -> None:
        service = SteamService("")

        with self.assertRaises(SteamServiceError) as context:
            asyncio.run(
                service.get_owned_games(
                    f"https://steamcommunity.com/profiles/{STEAM_ID}"
                )
            )

        self.assertEqual(context.exception.code, "STEAM_API_KEY_MISSING")

    def test_private_library_is_reported(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json={"response": {}})
        )
        service = SteamService("test-key", transport=transport)

        with self.assertRaises(SteamServiceError) as context:
            asyncio.run(
                service.get_owned_games(
                    f"https://steamcommunity.com/profiles/{STEAM_ID}"
                )
            )

        self.assertEqual(context.exception.code, "LIBRARY_PRIVATE")


if __name__ == "__main__":
    unittest.main()
