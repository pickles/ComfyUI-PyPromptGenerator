from pyprompt_generator.nodes import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    ResolutionInputNode,
)


def test_input_and_output_definitions():
    input_types = ResolutionInputNode.INPUT_TYPES()

    assert input_types["required"]["width"][0] == "INT"
    assert input_types["required"]["height"][0] == "INT"
    assert input_types["required"]["swap"] == ("BOOLEAN", {"default": False})
    assert ResolutionInputNode.RETURN_TYPES == ("INT", "INT")
    assert ResolutionInputNode.RETURN_NAMES == ("width", "height")


def test_execute_without_swap():
    assert ResolutionInputNode().execute(1024, 768, False) == (1024, 768)


def test_execute_with_swap():
    assert ResolutionInputNode().execute(1024, 768, True) == (768, 1024)


def test_node_is_registered():
    assert NODE_CLASS_MAPPINGS["ResolutionInputNode"] is ResolutionInputNode
    assert NODE_DISPLAY_NAME_MAPPINGS["ResolutionInputNode"] == "Resolution Input"
