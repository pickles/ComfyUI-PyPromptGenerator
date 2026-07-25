from random import choice

from sample_scripts.prompt_cdk import PromptProgram, option


def test_prompt_renders_each_option_on_its_own_line():
    program = PromptProgram("Multiline")
    program.dimension(
        "character",
        option("hero", "brave hero", negative="villain"),
    )
    program.dimension(
        "location",
        option("forest", "enchanted forest", negative="city"),
    )

    scene = program.synth(seed=1)

    assert scene.prompt("best quality") == (
        "best quality,\n"
        "brave hero,\n"
        "enchanted forest"
    )
    assert scene.negative_prompt("low quality") == (
        "low quality,\n"
        "villain,\n"
        "city"
    )


def test_option_accepts_string_list():
    program = PromptProgram("OptionList")
    program.dimension(
        "character",
        option(
            "hero",
            ["adult woman", "short bob haircut", "athletic build"],
        ),
    )

    scene = program.synth(seed=1)

    assert scene.prompt(prefix="") == (
        "adult woman,\n"
        "short bob haircut,\n"
        "athletic build"
    )


def test_option_list_can_contain_preselected_choices():
    program = PromptProgram("OptionChoices")
    program.dimension(
        "character",
        option(
            "hero",
            [
                "adult woman",
                choice(["short bob haircut"]),
                choice(["athletic build"]),
            ],
        ),
    )

    scene = program.synth(seed=1)

    assert scene.prompt(prefix="") == (
        "adult woman,\n"
        "short bob haircut,\n"
        "athletic build"
    )


def test_option_rejects_non_string_list_items():
    try:
        option("invalid", ["valid fragment", 123])
    except TypeError as error:
        assert str(error) == (
            "option() accepts a string or a list of strings"
        )
    else:
        raise AssertionError("Non-string option fragments should fail")


def test_dimension_can_insert_break_before_selected_option():
    program = PromptProgram("DimensionBreak")
    program.dimension("character", option("hero", "brave hero"))
    program.dimension(
        "location",
        option("forest", "enchanted forest"),
        break_before=True,
    )

    scene = program.synth(seed=1)

    assert scene.prompt() == (
        "masterpiece, best quality, solo,\n"
        "brave hero,\n"
        "BREAK\n"
        "enchanted forest"
    )


def test_individual_option_can_insert_break():
    program = PromptProgram("OptionBreak")
    program.dimension(
        "weather",
        option("rain", "gentle rain", break_before=True),
    )

    scene = program.synth(seed=1)

    assert scene.prompt("cinematic") == (
        "cinematic,\n"
        "BREAK\n"
        "gentle rain"
    )


def test_break_method_inserts_break_before_next_dimension():
    program = PromptProgram("ExplicitBreak")
    program.dimension("character", option("hero", "brave hero"))
    program.break_()
    program.dimension("location", option("forest", "enchanted forest"))

    scene = program.synth(seed=1)

    assert scene.prompt("cinematic") == (
        "cinematic,\n"
        "brave hero,\n"
        "BREAK\n"
        "enchanted forest"
    )


def test_break_method_requires_following_dimension():
    program = PromptProgram("TrailingBreak")
    program.dimension("character", option("hero", "brave hero"))
    program.break_()

    try:
        program.synth(seed=1)
    except ValueError as error:
        assert str(error) == "break_() must be followed by prompt content"
    else:
        raise AssertionError("Trailing break_() should fail")


def test_fixed_accepts_string_and_string_list():
    program = PromptProgram("Fixed")
    program.fixed("masterpiece")
    program.fixed(["best quality", "highly detailed"])

    scene = program.synth(seed=1)

    assert scene.prompt(prefix="") == (
        "masterpiece,\n"
        "best quality,\n"
        "highly detailed"
    )


def test_blocks_keep_each_character_and_attributes_together():
    program = PromptProgram("TwoCharacters")
    woman = program.block("woman", ["girl", "adult woman"])
    woman.dimension("hair", option("bob", "short bob haircut"))
    woman.dimension("body", option("slender", "slender body"))

    program.break_()

    man = program.block("man", "boy")
    man.dimension("hair", option("short", "short black hair"))
    man.dimension("body", option("athletic", "athletic body"))

    scene = program.synth(seed=1)

    assert scene.prompt(prefix="") == (
        "girl,\n"
        "adult woman,\n"
        "short bob haircut,\n"
        "slender body,\n"
        "BREAK\n"
        "boy,\n"
        "short black hair,\n"
        "athletic body"
    )
    assert scene.summary() == {
        "woman.hair": "bob",
        "woman.body": "slender",
        "man.hair": "short",
        "man.body": "athletic",
    }


def test_block_constraints_use_local_dimension_names():
    program = PromptProgram("BlockConstraints")
    woman = program.block("woman", "girl")
    woman.dimension(
        "outfit",
        option("swimsuit", "one-piece swimsuit", "swimwear"),
        option("casual", "sweater and jeans", "casual"),
    )
    woman.dimension(
        "location",
        option("beach", "sunny beach", "beach"),
        option("home", "living room", "indoor"),
    )
    woman.when("location", tag="beach").require("outfit", tag="swimwear")
    woman.when("location", tag="indoor").forbid("outfit", tag="swimwear")

    for seed in range(50):
        scene = program.synth(seed=seed)
        selection = scene.selection
        if selection["woman.location"].has_tag("beach"):
            assert selection["woman.outfit"].has_tag("swimwear")
        if selection["woman.location"].has_tag("indoor"):
            assert not selection["woman.outfit"].has_tag("swimwear")


