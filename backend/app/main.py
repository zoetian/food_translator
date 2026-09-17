import hashlib
import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .images import generate_dish_image
from .recognition import identify_dish
from .schemas import IdentifyResponse

app = FastAPI(title="Food Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Cache so repeat/duplicate photo uploads skip the paid OpenAI calls, persisted
# to a local JSON file so it survives `--reload` restarts during dev. No size
# cap — fine for local dev, but revisit with a real store before real traffic.
_CACHE_FILE = Path(__file__).resolve().parent.parent / ".cache" / "identify_cache.json"


def _load_cache() -> dict[str, IdentifyResponse]:
    if not _CACHE_FILE.exists():
        return {}
    try:
        raw = json.loads(_CACHE_FILE.read_text())
        return {key: IdentifyResponse(**value) for key, value in raw.items()}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def _save_cache() -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw = {key: value.model_dump() for key, value in _result_cache.items()}
    _CACHE_FILE.write_text(json.dumps(raw))


_result_cache: dict[str, IdentifyResponse] = _load_cache()

# Daily cap on paid OpenAI calls (cache hits above don't count against it).
# Counter lives in memory only, so it resets on restart as well as at midnight.
_request_count = 0
_request_count_date = date.today()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/identify", response_model=IdentifyResponse)
async def identify(
    photo: UploadFile = File(...),
    target_language: str = Form("English"),
) -> IdentifyResponse:
    global _request_count, _request_count_date

    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")

    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    cache_key = f"{hashlib.sha256(image_bytes).hexdigest()}:{target_language}"
    if cache_key in _result_cache:
        return _result_cache[cache_key]

    today = date.today()
    if today != _request_count_date:
        _request_count_date = today
        _request_count = 0

    if _request_count >= settings.daily_request_cap:
        raise HTTPException(
            status_code=429,
            detail="Daily request limit reached. Please try again tomorrow.",
        )
    _request_count += 1

    try:
        result = identify_dish(image_bytes, photo.content_type, target_language)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recognition failed: {exc}") from exc

    result.image_url = generate_dish_image(result.food_name, result.food_visual_description)
    _result_cache[cache_key] = result
    _save_cache()
    return result
