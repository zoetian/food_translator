from pydantic import BaseModel


class IdentifyResponse(BaseModel):
    food_name: str
    translated_name: str | None = None
    target_language: str | None = None
    food_visual_description: str
    match_explanation: str
    confidence: str
    image_url: str | None = None
