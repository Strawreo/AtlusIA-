"""Rota para gerar recomendações a partir de um perfil Steam."""

from fastapi import APIRouter, HTTPException, Request

from app.schemas.recommendations import RecommendationsRequest, RecommendationsResponse
from app.steam import SteamServiceError

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationsResponse)
async def create_recommendations(
    body: RecommendationsRequest,
    request: Request,
) -> RecommendationsResponse:
    service = request.app.state.recommendation_service
    try:
        return await service.recommend(body.steam_url, body.top_k)
    except SteamServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
        ) from error
