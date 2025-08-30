# Simple PyPromptGenerator Example
# This is a basic example showing essential features

# === BASIC PROMPT GENERATION ===

# Use choice function for random selection
quality = choice(["masterpiece", "high quality", "detailed artwork"])
art_style = choice(["anime style", "photorealistic", "oil painting", "digital art"])

# Use wildcards (if available)
if '_subjects' in globals():
    subject = choice(_subjects)
else:
    subject = "beautiful portrait"

if '_colors' in globals():
    color_theme = choice(_colors)
else:
    color_theme = "vibrant"

# Random effects with probability
use_lighting = random_boolean(0.8)  # 80% chance
if use_lighting:
    lighting = choice(["soft lighting", "dramatic lighting", "golden hour"])
else:
    lighting = ""

# Build positive prompt
positive_elements = [
    quality,
    art_style,
    subject,
    color_theme,
    maybe(lighting, 1.0),  # Include if not empty
    "highly detailed"
]

# Remove empty strings and join
positive_prompt = join(flatten(positive_elements))

# Simple negative prompt
negative_prompt = "worst quality, low quality, blurry, out of focus"

# Optional: Add style-specific negatives
if "anime" in art_style:
    negative_prompt += ", photorealistic, realistic"
elif "photorealistic" in art_style:
    negative_prompt += ", anime, cartoon, illustration"
