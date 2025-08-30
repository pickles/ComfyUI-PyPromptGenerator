# ComfyUI PyPromptGenerator Node

A powerful custom node for ComfyUI that enables dynamic prompt generation using Python scripts. This extension allows you to create sophisticated positive and negative prompts through scripting, offering more flexibility and control than traditional static prompts.

Perfect for scenarios where you need:
- **Conditional prompt generation** - Add complementary negative terms based on positive content
- **Weighted random selection** - Choose prompt elements with specific probabilities
- **Complex prompt logic** - Use Python's full power instead of learning template languages
- **File-based prompts** - Load and execute prompt scripts from external files
- **Dynamic wildcard support** - Advanced wildcard expansion with caching

## Installation

⚠️ **Important Notice**: This custom node uses Python's `exec()` function to execute dynamic scripts, which may not comply with some ComfyUI custom node guidelines regarding code execution safety. For reference, see the [ComfyUI Registry Standards](https://docs.comfy.org/registry/standards#eval%2Fexec-calls). Please review your security requirements before installation and use at your own discretion.

### Manual Installation
1. Navigate to your ComfyUI installation directory
2. Go to `custom_nodes/` folder
3. Clone this repository:
   ```bash
   git clone https://github.com/pickles/ComfyUI-PyPromptGenerator.git
   ```
4. Restart ComfyUI

## Quick Start with Mount Fuji Demo

This project includes a comprehensive demonstration script that showcases all PyPromptGenerator features by generating beautiful Mount Fuji artwork prompts.

### Running the Demo

The project includes a convenient wrapper script for running sample scripts:

```bash
# Navigate to the project directory
cd ComfyUI-PyPromptGenerator

# List available sample scripts
python run_sample.py --list

# Run the Mount Fuji generator demo
python run_sample.py mount_fuji_generator

# Show help
python run_sample.py --help
```

### Mount Fuji Generator Features

The `mount_fuji_generator.py` demonstrates:

- **🎨 Art Style Selection**: Traditional Japanese painting, ukiyo-e, sumi-e, watercolor, photorealistic
- **🌸 Seasonal Variations**: Spring cherry blossoms, autumn maple leaves, winter snow, summer greenery
- **🏔️ Dynamic Compositions**: Lake Kawaguchi views, Chureito Pagoda, rice fields, traditional gardens
- **🎨 Color Palettes**: Soft pastels, dramatic sunsets, monochromatic tones, earth colors
- **✨ Atmospheric Effects**: Lens flares, bokeh, volumetric lighting, atmospheric haze
- **⛩️ Traditional Elements**: Torii gates, Japanese calligraphy, gold leaf accents
- **🔄 Nested Wildcards**: Complex compositions using wildcard references
- **🎲 Weighted Selection**: Balanced probabilities for different styles and seasons
- **📊 Smart Structure**: BREAK notation for organized prompt sections

### Sample Output

```
=== Mount Fuji Artwork Generation Demo ===

【Style】: ukiyo-e woodblock print
【Season】: spring with cherry blossoms  
【Composition】: reflection in lake waters
【Colors】: soft pastel colors
【Mood】: serene and peaceful
【Resolution】: 1280x720

【Positive Prompt】 (385 characters):
Mount Fuji, reflection in lake waters
BREAK
ukiyo-e woodblock print, masterpiece, fine art
BREAK
spring with cherry blossoms, sunrise golden light, soft pastel colors
BREAK
blooming sakura trees, traditional torii gate
BREAK
gentle bokeh effect, atmospheric haze
BREAK
serene and peaceful, intricate brush strokes, delicate cloud formations
BREAK
1280x720, fine art

【Statistics】:
- Number of wildcards used: 6
- Foreground elements: 2
- Artistic details: 3
- Traditional elements: None
- Atmospheric effects: 2
```

### Creating Your Own Scripts

The `run_sample.py` wrapper allows you to create and run your own prompt generation scripts:

1. Create a new Python file in the `sample_scripts/` directory
2. Use all PyPromptGenerator utility functions without imports
3. Run your script: `python run_sample.py your_script_name`

## Features

### 🎯 **PyPromptGenerator Node**
- **Inline Python Scripts**: Write prompt generation logic directly in the node
- **Rich Utility Functions**: Built-in functions for weighted selection, list manipulation, and randomization
- **Always Refresh**: Option to regenerate prompts on every execution
- **Script Execution**: Uses Python's `exec()` for dynamic script execution (see security notice above)

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

## Creating Wildcard Files

Wildcard files allow you to define reusable lists of terms that can be randomly selected in your prompts. The system automatically loads `.txt` files from the `wildcards/` directory.

