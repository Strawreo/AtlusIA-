"""Testes do contrato HTTP de recomendações."""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.recommendations import (
    Movie,
    Profile,
    ProfileGame,
    RecommendationsResponse,
)
from app.steam import SteamServiceError


class FakeRecommendationService:
    async def recommend(self, steam_url: str, top_k: int) -> RecommendationsResponse:
        if steam_url == "https://steamcommunity.com/id/private":
            raise SteamServiceError(403, "LIBRARY_PRIVATE", "Biblioteca privada.")
        return RecommendationsResponse(
            profile=Profile(
                games_total=1,
                games_matched=1,
                top_games=[
                    ProfileGame(
                        appid=620,
                        name="Portal 2",
                        hours_played=2,
                        genres=["Action"],
                    )
                ],
            ),
            movies=[
                Movie(
                    id="tt0133093",
                    title="The Matrix",
                    year=1999,
                    genres=["Action", "Science Fiction"],
                    rating=8.7,
                    poster_url=None,
                    score=0.74,
                    because=["science fiction"],
                )
            ][:top_k],
        )


class RecommendationsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(FakeRecommendationService))
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def test_post_recommendations_returns_camel_case_contract(self) -> None:
        response = self.client.post(
            "/api/v1/recommendations",
            json={
                "steamUrl": "https://steamcommunity.com/id/player",
                "topK": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["profile"]["gamesTotal"], 1)
        self.assertEqual(body["profile"]["topGames"][0]["hoursPlayed"], 2)
        self.assertEqual(body["movies"][0]["posterUrl"], None)

    def test_steam_errors_keep_the_documented_error_shape(self) -> None:
        response = self.client.post(
            "/api/v1/recommendations",
            json={"steamUrl": "https://steamcommunity.com/id/private"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            {"code": "LIBRARY_PRIVATE", "message": "Biblioteca privada."},
        )

    def test_top_k_is_validated(self) -> None:
        response = self.client.post(
            "/api/v1/recommendations",
            json={
                "steamUrl": "https://steamcommunity.com/id/player",
                "topK": 0,
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
