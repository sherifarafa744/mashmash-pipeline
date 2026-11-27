"""Shared character + style constants so every episode's art stays on-model."""

CHARACTER = (
    "Basbusa: a chubby ginger-orange female cartoon cat with a cream-colored "
    "belly and muzzle, big round amber eyes, a small pink nose, and a "
    "signature tiny blue scarf around her neck"
)
STYLE = (
    "flat children's-book illustration, bold clean outlines, warm saturated "
    "colors, soft cel shading, vertical composition, no text, no watermark"
)
ZAEER = "a big drooling gray bulldog with a spiked collar, comedic not scary"


DISTINCT = (
    "Basbusa is ALWAYS the only ginger-orange cat, the smallest character, the only one with a blue scarf, and she NEVER wears an eye patch, bell or robe. "
    "Every other character must look clearly different from her: different fur color (not orange), different size, different outfit or accessory, kept the same in every scene."
)


def image_prompt(scene_description: str) -> str:
    return f"{CHARACTER}. {DISTINCT} Scene: {scene_description}. {STYLE}."
