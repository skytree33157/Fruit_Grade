"""Recipe API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services import llm as llm_service
from app.services.auth import require_api_key

router = APIRouter()


@router.post("/recipe", response_model=RecipeResponse)
async def recipe(req: RecipeRequest, _key: str = Depends(require_api_key)):
    try:
        return llm_service.get_recipe(req.ingredient)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
