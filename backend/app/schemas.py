from pydantic import BaseModel


class IdentifyResponse(BaseModel):
    dish_name: str
    translated_name: str | None = None
    target_language: str | None = None
    description: str
    # likely_ingredients: list[str] = []  # paused: not used currently
    confidence: str
    image_url: str | None = None
