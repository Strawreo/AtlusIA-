"""Modelos para os jogos retornados pela biblioteca Steam."""

from app.schemas.base import CamelModel


class OwnedGame(CamelModel):
    appid: int
    name: str
    hours_played: float
