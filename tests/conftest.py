"""
Pytest configuration and fixtures for ComfyUI Prompt Generator tests
"""

import pytest
import sys
import os
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def choice_function():
    """Fixture providing the choice function for testing"""
    from src.pyprompt_generator.utils import choice
    return choice


@pytest.fixture
def prompt_generator_node():
    """Fixture providing a PyPromptGeneratorNode instance"""
    from src.pyprompt_generator.nodes import PyPromptGeneratorNode
    return PyPromptGeneratorNode()


@pytest.fixture
def file_generator_node():
    """Fixture providing a PyPromptFileGeneratorNode instance"""
    from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
    return PyPromptFileGeneratorNode()


@pytest.fixture
def sample_scripts():
    """Fixture providing sample scripts for testing"""
    return {
        "simple": """
positive_prompt = "beautiful landscape"
negative_prompt = "ugly, blurry"
""",
        "basic": """
positive_prompt = "A beautiful landscape"
negative_prompt = "low quality, blurry"
""",
        "with_choice": """
options = ["sunny day", "cloudy sky", "starry night"]
positive_prompt = choice(options)
negative_prompt = "low quality"
""",
        "choice_function": """
styles = ["realistic", "anime"]
style = choice(styles)
positive_prompt = f"A {style} artwork"
negative_prompt = "low quality"
""",
        "weighted_choice": """
styles = ["10::realistic", "1::anime"]
results = []
for i in range(100):
    style = choice(styles)
    results.append(style)

realistic_count = results.count("realistic")
anime_count = results.count("anime")

positive_prompt = f"Realistic: {realistic_count}, Anime: {anime_count}"
negative_prompt = "test"
""",
        "multiple_choice": """
items = ["a", "b", "c", "d", "e"]
selected = choice(items, 3)
positive_prompt = f"Selected: {', '.join(selected)}"
negative_prompt = "test"
""",
        "error_script": """
# This will cause an error
invalid_variable_that_does_not_exist
positive_prompt = "This won't be reached"
negative_prompt = "This won't be reached"
"""
    }


@pytest.fixture(autouse=True)
def set_random_seed():
    """Set random seed for reproducible tests"""
    import random
    random.seed(42)
    yield
    # Reset after test
    import time
    random.seed(time.time())
