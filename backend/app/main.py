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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/identify", response_model=IdentifyResponse)
async def identify(
    photo: UploadFile = File(...),
    target_language: str = Form("English"),
) -> IdentifyResponse:
    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")

    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = identify_dish(image_bytes, photo.content_type, target_language)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recognition failed: {exc}") from exc

    result.image_url = generate_dish_image(result.food_name, result.food_visual_description)
    return result