### File Structure
Create text files in the `wildcards/` directory:
```
wildcards/
├── fuji_colors.txt                  # Mount Fuji color palettes
├── fuji_compositions.txt            # Composition and viewpoints
├── fuji_compositions_complex.txt    # Nested wildcard compositions
├── fuji_details.txt                 # Artistic details and effects
├── fuji_foreground.txt              # Foreground elements
├── fuji_seasons.txt                 # Seasons and weather conditions
├── mount_fuji_styles.txt            # Art styles for Mount Fuji
└── your_custom_wildcards.txt        # Add your own wildcard files
```

The project includes Mount Fuji-themed wildcard files as examples, but you can create your own wildcard files for any subject matter.

### File Format
Each wildcard file should contain one item per line:

**Example: `wildcards/mount_fuji_styles.txt`**
```
traditional Japanese painting
ukiyo-e woodblock print
sumi-e ink painting
watercolor landscape
oil painting masterpiece
digital art concept
photorealistic landscape
anime landscape style
studio ghibli style
minimalist landscape
impressionist painting
vintage postcard style
```

**Example: `wildcards/fuji_colors.txt`**
```
soft pastel colors
vibrant autumn hues
monochromatic blue tones
warm golden lighting
cool morning blues
dramatic sunset oranges
ethereal misty whites
deep forest greens
pristine snow whites
rich earth tones
```

**Example: `wildcards/fuji_seasons.txt`**
```
spring with cherry blossoms
summer with lush greenery
autumn with red maple leaves
winter with snow-capped peak
early morning mist
sunset golden hour
clear blue sky day
dramatic storm clouds
moonlit night scene
dawn breaking over mountains
```

### Advanced Wildcard Features

#### Weighted Entries
Add weights to entries using the `weight::item` format:
```
# effects.txt
10::highly detailed
5::masterpiece
3::professional
2::cinematic lighting
1::award winning
```

#### Comments and Empty Lines
- Lines starting with `#` are treated as comments and ignored
- Empty lines are automatically filtered out
- Use comments to organize your wildcard files

**Example: `wildcards/moods.txt`**
```
# Positive moods
cheerful
serene
confident
playful

# Neutral moods
calm
focused
contemplative

# Intense moods
dramatic
mysterious
epic
```

#### Nested Wildcards (Advanced)
You can reference other wildcard files within wildcard files using `{wildcard_name}` syntax:

**Example: `wildcards/fuji_compositions_complex.txt`**
```
{mount_fuji_styles} of Mount Fuji in {fuji_seasons}
{fuji_compositions} with {fuji_foreground} in foreground
{fuji_colors} Mount Fuji landscape with {fuji_details}
traditional Japanese {mount_fuji_styles} featuring {fuji_foreground}
{fuji_seasons} Mount Fuji scene with {fuji_compositions}
```

**How Nested Wildcards Work:**
- Use `{wildcard_name}` to reference another wildcard file (without the underscore prefix)
- Multiple references per line are supported
- Each reference is replaced with a random selection from the referenced wildcard
- Self-references are detected and prevented
- Invalid references are left as-is with a warning

**Example expansion:**
- `{mount_fuji_styles} of Mount Fuji in {fuji_seasons}` might become `"ukiyo-e woodblock print of Mount Fuji in spring with cherry blossoms"`
- `{fuji_colors} Mount Fuji landscape with {fuji_details}` might become `"dramatic sunset oranges Mount Fuji landscape with intricate brush strokes"`

### Using Wildcards in Scripts

Wildcard files are automatically loaded as variables prefixed with `_`:

```python
# Wildcard variables are automatically available
# _mount_fuji_styles, _fuji_colors, _fuji_seasons, etc.

# Basic usage
selected_style = choice(_mount_fuji_styles)
selected_color = choice(_fuji_colors)
selected_season = choice(_fuji_seasons)

positive_prompt = f"{selected_style}, {selected_color}, {selected_season}"

# Advanced usage with multiple selections
style_combo = choice(_mount_fuji_styles, count=2)  # Get 2 different styles
details = choice(_fuji_details, count=3)  # Get 3 different details

positive_prompt = f"{join(style_combo)}, Mount Fuji, {join(details)}"

# Conditional usage with seasonal elements
if "spring" in selected_season:
    foreground = choice(_fuji_foreground)
    positive_prompt += f", {foreground}"

# Check if wildcard exists before using
if '_fuji_compositions_complex' in globals():
    complex_comp = choice(_fuji_compositions_complex)
    positive_prompt = complex_comp
else:
    composition = "majestic view from Lake Kawaguchi"  # fallback
```

### Wildcard Management Functions

```python
# Reload wildcard files (useful during development)
refresh_wildcards()

# Get all available wildcard variables
wildcard_vars = get_wildcard_vars()
print(f"Available wildcards: {list(wildcard_vars.keys())}")

# Load wildcards from custom directory
custom_wildcards = load_wildcards("/path/to/custom/wildcards")
```

### Best Practices

1. **Organize by Category**: Create separate files for different types of content
2. **Use Descriptive Names**: File names become variable names (`styles.txt` → `_styles`)
3. **Include Weights**: Use weights for more control over selection probability
4. **Document with Comments**: Use `#` comments to organize and explain entries
5. **Test Combinations**: Ensure wildcard combinations make sense together
6. **Version Control**: Keep wildcard files in version control for team projects

