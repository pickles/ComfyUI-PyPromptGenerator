# Advanced PyPrompt script with wildcards
# This script demonstrates wildcard usage and complex prompt generation

# Check if wildcard variables are available
if '_styles' in globals():
    art_style = choice(_styles)
    print(f"Using wildcard style: {art_style}")
else:
    art_style = "realistic"
    print("No style wildcards found, using default")

if '_colors' in globals():
    color_scheme = choice(_colors)
    print(f"Using wildcard color: {color_scheme}")
else:
    color_scheme = "vibrant"
    print("No color wildcards found, using default")

# Define custom lists
camera_angles = ["close-up", "wide shot", "medium shot", "bird's eye view"]
moods = ["peaceful", "dramatic", "mysterious", "energetic"]

# Use weighted choices
quality_weights = [
    "5::masterpiece",
    "4::high quality", 
    "3::detailed",
    "2::professional",
    "1::artistic"
]

# Generate random elements (random module is already available)
angle = choice(camera_angles)
mood = choice(moods)
qualities = choice(quality_weights, 3)  # Pick 3 weighted qualities

# Use random functions
detail_level = random_range(5, 10)
use_effects = random_boolean(0.8)  # 80% chance for effects

# Build prompt components
base_prompt = f"{art_style} {color_scheme} artwork"
composition = f"{angle} of a {mood} scene"

# Conditional elements
effects = []
if use_effects:
    effects = maybe(["dramatic lighting", "depth of field", "bokeh"], 0.6)
    if effects:
        effects = flatten(effects)  # Ensure it's a flat list

# Compose final prompt
prompt_parts = [base_prompt, composition]
prompt_parts.extend(qualities)

if effects:
    prompt_parts.extend(effects)

prompt_parts.append(f"detail level {detail_level}/10")

positive_prompt = join(prompt_parts)
negative_prompt = "low quality, blurry, amateur, worst quality, deformed, bad anatomy"

# Debug information
print(f"Art style: {art_style}")
print(f"Color: {color_scheme}")
print(f"Angle: {angle}, Mood: {mood}")
print(f"Effects: {effects if effects else 'None'}")
print(f"Detail level: {detail_level}")
