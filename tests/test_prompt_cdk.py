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
        assert str(error) == "break_() must be followed by a dimension"
    else:
        raise AssertionError("Trailing break_() should fail")
