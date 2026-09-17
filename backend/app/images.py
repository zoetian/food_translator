from openai import OpenAI

from .config import settings

_client = OpenAI(api_key=settings.openai_api_key)

def generate_dish_image(food_name: str, food_visual_description: str) -> str | None:
    try:
        response = _client.images.generate(
            model=settings.openai_image_model,
            prompt=(
                f"Create an appetizing image of one edible {food_name}. "
                f"{food_visual_description} "
                "Show food only. "
                "Do not include animals, people, characters, mascots, faces, "
                "eyes, mouths, ears, paws, fur, facial expressions, or "
                "anthropomorphic features. "
                "Bright, playful, polished food photography."
            ),
            size="1024x1024",
            n=1,
        )
    except Exception:
        return None

    if not response.data or not response.data[0].b64_json:
        return None

    return f"data:image/png;base64,{response.data[0].b64_json}"
