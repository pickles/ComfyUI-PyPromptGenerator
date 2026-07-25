"""Generate a scene with reusable and conditional dimensions."""

import importlib
import sys


if "prompt_cdk" in sys.modules:
    prompt_cdk = importlib.reload(sys.modules["prompt_cdk"])
else:
    import prompt_cdk

if "shared_dimensions" in sys.modules:
    shared_dimensions = importlib.reload(sys.modules["shared_dimensions"])
else:
    import shared_dimensions

PromptProgram = prompt_cdk.PromptProgram
option = prompt_cdk.option

SEED = None

program = PromptProgram("ConditionalScene")
program.dimension(
    "situation",
    option("beach", "sunny beach"),
    option("living", "cozy living room"),
)

girl = program.block("girl", "girl")
girl.dimension(shared_dimensions.HAIR_LENGTH)
girl.dimension(shared_dimensions.FACE_EXPRESSION)

girl.when("program.situation", key="beach").dimension(
    "action",
    option("beach_bed", "sitting on a beach bed"),
)
girl.when("program.situation", key="living").dimension(
    "action",
    option("sofa", "sitting on a sofa"),
)

program.when("situation", key="living").dimension(
    "room",
    option("coffee", "coffee cup on the table"),
)

scene = program.synth(seed=SEED)
positive_prompt = scene.prompt(prefix="masterpiece, best quality")
negative_prompt = scene.negative_prompt("low quality, blurry")

print(f"[{program.name}] selection: {scene.summary()}")
print(f"[{program.name}] positive: {positive_prompt}")
print(f"[{program.name}] negative: {negative_prompt}")
