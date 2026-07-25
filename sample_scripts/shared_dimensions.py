"""Reusable prompt dimensions shared by multiple generation scripts."""

from prompt_cdk import dimension, option


HAIR_LENGTH = dimension(
    "hair_length",
    option("short", "short hair"),
    option("medium", "medium-length hair"),
    option("long", "long hair"),
)

FACE_EXPRESSION = dimension(
    "face",
    option("smile", "smiling face"),
    option("serious", "serious expression"),
    option("crying", "crying face"),
)
