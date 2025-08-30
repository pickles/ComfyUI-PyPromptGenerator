# Sample Scripts for PyPrompt File Generator

This directory contains sample Python scripts that demonstrate how to use the PyPrompt File Generator node.

## Files

### `prompt_script.py`
Basic example showing how to:
- Use utility functions like `choice()`, `maybe()`, and `join()`
- Create conditional prompt elements
- Compose prompts from multiple components

### `advanced_script.py`
Advanced example demonstrating:
- Wildcard variable usage (`_styles`, `_colors`, etc.)
- Weighted choice selection
- Complex prompt composition with effects
- Random number generation and boolean logic

## Usage

1. In ComfyUI, add a "PyPrompt File Generator" node
2. Set the `script_file` parameter to one of these sample files:
   - `tests/sample_scripts/prompt_script.py`
   - `tests/sample_scripts/advanced_script.py`
3. Optionally set `base_path` to the project root directory
4. Execute the node to generate prompts from the script

## Available Functions

All utility functions from the main PyPrompt library are available:

- `choice(items, count=1)` - Random selection with optional weighting
- `weighted_choice(items, count=1)` - Alias for choice with weights
- `shuffle_list(items)` - Shuffle a list randomly
- `random_range(min_val, max_val)` - Generate random integer
- `random_boolean(probability=0.5)` - Random true/false
- `join(items, separator=', ')` - Join items into string
- `flatten(nested_list, depth=None)` - Flatten nested lists
- `maybe(item, probability=0.5)` - Conditionally return item

## Wildcard Variables

If wildcard files exist in the `wildcard/` directory, they are automatically loaded as variables:
- `_styles` - from `styles.txt`
- `_colors` - from `colors.txt`
- `_subjects` - from `subjects.txt`
- etc.

## Creating Your Own Scripts

1. Create a new `.py` file
2. Use any of the available utility functions
3. Set `positive` and `negative` variables for the prompt outputs
4. Optionally use `print()` for debugging information

The script will be executed in a safe environment with access to utility functions and wildcard variables.
