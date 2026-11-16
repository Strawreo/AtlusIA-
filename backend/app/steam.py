"""Integração com a Web API oficial da Steam."""

import re
from urllib.parse import unquote, urlparse

import httpx

from app.schemas.steam import OwnedGame

STEAM_API_BASE = "https://api.steampowered.com"
STEAM_COMMUNITY_HOSTS = {"steamcommunity.com", "www.steamcommunity.com"}
STEAM_ID64_PATTERN = re.compile(r"^\d{17}$")
VANITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
REQUEST_TIMEOUT_SECONDS = 10.0


class SteamServiceError(Exception):
    """Erro esperado da integração, pronto para ser convertido em resposta HTTP."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def parse_profile_url(profile_url: str) -> tuple[str, str]:
    """Valida um link de perfil e retorna o tipo e o identificador."""
    parsed = urlparse(profile_url.strip())

    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in STEAM_COMMUNITY_HOSTS
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise SteamServiceError(
            400,
            "INVALID_STEAM_URL",
            "Informe um link válido de perfil da Steam.",
        )

    path_parts = [unquote(part) for part in parsed.path.split("/") if part]
    if len(path_parts) != 2:
        raise SteamServiceError(
            400,
            "INVALID_STEAM_URL",
            "O link deve usar /profiles/<SteamID64> ou /id/<nome>.",
        )

    profile_type, identifier = path_parts
    if profile_type == "profiles" and STEAM_ID64_PATTERN.fullmatch(identifier):
        return "steamid", identifier
    if profile_type == "id" and VANITY_PATTERN.fullmatch(identifier):
        return "vanity", identifier

    raise SteamServiceError(
        400,
        "INVALID_STEAM_URL",
        "O link deve usar /profiles/<SteamID64> ou /id/<nome>.",
    )


class SteamService:
    """Resolve o perfil e carrega jogos e horas jogadas pela API da Steam."""

    def __init__(
        self,
        api_key: str,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.transport = transport

    async def get_owned_games(self, profile_url: str) -> list[OwnedGame]:
        profile_type, identifier = parse_profile_url(profile_url)
        if not self.api_key:
            raise SteamServiceError(
                503,
                "STEAM_API_KEY_MISSING",
                "A chave da API da Steam não está configurada no backend.",
            )

        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            if profile_type == "vanity":
                steam_id = await self._resolve_vanity_url(client, identifier)
            else:
                steam_id = identifier

            payload = await self._get_json(
                client,
                f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v1/",
                {
                    "key": self.api_key,
                    "steamid": steam_id,
                    "include_appinfo": 1,
                    "include_played_free_games": 1,
                },
            )

        response = payload.get("response")
        if not isinstance(response, dict) or "game_count" not in response:
            raise SteamServiceError(
                403,
                "LIBRARY_PRIVATE",
                "Não foi possível acessar a biblioteca. Verifique se os detalhes dos jogos são públicos.",
            )

        game_count = response["game_count"]
        games = response.get("games", [])
        if (
            not isinstance(game_count, int)
            or game_count < 0
            or not isinstance(games, list)
        ):
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou dados inválidos para a biblioteca.",
            )

        if game_count > 0 and not games:
            raise SteamServiceError(
                403,
                "LIBRARY_PRIVATE",
                "Não foi possível acessar a biblioteca. Verifique se os detalhes dos jogos são públicos.",
            )

        return [self._parse_owned_game(game) for game in games]

    async def _resolve_vanity_url(
        self,
        client: httpx.AsyncClient,
        vanity_url: str,
    ) -> str:
        payload = await self._get_json(
            client,
            f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v1/",
            {"key": self.api_key, "vanityurl": vanity_url},
        )

        response = payload.get("response")
        if not isinstance(response, dict) or "success" not in response:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou uma resposta inválida ao localizar o perfil.",
            )

        if response["success"] != 1:
            raise SteamServiceError(
                404,
                "PROFILE_NOT_FOUND",
                "Não foi possível encontrar esse perfil da Steam.",
            )

        steam_id = response.get("steamid")
        if not isinstance(steam_id, str) or not STEAM_ID64_PATTERN.fullmatch(steam_id):
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou um identificador de perfil inválido.",
            )
        return steam_id

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, str | int],
    ) -> dict:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam demorou para responder. Tente novamente.",
            ) from error
        except httpx.HTTPStatusError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam não conseguiu processar a solicitação.",
            ) from error
        except httpx.RequestError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "Não foi possível conectar à Steam. Tente novamente.",
            ) from error
        except ValueError as error:
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou uma resposta inválida.",
            ) from error

        if not isinstance(payload, dict):
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou uma resposta inválida.",
            )
        return payload

    @staticmethod
    def _parse_owned_game(game: object) -> OwnedGame:
        if not isinstance(game, dict):
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou um jogo em formato inválido.",
            )

        appid = game.get("appid")
        name = game.get("name")
        playtime_minutes = game.get("playtime_forever")
        if (
            not isinstance(appid, int)
            or isinstance(appid, bool)
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(playtime_minutes, int)
            or isinstance(playtime_minutes, bool)
            or playtime_minutes < 0
        ):
            raise SteamServiceError(
                502,
                "STEAM_UNAVAILABLE",
                "A Steam retornou dados inválidos para um jogo.",
            )

        return OwnedGame(
            appid=appid,
            name=name,
            hours_played=playtime_minutes / 60,
        )
