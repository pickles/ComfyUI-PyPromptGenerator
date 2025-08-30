# ComfyUI PyPromptGenerator - Comprehensive Feature Demo
# This sample demonstrates all available features of the PyPromptGenerator

# Note: random module is automatically available, no import needed

print("=== PyPromptGenerator Feature Demo ===")

# === 1. BASIC UTILITY FUNCTIONS ===
print("1. Testing utility functions...")

# Basic choice function
base_quality = choice(["masterpiece", "high quality", "detailed", "professional"])
print(f"Selected quality: {base_quality}")

# Weighted choice (higher weights = more likely)
art_style = choice([
    "5::photorealistic",    # 5x more likely
    "3::anime style",       # 3x more likely  
    "2::oil painting",      # 2x more likely
    "1::watercolor"         # 1x (baseline)
])
print(f"Selected style: {art_style}")

# Multiple selections (no duplicates)
multiple_effects = choice(["bloom", "depth of field", "soft lighting", "lens flare", "film grain"], count=3)
print(f"Selected effects: {multiple_effects}")

# Random boolean with custom probability
use_dramatic_lighting = random_boolean(0.7)  # 70% chance
print(f"Use dramatic lighting: {use_dramatic_lighting}")

# Random range
image_resolution = random_range(1024, 4096, 512)  # 1024, 1536, 2048, 2560, 3072, 3584, 4096
print(f"Resolution: {image_resolution}x{image_resolution}")

# === 2. WILDCARD FUNCTIONALITY ===
print("\n2. Testing wildcard functionality...")

# Check available wildcards
print(f"Available wildcards: {[k for k in globals().keys() if k.startswith('_')]}")

# Use wildcards with fallbacks
selected_style = choice(_styles) if '_styles' in globals() else "realistic"
selected_color = choice(_colors) if '_colors' in globals() else "vibrant"
selected_subject = choice(_subjects) if '_subjects' in globals() else "portrait"

print(f"Wildcard selections - Style: {selected_style}, Color: {selected_color}, Subject: {selected_subject}")

# Use nested wildcards (if available)
if '_compositions' in globals():
    composition = choice(_compositions)
    print(f"Composition (nested wildcards): {composition}")
else:
    composition = f"{selected_style} {selected_subject}"
    print(f"Fallback composition: {composition}")

# === 3. ADVANCED LIST MANIPULATION ===
print("\n3. Testing advanced list functions...")

# Shuffle list
camera_angles = shuffle_list(["low angle", "high angle", "eye level", "bird's eye", "worm's eye"])
selected_angle = camera_angles[0]  # Take first from shuffled list
print(f"Camera angle: {selected_angle}")

# Maybe function (conditional inclusion)
mood_modifier = maybe("moody atmosphere", 0.6)  # 60% chance to include
depth_effect = maybe("shallow depth of field", 0.4)  # 40% chance
print(f"Mood modifier: '{mood_modifier}' (empty if not selected)")
print(f"Depth effect: '{depth_effect}' (empty if not selected)")

# Flatten nested lists
complex_elements = [
    base_quality,
    [art_style, selected_angle],
    multiple_effects,
    ["highly detailed", maybe("award winning", 0.3)],
    ""  # Empty string will be filtered out
]
flattened = flatten(complex_elements)
print(f"Flattened elements: {flattened}")

# === 4. CONDITIONAL LOGIC ===
print("\n4. Testing conditional logic...")

# Character type selection with different prompt strategies
character_types = {
    "warrior": {
        "features": ["muscular build", "battle scars", "determined expression", "armor details"],
        "avoid": ["delicate", "fragile", "peaceful", "soft"]
    },
    "mage": {
        "features": ["mystical aura", "wise eyes", "flowing robes", "magical artifacts"],
        "avoid": ["mundane", "ordinary", "simple", "realistic clothing"]
    },
    "rogue": {
        "features": ["agile build", "sharp eyes", "dark clothing", "stealth gear"],
        "avoid": ["bright colors", "heavy armor", "obvious", "clumsy"]
    }
}

character_type = choice(list(character_types.keys()))
character_data = character_types[character_type]
print(f"Selected character type: {character_type}")

# Build character-specific features
character_features = choice(character_data["features"], count=2)
print(f"Character features: {character_features}")

# === 5. ENVIRONMENT AND SETTING ===
print("\n5. Building environment...")

# Time of day affects lighting
time_of_day = choice(["dawn", "morning", "noon", "afternoon", "sunset", "dusk", "night"])
if time_of_day in ["dawn", "sunset"]:
    lighting = "golden hour lighting"
elif time_of_day == "night":
    lighting = choice(["moonlight", "artificial lighting", "candlelight"])
elif time_of_day == "noon":
    lighting = "bright natural lighting"
else:
    lighting = "soft natural lighting"

print(f"Time: {time_of_day}, Lighting: {lighting}")

# Weather effects (conditional)
weather_chance = random_boolean(0.4)
weather = ""
if weather_chance:
    weather = choice(["light rain", "fog", "overcast", "snow", "clear sky"])
    print(f"Weather: {weather}")

# === 6. PROMPT CONSTRUCTION WITH BREAK ===
print("\n6. Constructing final prompt...")

# Build positive prompt sections
subject_section = [composition, join(character_features)]
style_section = [art_style, base_quality]
lighting_section = [lighting, maybe(mood_modifier, 1.0)]  # Include if not empty
effects_section = flatten([multiple_effects, maybe(depth_effect, 1.0), maybe(weather, 1.0)])
technical_section = [f"{image_resolution}x{image_resolution}", "professional photography"]

# Use BREAK to separate sections for better prompt structure
prompt_sections = [
    join(subject_section),
    "BREAK",
    join(style_section), 
    "BREAK",
    join(lighting_section),
    "BREAK", 
    join(effects_section),
    "BREAK",
    join(technical_section)
]

# Remove empty sections
cleaned_sections = [section for section in prompt_sections if section and section != "BREAK, BREAK"]

positive_prompt = join(cleaned_sections)

# === 7. NEGATIVE PROMPT CONSTRUCTION ===
print("\n7. Building negative prompt...")

# Base negative terms
base_negative = ["worst quality", "low quality", "blurry", "out of focus"]

# Character-specific negative terms
character_avoid = character_data["avoid"]

# Conditional negative terms based on style
style_negative = []
if "photorealistic" in art_style:
    style_negative.extend(["anime", "cartoon", "illustration", "painted"])
elif "anime" in art_style:
    style_negative.extend(["photorealistic", "realistic", "photograph"])

# Technical negative terms
technical_negative = ["low resolution", "pixelated", "compression artifacts"]

# Weather-related negatives (if no weather was selected)
if not weather:
    weather_negative = maybe("bad weather", 0.3)
    if weather_negative:
        technical_negative.append(weather_negative)

# Combine all negative elements
all_negative = flatten([
    base_negative,
    character_avoid[:2],  # Take first 2 character-specific negatives
    style_negative,
    technical_negative
])

negative_prompt = join(all_negative)

# === 8. FINAL OUTPUT ===
print("\n=== FINAL RESULTS ===")
print(f"Positive prompt length: {len(positive_prompt)} characters")
print(f"Negative prompt length: {len(negative_prompt)} characters")
print(f"Character type: {character_type}")
print(f"Style: {art_style}")
print(f"Lighting: {lighting}")
if weather:
    print(f"Weather: {weather}")

# Final prompts (these will be used by ComfyUI)
positive_prompt = positive_prompt
negative_prompt = negative_prompt
