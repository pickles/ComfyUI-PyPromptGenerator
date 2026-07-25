"""Generate a constrained random image prompt for PyPromptGeneratorNode."""

import importlib
import sys


# PyPromptGeneratorNode adds scripts/ and sample_scripts/ to sys.path.
# Reload the helper so edits take effect without restarting ComfyUI.
if "prompt_cdk" in sys.modules:
    prompt_cdk = importlib.reload(sys.modules["prompt_cdk"])
else:
    import prompt_cdk

PromptProgram = prompt_cdk.PromptProgram
option = prompt_cdk.option


# Set this to an integer for reproducible output, or None for a new result.
SEED = None

program = PromptProgram("CharacterPortrait")

program.fixed(
    [
        "masterpiece, best quality, highly detailed",
        "solo",
    ]
)

woman = program.block("woman", "adult woman")

woman.dimension(
    "hair",
    option("short_bob", "short bob haircut, glossy black hair"),
    option("long_wavy", "long wavy auburn hair"),
    option("ponytail", "high ponytail, chestnut brown hair"),
    option("pixie", "textured pixie cut, platinum blonde hair", weight=0.7),
)

woman.dimension(
    "face",
    option("gentle", "gentle oval face, warm smile, soft features"),
    option("sharp", "defined facial features, confident expression"),
    option("freckled", "round face, light freckles, bright eyes"),
)

woman.dimension(
    "body",
    option("slender", "slender build"),
    option("athletic", "athletic build"),
    option("curvy", "curvy build"),
)

woman.dimension(
    "outfit",
    option(
        "one_piece_swimsuit",
        "elegant one-piece swimsuit, lightweight beach cover-up",
        "swimwear",
        "beachwear",
        negative="winter coat, business suit",
    ),
    option(
        "rash_guard",
        "sporty rash guard and swim shorts",
        "swimwear",
        "beachwear",
        negative="winter coat, formal dress",
    ),
    option(
        "casual",
        "comfortable knit sweater and jeans",
        "casual",
        negative="swimsuit, swimwear",
    ),
    option(
        "summer_dress",
        "light summer dress and sandals",
        "casual",
        "outdoor",
        negative="winter coat, heavy clothing",
    ),
    option(
        "activewear",
        "modern athletic wear and sneakers",
        "sport",
        negative="formal wear, evening gown",
    ),
)

woman.dimension(
    "pose",
    option("standing", "relaxed standing pose, looking at viewer"),
    option("walking", "natural walking pose"),
    option(
        "shore_walk",
        "walking along the shoreline",
        "shore",
        negative="indoor pose, sitting on furniture",
    ),
    option(
        "sofa",
        "relaxing on a sofa",
        "sofa",
        negative="standing pose, walking pose",
    ),
    option("stretch", "light stretching pose", "sport"),
)

program.break_()

program.dimension(
    "location",
    option(
        "beach",
        "sunny beach, blue ocean, gentle waves, golden hour",
        "beach",
        "outdoor",
        negative="indoor, living room, studio background",
    ),
    option(
        "living_room",
        "cozy modern living room, warm window light",
        "living_room",
        "indoor",
        "home",
        negative="beach, ocean, outdoor background",
    ),
    option(
        "cafe",
        "stylish quiet cafe, soft ambient light",
        "indoor",
        negative="beach, ocean, home interior",
    ),
    option(
        "park",
        "green city park, dappled sunlight",
        "outdoor",
        negative="indoor, studio background",
    ),
    option(
        "studio",
        "minimal photography studio, softbox lighting",
        "indoor",
        negative="outdoor scenery, beach, home interior",
    ),
)


# CDK-like declarative constraints:
# A beach scene always uses swimwear.
program.when("location", tag="beach").require("woman.outfit", tag="swimwear")

# Swimwear is only valid at the beach, and never in indoor locations.
program.when("woman.outfit", tag="swimwear").require("location", tag="beach")
program.when("location", tag="indoor").forbid("woman.outfit", tag="swimwear")

# Location-specific poses.
program.when("woman.pose", tag="shore").require("location", tag="beach")
program.when("woman.pose", tag="sofa").require("location", key="living_room")

# A sporty stretch should use activewear.
program.when("woman.pose", tag="sport").require("woman.outfit", key="activewear")


scene = program.synth(seed=SEED)

positive_prompt = scene.prompt(prefix="")
negative_prompt = scene.negative_prompt(
    "low quality, worst quality, blurry, bad anatomy, bad hands, "
    "extra fingers, missing fingers, deformed, text, watermark"
)

print(f"[{program.name}] selection: {scene.summary()}")
print(f"[{program.name}] positive: {positive_prompt}")
print(f"[{program.name}] negative: {negative_prompt}")
