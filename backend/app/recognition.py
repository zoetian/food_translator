import base64
import json

from openai import OpenAI

from .config import settings
from .schemas import IdentifyResponse

_client = OpenAI(api_key=settings.openai_api_key)

_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "food_name": {"type": "string"},
        "translated_name": {"type": ["string", "null"]},
        "target_language": {"type": ["string", "null"]},
        "food_visual_description": {"type": "string"},
        "match_explanation": {"type": "string"},
        # "likely_ingredients": {
        #     "type": "array",
        #     "items": {"type": "string"},
        # },
        # paused: not used currently
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
    },
    "required": [
        "food_name",
        "translated_name",
        "target_language",
        "food_visual_description",
        "match_explanation",
        # "likely_ingredients", # paused: not used currently
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

                            "The food_name field must contain only the name of an edible food or dish. "
                            "Never include the source subject, animal species, person, character, object, "
                            "franchise, or profession in food_name. "

                            "The food_visual_description field must describe only the generated food's "
                            "appearance, including its shape, color, texture, filling, toppings, and "
                            "presentation. It must not mention the source image, animals, people, body "
                            "parts, faces, fur, characters, or expressions. "

                            "Use match_explanation separately to explain why the original subject visually "
                            "resembles the selected food. This field may mention features of the original "
                            "subject, but it will never be sent to the image generation model. "
                            "Output only the best candidate."

                            "Explain the visual resemblance in a playful but concise way. "
                            f"Translate the result into {target_language}. "

                            "# Example:\n"
                            "food_name: Caramel-Dotted Mochi Bun\n"
                            "food_visual_description: A round, golden-brown mochi bun with a soft, puffy "
                            "surface and small dark caramelized spots.\n"
                            "match_explanation: The subject's round cheeks resemble soft mochi buns, "
                            "while the warm coloring and dark spots resemble caramelized toppings.\n"
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
