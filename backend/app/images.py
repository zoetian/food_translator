from openai import OpenAI

from .config import settings

_client = OpenAI(api_key=settings.openai_api_key)


def generate_dish_image(dish_name: str, description: str) -> str | None:
    try:
        response = _client.images.generate(
            model=settings.openai_image_model,
            prompt=(
                f"A fun, appetizing illustration of '{dish_name}': {description} "
                "Bright, playful food photography style."
            ),
            size="1024x1024",
            n=1,
        )
    except Exception:
        return None

    if not response.data or not response.data[0].b64_json:
        return None

    return f"data:image/png;base64,{response.data[0].b64_json}"
