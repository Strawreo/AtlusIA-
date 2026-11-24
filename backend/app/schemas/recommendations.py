"""Contrato HTTP para solicitar e receber recomendações de filmes."""

from pydantic import Field

from app.schemas.base import CamelModel


class RecommendationsRequest(CamelModel):
    steam_url: str
    top_k: int = Field(default=10, ge=1, le=50)


class ProfileGame(CamelModel):
    appid: int
    name: str
    hours_played: float
    genres: list[str]


class Profile(CamelModel):
    games_total: int
    games_matched: int
    avatar_url: str | None
    top_games: list[ProfileGame]


class Movie(CamelModel):
    id: str
    title: str
    year: int | None
    genres: list[str]
    rating: float | None
    poster_url: str | None
    score: float
    because: list[str] = Field(default_factory=list)


class Game(CamelModel):
    appid: int
    name: str
    genres: list[str]
    header_image_url: str | None
    hours_played: float
    score: float
    because: list[str] = Field(default_factory=list)


class Album(CamelModel):
    id: str
    name: str
    artist: str
    year: int | None
    cover_url: str | None
    genres: list[str]
    score: float
    because: list[str] = Field(default_factory=list)


class RecommendationsResponse(CamelModel):
    profile: Profile
    movies: list[Movie]
    games: list[Game] = Field(default_factory=list)
    albums: list[Album] = Field(default_factory=list)
