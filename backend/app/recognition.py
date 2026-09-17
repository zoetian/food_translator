import base64
import json

from openai import OpenAI

from .config import settings
from .schemas import IdentifyResponse

_client = OpenAI(api_key=settings.openai_api_key)

_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "dish_name": {"type": "string"},
        "translated_name": {"type": ["string", "null"]},
        "target_language": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "likely_ingredients": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "dish_name",
        "translated_name",
        "target_language",
        "description",
        "likely_ingredients",
        "confidence",
    ],
    "additionalProperties": False,
}


def identify_dish(image_bytes: bytes, content_type: str, target_language: str) -> IdentifyResponse:
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64_image}"

    response = _client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a playful visual food-association assistant. "
                            "The image may contain food, an animal, a person, an object, "
                            "or an animated character. Your task is NOT limited to identifying "
                            "food that is literally present in the image. "

                            "Instead, examine the subject's shape, colors, texture, pattern, "
                            "softness, and overall visual impression, then imagine the food "
                            "or dessert it most resembles. Always provide a food association, "
                            "even when the image contains no actual food. "

                            "Ignore the subject's proper name, franchise, job, and scene context. "
                            "Do not use the name of a known character in the result. "

                            "Focus only on visible shape, color, pattern, and apparent texture. "
                            "Privately consider at least three food candidates, then select the one "
                            "that explains the greatest number of distinct visual features. "
                            "Prefer a specific, imaginative association over generic choices such as "
                            "'cream puff', 'cupcake', or 'donut'. "

                            "The final name must follow this general pattern: "
                            "'[visual or flavor modifier] + [specific food] + [generic subject type]'. "
                            "For animals, use the species rather than the character's proper name. "
                            "Output only the best candidate."

                            "Explain the visual resemblance in a playful but concise way. "
                            f"Translate the result into {target_language}. "

                            "For example, a round, fluffy, tan-and-brown spotted cheetah might resemble "
                            "a sesame mochi bun and could be called a 'Sesame Mochi Bun Cheetah'. "
                            "Do not respond with 'no dish detected' merely because the subject is not edible."
                        )
                    },
                    {"type": "input_image", "image_url": data_url, "detail": "auto"},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "dish_identification",
                "schema": _JSON_SCHEMA,
                "strict": True,
            }
        },
    )

    return IdentifyResponse(**json.loads(response.output_text))
