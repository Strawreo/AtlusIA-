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

    def test_recommendation_service_to_movie_semantic_contract(self) -> None:
        from app.recommendation_service import RecommendationService

        row = {
            "id": "tt0058131",
            "title": "The Mystery of Thug Island",
            "year": 1964,
            "genres": ["Action", "Adventure"],
            "rating": 5.0,
            "score": 0.52,
            "because": ["Gêneros: Action", "Temas: island"],
        }
        movie = RecommendationService._to_movie(row)
        self.assertEqual(movie.id, "tt0058131")
        self.assertEqual(movie.title, "The Mystery of Thug Island")
        self.assertEqual(movie.year, 1964)
        self.assertEqual(movie.genres, ["Action", "Adventure"])
        self.assertEqual(movie.rating, 5.0)
        self.assertEqual(movie.score, 0.52)
        self.assertEqual(movie.because, ["Gêneros: Action", "Temas: island"])


if __name__ == "__main__":
    unittest.main()
