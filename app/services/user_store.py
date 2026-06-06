"""File-backed user store and session handling for Fruit Grade."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Header, HTTPException, status

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STORE_PATH = DATA_DIR / "auth_store.json"

_STORE_LOCK = threading.RLock()
_SESSION_TOKENS: dict[str, str] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_store() -> dict[str, Any]:
    return {"users": []}


def _load_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return _default_store()

    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_store()
        data.setdefault("users", [])
        return data
    except Exception:
        return _default_store()


def _save_store(store: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_username(username: str) -> str:
    return username.strip()


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt_hex = salt_hex or secrets.token_hex(16)
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()
    return salt_hex, hashed


def _verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    _, hashed = _hash_password(password, salt_hex)
    return hmac.compare_digest(hashed, expected_hash)


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }


def _find_user(store: dict[str, Any], username: str) -> dict[str, Any] | None:
    normalized = _normalize_username(username)
    for user in store["users"]:
        if user.get("username") == normalized:
            return user
    return None


def _find_user_by_id(store: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    for user in store["users"]:
        if user.get("id") == user_id:
            return user
    return None


def _normalize_checklist(checklist: list[bool] | None, length: int) -> list[bool]:
    values = list(checklist or [])
    if len(values) < length:
        values.extend([False] * (length - len(values)))
    return values[:length]


def _normalize_recipe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ingredients = list(payload.get("ingredients") or [])
    steps = list(payload.get("steps") or [])
    created_at_value = payload.get("created_at") or _utc_now()
    if hasattr(created_at_value, "isoformat"):
        created_at = created_at_value.isoformat()
    else:
        created_at = str(created_at_value)
    checklist_checked = _normalize_checklist(payload.get("checklist_checked"), len(ingredients))
    return {
        "id": payload.get("id") or str(uuid4()),
        "ingredient": str(payload.get("ingredient") or ""),
        "title": str(payload.get("title") or ""),
        "ingredients": ingredients,
        "steps": steps,
        "created_at": created_at,
        "checklist_checked": checklist_checked,
    }


def register_user(username: str, password: str) -> dict[str, Any]:
    normalized = _normalize_username(username)
    if not normalized:
        raise ValueError("사용자 이름은 필수입니다")

    with _STORE_LOCK:
        store = _load_store()
        if _find_user(store, normalized):
            raise ValueError("이미 존재하는 사용자 이름입니다")

        salt_hex, password_hash = _hash_password(password)
        user = {
            "id": str(uuid4()),
            "username": normalized,
            "password_salt": salt_hex,
            "password_hash": password_hash,
            "created_at": _utc_now(),
            "recipes": [],
        }
        store["users"].append(user)
        _save_store(store)

    token = secrets.token_urlsafe(32)
    _SESSION_TOKENS[token] = user["id"]
    return {"token": token, "user": _public_user(user)}


def authenticate_user(username: str, password: str) -> dict[str, Any]:
    normalized = _normalize_username(username)
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user(store, normalized)
        if not user:
            raise ValueError("잘못된 사용자 이름 또는 비밀번호입니다")
        if not _verify_password(password, user["password_salt"], user["password_hash"]):
            raise ValueError("잘못된 사용자 이름 또는 비밀번호입니다")

    token = secrets.token_urlsafe(32)
    _SESSION_TOKENS[token] = user["id"]
    return {"token": token, "user": _public_user(user)}


def get_user_by_token(token: str) -> dict[str, Any] | None:
    user_id = _SESSION_TOKENS.get(token)
    if not user_id:
        return None

    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            return None
        return user


def _extract_session_token(
    x_session_token: str | None = Header(None, alias="X-Session-Token"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> str | None:
    if x_session_token:
        return x_session_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(None, 1)[1].strip()
    return None


def get_current_user(
    x_session_token: str | None = Header(None, alias="X-Session-Token"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    token = _extract_session_token(x_session_token, authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session token")

    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    return user


def list_user_recipes(user_id: str) -> list[dict[str, Any]]:
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            return []
        recipes = [deepcopy(recipe) for recipe in user.get("recipes", [])]
    recipes.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return recipes


def add_user_recipe(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        recipe = _normalize_recipe_payload(payload)
        user.setdefault("recipes", []).insert(0, recipe)
        _save_store(store)
        return deepcopy(recipe)


def update_user_recipe_checklist(
    user_id: str,
    recipe_id: str,
    checklist_checked: list[bool],
) -> dict[str, Any]:
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        for recipe in user.get("recipes", []):
            if recipe.get("id") == recipe_id:
                recipe["checklist_checked"] = _normalize_checklist(
                    checklist_checked,
                    len(recipe.get("ingredients", [])),
                )
                _save_store(store)
                return deepcopy(recipe)

    raise ValueError("Saved recipe not found")


def delete_user_recipe(user_id: str, recipe_id: str) -> None:
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        recipes = user.get("recipes", [])
        original_count = len(recipes)
        user["recipes"] = [recipe for recipe in recipes if recipe.get("id") != recipe_id]
        if len(user["recipes"]) == original_count:
            raise ValueError("저장된 레시피를 찾을 수 없습니다")

        _save_store(store)


def clear_user_recipe_checklist(user_id: str, recipe_id: str) -> dict[str, Any]:
    with _STORE_LOCK:
        store = _load_store()
        user = _find_user_by_id(store, user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        for recipe in user.get("recipes", []):
            if recipe.get("id") == recipe_id:
                recipe["checklist_checked"] = [False] * len(recipe.get("ingredients", []))
                _save_store(store)
                return deepcopy(recipe)

    raise ValueError("저장된 레시피를 찾을 수 없습니다")


def clear_session(token: str) -> None:
    _SESSION_TOKENS.pop(token, None)