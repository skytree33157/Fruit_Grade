"""Recipe generation service.

Produces a validated recipe dictionary matching the `RecipeResponse` schema.
Supports `mock` (default), `gemini`/`google`, and legacy `openai` providers via
lazy import. Implements simple retries, timeout handling, and JSON extraction
from raw text.
"""

from __future__ import annotations

import json
import os
import re
import time
from importlib import import_module
from typing import Any

from app.config import settings
from app.schemas.recipe import RecipeResponse

_JSON_RE = re.compile(r"\{.*\}", flags=re.DOTALL)


def _build_recipe_prompt(ingredient: str) -> str:
    return f"""
당신은 전문 요리사입니다. 사용자가 '{ingredient}'(을)를 입력했습니다.
이 재료를 메인으로 활용한 맛있고 실용적인 요리 레시피를 한국어로 작성해주세요.

반드시 아래 JSON 형식을 엄격하게 지켜서, JSON만 출력하세요.

{{
    "title": "요리 이름",
    "ingredients": ["재료 1", "재료 2"],
    "steps": ["조리 순서 1", "조리 순서 2"]
}}
""".strip()


def _parse_json_text(text: str) -> dict[str, Any]:
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract JSON substring
    m = _JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    raise ValueError("Could not parse JSON from LLM response")


def _response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    try:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text.strip():
                    return part_text
    except Exception:
        pass

    return str(response)


def _get_gemini_recipe(ingredient: str) -> dict:
    try:
        genai = import_module("google.generativeai")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Gemini provider requires 'google-generativeai'. Install it with 'pip install google-generativeai'."
        ) from exc

    api_key = settings.LLM_API_KEY or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Set LLM_API_KEY (or GOOGLE_API_KEY) in your .env file."
        )

    genai.configure(api_key=api_key)
    model_name = getattr(settings, "LLM_MODEL", None) or "gemini-2.5-flash"
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(_build_recipe_prompt(ingredient))
    data = _parse_json_text(_response_text(response))
    return RecipeResponse(**data).model_dump()


def _get_openai_recipe(ingredient: str) -> dict:
    openai = import_module("openai")
    openai.api_key = settings.LLM_API_KEY

    prompt = _build_recipe_prompt(ingredient)

    response = openai.ChatCompletion.create(
        model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        timeout=getattr(settings, "LLM_TIMEOUT", 10),
    )

    text = ""
    try:
        text = response.choices[0].message.content
    except Exception:
        try:
            text = response.choices[0].text
        except Exception:
            text = str(response)

    data = _parse_json_text(text)
    return RecipeResponse(**data).model_dump()


def _get_mock_recipe(ingredient: str) -> dict:
    sample = {
        "title": f"{ingredient} 볶음 (샘플)",
        "ingredients": [f"{ingredient} 200g", "소금 1t", "후추 약간"],
        "steps": ["재료 손질", "팬에 볶기", "간 맞추기"],
    }
    return RecipeResponse(**sample).model_dump()


def get_recipe(ingredient: str, *, retries: int = 2, backoff: float = 0.5) -> dict:
    provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "mock"

    if provider in {"gemini", "google"}:
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return _get_gemini_recipe(ingredient)
            except Exception as exc:
                last_err = exc
                if attempt < retries:
                    time.sleep(backoff * attempt)
                    continue
                raise

        if last_err:
            raise last_err

    if provider == "openai":
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return _get_openai_recipe(ingredient)
            except Exception as exc:
                last_err = exc
                if attempt < retries:
                    time.sleep(backoff * attempt)
                    continue
                raise

        if last_err:
            raise last_err

    # default/mock provider
    return _get_mock_recipe(ingredient)
