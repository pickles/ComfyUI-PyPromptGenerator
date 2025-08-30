# PyPromptGenerator

A powerful custom node for ComfyUI that enables dynamic prompt generation using Python scripts. This extension allows you to create sophisticated positive and negative prompts through scripting, offering more flexibility and control than traditional static prompts.

Perfect for scenarios where you need:
- **Conditional prompt generation** - Add complementary negative terms based on positive content
- **Weighted random selection** - Choose prompt elements with specific probabilities
- **Complex prompt logic** - Use Python's full power instead of learning template languages
- **File-based prompts** - Load and execute prompt scripts from external files
- **Dynamic wildcard support** - Advanced wildcard expansion with caching

## Installation

### Option 1: ComfyUI Manager (Recommended)
1. Install [ComfyUI](https://docs.comfy.org/get_started)
2. Install [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
3. Search for "PyPromptGenerator" in ComfyUI-Manager and install
4. Restart ComfyUI

### Option 2: Manual Installation
1. Navigate to your ComfyUI installation directory
2. Go to `custom_nodes/` folder
3. Clone this repository:
   ```bash
   git clone https://github.com/pickles/ComfyUI-PyPromptGenerator.git
   ```
4. Restart ComfyUI

## Features

### 🎯 **PyPromptGenerator Node**
- **Inline Python Scripts**: Write prompt generation logic directly in the node
- **Rich Utility Functions**: Built-in functions for weighted selection, list manipulation, and randomization
- **Always Refresh**: Option to regenerate prompts on every execution
- **Safe Execution**: Sandboxed environment with controlled access to Python functionality

### 📁 **PyPromptFileGenerator Node**
- **External Script Files**: Load and execute Python scripts from files
- **Hot Reload**: Automatically detects file changes and reloads scripts
- **Organized Workflows**: Keep complex prompt logic in separate, reusable files
- **Version Control**: Track and manage prompt scripts in your project

### 🛠 **Powerful Utility Functions**
All nodes include access to specialized utility functions:

- **`choice(items, count=1)`** - Random selection with weighted support
  ```python
  # Basic selection
  choice(["red", "blue", "green"])
  
  # Weighted selection (red is 3x more likely)
  choice(["3::red", "1::blue", "1::green"])
  
  # Multiple selections (no duplicates)
  choice(["cat", "dog", "bird"], count=2)
  ```

- **`weighted_choice(items, weights=None)`** - Advanced weighted selection
- **`shuffle_list(items)`** - Randomize list order without modifying original
- **`random_range(min, max, step=1)`** - Generate random numbers in range
- **`random_boolean(probability=0.5)`** - Random true/false with custom probability
- **`join(items, separator=", ")`** - Smart joining with BREAK support
- **`maybe(value, probability=0.5)`** - Conditionally include content
- **`flatten(nested_list, depth=None)`** - Flatten nested structures with empty filtering

### 🃏 **Advanced Wildcard Support**
- **Dynamic Loading**: Automatically load wildcard files from directories
- **Caching**: Efficient wildcard processing with smart caching
- **Nested Support**: Use wildcards within wildcards for complex structures

### 🔧 **Developer Features**
- **Comprehensive Tests**: Full test suite with 60+ test cases
- **Type Safety**: MyPy compatible with proper type hints
- **Code Quality**: Ruff linting and pre-commit hooks
- **Documentation**: Extensive inline documentation and examples

## Usage Examples

### Basic Prompt Generation
```python
# Simple conditional prompt
if random_boolean(0.7):
    positive_prompt = "beautiful landscape, " + choice(["sunset", "sunrise", "noon"])
else:
    positive_prompt = "portrait, " + choice(["smiling", "serious", "contemplative"])

negative_prompt = "blurry, low quality"
```

### Weighted Selection
```python
# Characters with different rarities
character = choice([
    "10::warrior",    # Common (10x weight)
    "5::mage",        # Uncommon (5x weight) 
    "1::dragon"       # Rare (1x weight)
])

positive_prompt = f"{character}, fantasy art"
negative_prompt = "modern, realistic"
```

### Complementary Negatives
```python
# Auto-generate negative terms based on positive content
styles = ["anime", "realistic", "cartoon", "oil painting"]
chosen_style = choice(styles)

positive_prompt = f"{chosen_style} style, beautiful woman"

# Add opposite styles to negative
other_styles = [s for s in styles if s != chosen_style]
negative_prompt = join(other_styles) + ", ugly, deformed"
```

### Complex Logic with File-based Scripts
Create a file `advanced_portrait.py`:
```python
# Define character archetypes
archetypes = {
    "warrior": {
        "features": ["strong jaw", "battle scars", "determined eyes"],
        "avoid": ["delicate", "frail", "peaceful"]
    },
    "mage": {
        "features": ["wise eyes", "mystical aura", "intricate robes"],
        "avoid": ["mundane", "simple", "ordinary"]
    }
}

# Select archetype
archetype = choice(list(archetypes.keys()))
data = archetypes[archetype]

# Build prompts
features = choice(data["features"], count=2)
positive_prompt = f"{archetype}, {join(features)}, masterpiece"
negative_prompt = join(data["avoid"]) + ", low quality"
```

### Using BREAK for Prompt Structure
```python
# Create structured prompts with breaks
elements = [
    "portrait of a woman",
    "BREAK",
    choice(["red hair", "blonde hair", "black hair"]),
    choice(["blue eyes", "green eyes", "brown eyes"]),
    "BREAK", 
    "photorealistic, high detail"
]

positive_prompt = join(elements)
# Result: "portrait of a woman\nBREAK\nred hair, blue eyes\nBREAK\nphotorealistic, high detail"
```

## Development

### Setting up Development Environment

To install the development dependencies and pre-commit hooks:

```bash
cd ComfyUI-PyPromptGenerator
pip install -e .[dev]
pre-commit install
```

The `-e` flag results in a "live" install where changes to the extension are automatically picked up when you restart ComfyUI.

### Running Tests

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests only

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Pre-commit**: Automated code quality checks
- **Pytest**: Comprehensive testing framework

### Project Structure

```
ComfyUI-PyPromptGenerator/
├── src/pyprompt_generator/    # Main package
│   ├── nodes.py              # ComfyUI node implementations
│   ├── utils.py              # Utility functions
│   └── __init__.py           # Package initialization
├── tests/                    # Test suite
│   ├── test_choice.py        # Choice function tests
│   ├── test_utils.py         # Utility function tests
│   ├── test_integration.py   # Integration tests
│   └── conftest.py          # Test configuration
├── wildcards/               # Example wildcard files
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## Contributing

Contributions are welcome! This project follows standard open-source contribution practices:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Ensure tests pass and code follows style guidelines
4. **Run tests**: `pytest` and `pre-commit run --all-files`
5. **Commit changes**: `git commit -m "Add amazing feature"`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Guidelines
- Add tests for new functionality
- Update documentation for user-facing changes
- Follow existing code style and conventions
- Ensure all CI checks pass

## API Reference

### Node Classes

#### `PyPromptGeneratorNode`
Main node for inline script execution.

**Inputs:**
- `script` (STRING): Python script to execute

**Outputs:**
- `positive_prompt` (STRING): Generated positive prompt
- `negative_prompt` (STRING): Generated negative prompt

#### `PyPromptFileGeneratorNode`
Node for file-based script execution.

**Inputs:**
- `script_file` (STRING): Path to Python script file
- `base_path` (STRING, optional): Base directory for relative paths

**Outputs:**
- `positive_prompt` (STRING): Generated positive prompt
- `negative_prompt` (STRING): Generated negative prompt

### Utility Functions Reference

For complete function documentation and examples, see the inline documentation in [`utils.py`](src/pyprompt_generator/utils.py).

## Troubleshooting

### Common Issues

**Import Errors**
```
ImportError: cannot import name 'PyPromptGeneratorNode'
```
- Ensure ComfyUI is restarted after installation
- Check that the extension is in the correct `custom_nodes/` directory

**Script Execution Errors**
```
NameError: name 'choice' is not defined
```
- All utility functions are automatically available in scripts
- No imports needed - functions are injected into the execution environment

**File Not Found (PyPromptFileGeneratorNode)**
```
FileNotFoundError: Script file not found
```
- Check file path is correct relative to ComfyUI directory
- Use absolute paths if having issues with relative paths
- Ensure file has `.py` extension

### Performance Tips

- Use file-based scripts for complex logic to avoid recompilation
- Enable caching for wildcard-heavy workflows
- Both nodes automatically refresh on every execution for dynamic content

## Publishing to Registry

If you wish to share this custom node with others in the community, you can publish it to the registry. We've already auto-populated some fields in `pyproject.toml` under `tool.comfy`, but please double-check that they are correct.

You need to make an account on https://registry.comfy.org and create an API key token.

- [ ] Go to the [registry](https://registry.comfy.org). Login and create a publisher id (everything after the `@` sign on your registry profile). 
- [ ] Add the publisher id into the pyproject.toml file.
- [ ] Create an api key on the Registry for publishing from Github. [Instructions](https://docs.comfy.org/registry/publishing#create-an-api-key-for-publishing).
- [ ] Add it to your Github Repository Secrets as `REGISTRY_ACCESS_TOKEN`.

A Github action will run on every git push. You can also run the Github action manually. Full instructions [here](https://docs.comfy.org/registry/publishing). Join our [discord](https://discord.com/invite/comfyorg) if you have any questions!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

