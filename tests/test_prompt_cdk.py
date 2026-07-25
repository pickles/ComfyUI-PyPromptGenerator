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