def test_multiple_tags_can_match_all():
    program = PromptProgram("AllTags")
    program.dimension(
        "location",
        option("beach", "sunny beach", "beach", "outdoor"),
        option("pool", "indoor pool", "pool", "indoor"),
    )
    program.dimension(
        "outfit",
        option("swimsuit", "one-piece swimsuit", "swimwear"),
        option("casual", "sweater and jeans", "casual"),
    )
    program.when(
        "location",
        tags=["beach", "outdoor"],
        match="all",
    ).require("outfit", tag="swimwear")

    for seed in range(50):
        scene = program.synth(seed=seed)
        location = scene.selection["location"]
        if location.key == "beach":
            assert scene.selection["outfit"].has_tag("swimwear")


def test_multiple_tags_can_match_any():
    program = PromptProgram("AnyTags")
    program.dimension(
        "location",
        option("home", "living room", "home", "indoor"),
        option("cafe", "quiet cafe", "cafe", "indoor"),
        option("park", "green park", "park", "outdoor"),
    )
    program.dimension(
        "outfit",
        option("swimsuit", "one-piece swimsuit", "swimwear"),
        option("casual", "sweater and jeans", "casual"),
    )
    program.when(
        "location",
        tags=["home", "cafe"],
        match="any",
    ).forbid("outfit", tag="swimwear")

    for seed in range(75):
        scene = program.synth(seed=seed)
        location = scene.selection["location"]
        if location.has_tag("home") or location.has_tag("cafe"):
            assert not scene.selection["outfit"].has_tag("swimwear")


def test_require_target_supports_multiple_tags():
    program = PromptProgram("RequiredTags")
    program.dimension(
        "location",
        option("beach", "sunny beach", "beach"),
    )
    program.dimension(
        "outfit",
        option("swimsuit", "one-piece swimsuit", "swimwear", "beachwear"),
        option("costume", "stage costume", "swimwear", "costume"),
    )
    program.when("location", tag="beach").require(
        "outfit",
        tags=["swimwear", "beachwear"],
        match="all",
    )

    for seed in range(20):
        scene = program.synth(seed=seed)
        assert scene.selection["outfit"].key == "swimsuit"


def test_tag_and_tags_cannot_be_used_together():
    program = PromptProgram("InvalidTags")
    program.dimension("location", option("beach", "sunny beach", "beach"))

    try:
        program.when("location", tag="beach", tags=["outdoor"])
    except ValueError as error:
        assert str(error) == "Use either tag or tags, not both"
    else:
        raise AssertionError("Using tag and tags together should fail")


def test_match_must_be_all_or_any():
    program = PromptProgram("InvalidMatch")
    program.dimension("location", option("beach", "sunny beach", "beach"))

    try:
        program.when("location", tags=["beach"], match="none")
    except ValueError as error:
        assert str(error) == "match must be 'all' or 'any'"
    else:
        raise AssertionError("Invalid match mode should fail")


def test_multiple_keys_match_any_selected_key():
    program = PromptProgram("MultipleKeys")
    program.dimension(
        "location",
        option("home", "living room"),
        option("cafe", "quiet cafe"),
        option("beach", "sunny beach"),
    )
    program.dimension(
        "outfit",
        option("swimsuit", "one-piece swimsuit", "swimwear"),
        option("casual", "sweater and jeans", "casual"),
    )
    program.when(
        "location",
        keys=["home", "cafe"],
    ).forbid("outfit", key="swimsuit")

    for seed in range(75):
        scene = program.synth(seed=seed)
        if scene.selection["location"].key in {"home", "cafe"}:
            assert scene.selection["outfit"].key != "swimsuit"


def test_require_target_supports_multiple_keys():
    program = PromptProgram("RequiredKeys")
    program.dimension("location", option("beach", "sunny beach"))
    program.dimension(
        "outfit",
        option("one_piece", "one-piece swimsuit"),
        option("rash_guard", "rash guard"),
        option("casual", "sweater and jeans"),
    )
    program.when("location", key="beach").require(
        "outfit",
        keys=["one_piece", "rash_guard"],
    )

    for seed in range(30):
        scene = program.synth(seed=seed)
        assert scene.selection["outfit"].key in {"one_piece", "rash_guard"}


def test_keys_and_tags_are_combined_with_and():
    program = PromptProgram("KeysAndTags")
    program.dimension(
        "location",
        option("beach", "sunny beach", "outdoor"),
        option("indoor_beach", "indoor artificial beach", "indoor"),
        option("park", "green park", "outdoor"),
    )
    program.dimension(
        "weather",
        option("sunny", "sunny weather"),
        option("rain", "rainy weather"),
    )
    program.when(
        "location",
        keys=["beach", "indoor_beach"],
        tag="outdoor",
    ).require("weather", key="sunny")

    for seed in range(75):
        scene = program.synth(seed=seed)
        location = scene.selection["location"]
        if location.key in {"beach", "indoor_beach"} and location.has_tag("outdoor"):
            assert scene.selection["weather"].key == "sunny"


def test_key_and_keys_cannot_be_used_together():
    program = PromptProgram("InvalidKeys")
    program.dimension("location", option("beach", "sunny beach"))

    try:
        program.when("location", key="beach", keys=["cafe"])
    except ValueError as error:
        assert str(error) == "Use either key or keys, not both"
    else:
        raise AssertionError("Using key and keys together should fail")
