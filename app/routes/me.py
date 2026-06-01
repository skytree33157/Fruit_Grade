"""Routes for authenticated saved recipes and checklist state."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.saved_recipe import (
    SavedRecipeChecklistUpdate,
    SavedRecipeCreate,
    SavedRecipeResponse,
)
from app.services.user_store import (
    add_user_recipe,
    clear_user_recipe_checklist,
    delete_user_recipe,
    get_current_user,
    list_user_recipes,
    update_user_recipe_checklist,
)

router = APIRouter(prefix="/me")


@router.get("/recipes", response_model=list[SavedRecipeResponse])
async def get_recipes(user: dict = Depends(get_current_user)):
    return list_user_recipes(user["id"])


@router.post("/recipes", response_model=SavedRecipeResponse)
async def save_recipe(payload: SavedRecipeCreate, user: dict = Depends(get_current_user)):
    try:
        return add_user_recipe(user["id"], payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/recipes/{recipe_id}/checklist", response_model=SavedRecipeResponse)
async def update_recipe_checklist(
    recipe_id: str,
    payload: SavedRecipeChecklistUpdate,
    user: dict = Depends(get_current_user),
):
    try:
        return update_user_recipe_checklist(user["id"], recipe_id, payload.checklist_checked)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    try:
        delete_user_recipe(user["id"], recipe_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/recipes/{recipe_id}/checklist", response_model=SavedRecipeResponse)
async def clear_recipe_checklist(recipe_id: str, user: dict = Depends(get_current_user)):
    try:
        return clear_user_recipe_checklist(user["id"], recipe_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc