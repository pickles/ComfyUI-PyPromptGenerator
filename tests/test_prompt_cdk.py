from random import choice
from time import perf_counter

import pytest

from sample_scripts.prompt_cdk import PromptProgram, dimension, option


def _conditional_chain_stress_program():
    program = PromptProgram("ConditionalChainStress")
    keys = [f"key{index}" for index in range(5)]
    program.dimension("root", *(option(key, key) for key in keys))
    previous = "root"
    for level in range(7):
        current = f"level{level}"
        for key in keys:
            program.when(previous, key=key).dimension(
                current,
                *(option(next_key, next_key) for next_key in keys),
            )
        previous = current
    for key in keys:
        program.when(previous, key=key).dimension(
            "last", option("x", "last x")
        )
    program.when("last", key="x").dimension(
        "detail", option("first", "first detail")
    )
    program.when("last", key="y").dimension(
        "detail", option("second", "second detail")
    )
    return program


def test_synth_handles_large_cartesian_product_without_materializing_it():
    program = PromptProgram("LargeProduct")
    for dimension_index in range(20):
        program.dimension(
            f"dimension_{dimension_index}",
            *(option(f"option_{option_index}", str(option_index))
              for option_index in range(10)),
        )

    first = program.synth(seed=123)
    second = program.synth(seed=123)

    assert len(first.selection) == 20
    assert first.summary() == second.summary()


def test_conditional_branch_weights_keep_raw_product_weighting():
    program = PromptProgram("ConditionalWeights")
    program.dimension(
        "context", option("small", "small"), option("large", "large")
    )
    program.when("context", key="small").dimension(
        "detail", option("small_detail", "small detail", weight=1)
    )
    program.when("context", key="large").dimension(
        "detail",
        option("large_detail_a", "large detail a", weight=1),
        option("large_detail_b", "large detail b", weight=9),
    )

    large_count = sum(
        program.synth(seed=seed).summary()["context"] == "large"
        for seed in range(1_000)
    )

    assert 800 < large_count < 980


def test_reachable_overlap_is_rejected_before_random_sampling():
    program = PromptProgram("PartiallyOverlappingConditional")
    program.dimension(
        "context",
        *(option(f"safe{index}", f"safe {index}") for index in range(99)),
        option("overlap", "overlap"),
    )
    program.when("context", key="overlap").dimension(
        "detail", option("first", "first detail")
    )
    program.when("context", key="overlap").dimension(
        "detail", option("second", "second detail")
    )

    with pytest.raises(ValueError, match=(
        "Multiple conditional branches matched dimension: detail"
    )):
        program.synth(seed=1)


def test_mutually_exclusive_conditional_triggers_do_not_overlap():
    program = PromptProgram("MutuallyExclusiveConditional")
    program.dimension("context", option("a", "A"), option("b", "B"))
    program.when("context", key="a").dimension(
        "first", option("a_only", "first A")
    )
    program.when("context", key="b").dimension(
        "second", option("b_only", "second B")
    )
    program.when("first", key="a_only").dimension(
        "detail", option("a_detail", "detail A")
    )
    program.when("second", key="b_only").dimension(
        "detail", option("b_detail", "detail B")
    )

    scene = program.synth(seed=1)

    assert scene.summary() == {
        "context": "a",
        "first": "a_only",
        "detail": "a_detail",
    }


def test_forward_conditional_branch_is_inactive_at_its_own_position():
    program = PromptProgram("ForwardConditionalBranch")
    program.dimension("root", option("a", "A"))
    program.when("root", key="a").dimension("x", option("x1", "X1"))
    program.when("x", key="x1").dimension("y", option("y1", "Y1"))
    program.when("y", key="y1").dimension("x", option("x2", "X2"))

    assert program.synth(seed=1).summary() == {
        "root": "a",
        "x": "x1",
        "y": "y1",
    }


def test_recursive_forward_conditional_source_is_not_available_for_overlap():
    program = PromptProgram("RecursiveForwardConditional")
    program.dimension("root", option("a", "A"))
    program.when("root", key="a").dimension("source", option("s1", "S1"))
    program.when("source", key="s1").dimension("later", option("l1", "L1"))
    program.when("later", key="l1").dimension("source", option("s2", "S2"))
    program.when("source", key="s2").dimension(
        "detail", option("from_forward", "forward detail")
    )
    program.when("root", key="a").dimension(
        "detail", option("from_root", "root detail")
    )

    assert program.synth(seed=1).summary() == {
        "root": "a",
        "source": "s1",
        "later": "l1",
        "detail": "from_root",
    }


def test_reachable_pair_is_rejected_despite_unreachable_forward_branch():
    program = PromptProgram("MixedConditionalOverlap")
    program.dimension("root", option("a", "A"))
    program.when("root", key="a").dimension("x", option("x1", "X1"))
    program.when("x", key="x1").dimension("y", option("y1", "Y1"))
    program.when("y", key="y1").dimension("x", option("x2", "X2"))
    program.when("x", key="x2").dimension(
        "detail", option("forward", "forward detail")
    )
    program.when("root", key="a").dimension(
        "detail", option("first", "first detail")
    )
    program.when("root", key="a").dimension(
        "detail", option("second", "second detail")
    )

    with pytest.raises(ValueError, match=(
        "Multiple conditional branches matched dimension: detail"
    )):
        program.synth(seed=1)


def test_conditional_overlap_validation_is_bounded_for_branching_chains():
    program = _conditional_chain_stress_program()

    started = perf_counter()
    scene = program.synth(seed=1)

    assert perf_counter() - started < 1.0
    assert scene.summary()["detail"] == "first"


def test_overlap_validation_cache_is_shared_across_branch_pairs(monkeypatch):
    program = _conditional_chain_stress_program()
    calls = 0
    original = program._consume_overlap_validation_work

    def count_work(work):
        nonlocal calls
        calls += 1
        original(work)

    monkeypatch.setattr(program, "_consume_overlap_validation_work", count_work)

    program.synth(seed=1)

    assert calls < 1_000


def test_overlap_validation_limit_fails_closed_before_sampling(monkeypatch):
    program = PromptProgram("OverlapValidationLimit")
    program.dimension("context", option("a", "A"), option("b", "B"))
    program.when("context", key="a").dimension("first", option("a", "A"))
    program.when("context", key="b").dimension("second", option("b", "B"))
    program.when("first", key="a").dimension("detail", option("a", "A"))
    program.when("second", key="b").dimension("detail", option("b", "B"))
    monkeypatch.setattr(program, "_OVERLAP_VALIDATION_WORK_LIMIT", 0)

    with pytest.raises(ValueError, match=(
        "Conditional overlap validation limit exceeded for OverlapValidationLimit"
    )):
        program.synth(seed=1)


def test_extreme_conditional_weight_totals_do_not_underflow_before_logging():
    program = PromptProgram("ExtremeConditionalWeights")
    program.dimension(
        "context", option("small", "small"), option("large", "large")
    )
    program.when("context", key="small").dimension(
        "detail", option("small_detail", "small detail", weight=1e-300)
    )
    program.when("context", key="large").dimension(
        "detail", option("large_detail", "large detail", weight=1e308)
    )

    assert program.synth(seed=1).summary()["context"] in {"small", "large"}


def test_large_unsatisfiable_program_fails_after_bounded_search(monkeypatch):
    program = PromptProgram("SelectiveProgram")
    for dimension_index in range(5):
        program.dimension(
            f"dimension_{dimension_index}",
            *(option(f"option_{option_index}", str(option_index))
              for option_index in range(10)),
        )
    program.when("dimension_0", keys=[f"option_{index}" for index in range(10)]).require(
        "dimension_1", key="missing"
    )
    monkeypatch.setattr(program, "_MAX_PROPOSAL_ATTEMPTS", 1)
    monkeypatch.setattr(program, "_EXACT_FALLBACK_STATE_LIMIT", 10)

    with pytest.raises(ValueError, match=(
        "No candidate found within bounded search for SelectiveProgram"
    )):
        program.synth(seed=1)


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


def test_block_can_add_conditional_dimension_from_program_dimension():
    program = PromptProgram("ConditionalBlocks")
    program.dimension(
        "situation",
        option("beach", "sunny beach"),
        option("living", "cozy living room"),
    )

    girl = program.block("girl", "girl")
    girl.dimension("face", option("smile", "smiling face"))
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

    scenes = [program.synth(seed=seed) for seed in range(20)]
    beach = next(
        scene
        for scene in scenes
        if scene.selection["situation"].key == "beach"
    )
    living = next(
        scene
        for scene in scenes
        if scene.selection["situation"].key == "living"
    )

    assert beach.prompt(prefix="") == (
        "sunny beach,\n"
        "girl,\n"
        "smiling face,\n"
        "sitting on a beach bed"
    )
    assert beach.summary() == {
        "situation": "beach",
        "girl.face": "smile",
        "girl.action": "beach_bed",
    }
    assert living.prompt(prefix="") == (
        "cozy living room,\n"
        "girl,\n"
        "smiling face,\n"
        "sitting on a sofa,\n"
        "coffee cup on the table"
    )
    assert living.summary() == {
        "situation": "living",
        "girl.face": "smile",
        "girl.action": "sofa",
        "room": "coffee",
    }


def test_conditional_dimension_is_absent_when_no_branch_matches():
    program = PromptProgram("InactiveConditional")
    program.dimension("situation", option("studio", "photo studio"))
    girl = program.block("girl", "girl")
    girl.when("program.situation", key="beach").dimension(
        "action",
        option("beach_bed", "sitting on a beach bed"),
    )

    scene = program.synth(seed=1)

    assert scene.prompt(prefix="") == "photo studio,\ngirl"
    assert "girl.action" not in scene.selection
    assert "girl.action" not in scene.summary()


def test_overlapping_conditional_dimension_branches_are_rejected():
    program = PromptProgram("OverlappingConditional")
    program.dimension("situation", option("beach", "sunny beach", "outdoor"))
    girl = program.block("girl", "girl")
    girl.when("program.situation", key="beach").dimension(
        "action",
        option("sitting", "sitting pose"),
    )
    girl.when("program.situation", tag="outdoor").dimension(
        "action",
        option("walking", "walking pose"),
    )

    try:
        program.synth(seed=1)
    except ValueError as error:
        assert str(error) == (
            "Multiple conditional branches matched dimension: girl.action"
        )
    else:
        raise AssertionError("Overlapping conditional branches should fail")


def test_reusable_dimension_can_be_used_by_multiple_blocks():
    hair_length = dimension(
        "hair_length",
        option("short", "short hair"),
        option("long", "long hair"),
    )

    program = PromptProgram("ReusableDimension")
    girl = program.block("girl", "girl")
    girl.dimension(hair_length)
    man = program.block("man", "man")
    man.dimension(hair_length)

    scene = program.synth(seed=1)

    assert set(scene.summary()) == {"girl.hair_length", "man.hair_length"}
    assert scene.selection["girl.hair_length"] in hair_length.options
    assert scene.selection["man.hair_length"] in hair_length.options


def test_reusable_dimension_can_be_used_conditionally():
    actions = dimension(
        "action",
        option("sitting", "sitting pose"),
        option("walking", "walking pose"),
    )
    program = PromptProgram("ReusableConditional")
    program.dimension("situation", option("beach", "sunny beach"))
    girl = program.block("girl", "girl")
    girl.when("program.situation", key="beach").dimension(actions)

    scene = program.synth(seed=1)

    assert scene.summary()["girl.action"] in {"sitting", "walking"}