### Troubleshooting Wildcards

**Wildcard not found:**
```python
# Always check if wildcard exists
if '_mount_fuji_styles' in globals():
    style = choice(_mount_fuji_styles)
else:
    print("Wildcard _mount_fuji_styles not found")
    style = "traditional Japanese painting"
```

**Reload after changes:**
```python
# Force reload if you've modified wildcard files
refresh_wildcards()
selected_item = choice(_fuji_colors)  # Now uses updated file
```

### 🔧 **Developer Features**
- **Comprehensive Tests**: Full test suite with 94 test cases covering all functionality
- **Type Safety**: MyPy compatible with proper type hints
- **Code Quality**: Ruff linting and pre-commit hooks
- **Documentation**: Extensive inline documentation and examples
- **Sample Scripts**: Complete Mount Fuji art generator demonstrating all features
- **Script Wrapper**: Easy-to-use `run_sample.py` for testing and development

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

### Using Nested Wildcards
```python
# Create wildcard files with nested references
# mount_fuji_styles.txt: traditional Japanese painting, ukiyo-e woodblock print, sumi-e ink painting
# fuji_colors.txt: soft pastel colors, dramatic sunset oranges, monochromatic blue tones
# fuji_compositions_complex.txt: {mount_fuji_styles} of Mount Fuji in {fuji_seasons}

# Use nested wildcards in script
if '_fuji_compositions_complex' in globals():
    complex_composition = choice(_fuji_compositions_complex)
    # Might result in: "ukiyo-e woodblock print of Mount Fuji in spring with cherry blossoms"
    positive_prompt = f"{complex_composition}, masterpiece, highly detailed"
else:
    positive_prompt = "Mount Fuji landscape, masterpiece, highly detailed"

negative_prompt = "low quality, blurry, modern buildings"
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

The project includes comprehensive test coverage with 94 test cases:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests only

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests with verbose output
pytest -v
```

Test categories include:
- **Choice function tests** (17 tests) - Weighted selection, multiple selection, edge cases
- **Utility function tests** (20 tests) - All utility functions including `maybe`, `flatten`, `join`
- **Nested wildcard tests** (9 tests) - Advanced wildcard functionality
- **Integration tests** (13 tests) - ComfyUI node integration and complex scenarios
- **Wildcard tests** (10 tests) - Wildcard loading, caching, and management
- **File generator tests** (8 tests) - File-based script execution
- **Flatten function tests** (13 tests) - Array flattening with various scenarios
- **Other specialized tests** (4 tests) - Additional edge cases and functionality

### Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Pre-commit**: Automated code quality checks
- **Pytest**: Comprehensive testing framework

### Project Structure

```
ComfyUI-PyPromptGenerator/
├── src/pyprompt_generator/           # Main package
│   ├── nodes.py                     # ComfyUI node implementations
│   ├── utils.py                     # Utility functions with nested wildcards
│   └── __init__.py                  # Package initialization
├── sample_scripts/                   # Example scripts and demos
│   └── mount_fuji_generator.py      # Comprehensive Mount Fuji art generator demo
├── tests/                           # Comprehensive test suite (94 tests)
│   ├── test_choice.py               # Choice function tests
│   ├── test_file_generator.py       # File generator node tests
│   ├── test_flatten.py              # Flatten function tests
│   ├── test_integration.py          # Integration tests
│   ├── test_nested_wildcards.py     # Nested wildcard tests
│   ├── test_utils.py                # Utility function tests
│   ├── test_wildcard.py             # Wildcard function tests
│   ├── test_wildcard_manager.py     # WildcardManager tests
│   ├── conftest.py                  # Test configuration
│   └── pytest.ini                   # Pytest configuration
├── wildcards/                       # Mount Fuji themed wildcard files
│   ├── fuji_colors.txt              # Color palettes for Mount Fuji
│   ├── fuji_compositions.txt        # Composition and viewpoints
│   ├── fuji_compositions_complex.txt # Nested wildcard compositions
│   ├── fuji_details.txt             # Artistic details and effects
│   ├── fuji_foreground.txt          # Foreground elements
│   ├── fuji_seasons.txt             # Seasons and weather
│   ├── mount_fuji_styles.txt        # Art styles for Mount Fuji
│   └── create_wildcards_here        # Placeholder for custom wildcards
├── run_sample.py                    # Sample script execution wrapper
├── .github/                         # GitHub configuration
│   └── workflows/                   # CI/CD workflows
├── .vscode/                         # VS Code configuration
├── pyproject.toml                   # Project configuration
├── MANIFEST.in                      # Package manifest
├── LICENSE                          # MIT License
├── README.md                        # Documentation (English)
└── README-JA.md                     # Documentation (Japanese)
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