def test_block_conditional_dimension_chain_keeps_each_branch_together():
    program = PromptProgram("BlockConditionalChain")
    program.dimension(
        "situation",
        option("a", "A situation"),
        option("b", "B situation"),
    )
    girl = program.block("girl", "girl")
    girl.when("program.situation", key="a").dimension(
        "first", option("a1", "A1")
    ).dimension("second", option("a2", "A2"))
    girl.when("program.situation", key="b").dimension(
        "first", option("b1", "B1")
    ).dimension("second", option("b2", "B2"))

    scenes = [program.synth(seed=seed) for seed in range(20)]

    for scene in scenes:
        branch = scene.summary()["situation"].upper()
        assert scene.selection["girl.first"].key == f"{branch.lower()}1"
        assert scene.selection["girl.second"].key == f"{branch.lower()}2"
        assert scene.summary()["girl.first"] == f"{branch.lower()}1"
        assert scene.summary()["girl.second"] == f"{branch.lower()}2"
        assert f"{branch}1" in scene.prompt(prefix="")
        assert f"{branch}2" in scene.prompt(prefix="")


def test_program_conditional_dimension_chain_keeps_each_branch_together():
    program = PromptProgram("ProgramConditionalChain")
    program.dimension(
        "situation",
        option("a", "A situation"),
        option("b", "B situation"),
    )
    program.when("situation", key="a").dimension(
        "first", option("a1", "A1")
    ).dimension("second", option("a2", "A2"))
    program.when("situation", key="b").dimension(
        "first", option("b1", "B1")
    ).dimension("second", option("b2", "B2"))

    for seed in range(20):
        scene = program.synth(seed=seed)
        branch = scene.summary()["situation"]
        assert scene.selection["first"].key == f"{branch}1"
        assert scene.selection["second"].key == f"{branch}2"
        assert scene.summary()["first"] == f"{branch}1"
        assert scene.summary()["second"] == f"{branch}2"


def test_conditional_dimension_chain_supports_reusable_dimensions_and_owner_exit():
    actions = dimension("action", option("a1", "A1"))
    program = PromptProgram("ConditionalChainOwnerExit")
    program.dimension(
        "situation",
        option("a", "A situation"),
        option("b", "B situation"),
    )
    girl = program.block("girl", "girl")
    girl.when("program.situation", key="a").dimension(actions).fixed(
        "after condition"
    ).dimension("always", option("yes", "always present"))

    scenes = [program.synth(seed=seed) for seed in range(20)]
    a_scene = next(scene for scene in scenes if scene.summary()["situation"] == "a")
    b_scene = next(scene for scene in scenes if scene.summary()["situation"] == "b")

    assert a_scene.summary()["girl.action"] == "a1"
    assert a_scene.prompt(prefix="") == (
        "A situation,\n"
        "girl,\n"
        "A1,\n"
        "after condition,\n"
        "always present"
    )
    assert "girl.action" not in b_scene.summary()
    assert b_scene.summary()["girl.always"] == "yes"
    assert b_scene.prompt(prefix="") == (
        "B situation,\n"
        "girl,\n"
        "after condition,\n"
        "always present"
    )


def test_program_namespace_works_for_block_rule_targets():
    program = PromptProgram("ProgramNamespaceTargets")
    program.dimension(
        "situation",
        option("beach", "sunny beach"),
        option("living", "cozy living room"),
    )
    girl = program.block("girl", "girl")
    girl.dimension(
        "pose",
        option("sofa", "sitting on a sofa"),
        option("shore", "walking by the shore"),
    )
    girl.when("pose", key="sofa").require(
        "program.situation",
        key="living",
    )

    for seed in range(20):
        scene = program.synth(seed=seed)
        if scene.selection["girl.pose"].key == "sofa":
            assert scene.selection["situation"].key == "living"
