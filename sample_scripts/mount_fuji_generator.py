"""
Mount Fuji Art Generator - PyPromptGenerator Demo
Comprehensive prompt generation demo for creating beautiful Mount Fuji artwork

This script uses all features of PyPromptGenerator to generate prompts
for Mount Fuji artwork in various styles and compositions.
"""

print("=== Mount Fuji Artwork Generation Demo ===")

# === 1. Wildcard Loading and Auto-refresh ===
print("\n1. Loading wildcard files...")
wildcards = get_wildcard_vars_with_auto_refresh()

# Add wildcard variables to local environment
for key, value in wildcards.items():
    globals()[key] = value

print(f"Loaded wildcards: {len(wildcards)} files")

# === 2. Basic Settings and Style Selection ===
print("\n2. Art style and basic settings...")

# Art style selection (weighted)
art_styles = [
    "3::traditional Japanese painting",
    "2::ukiyo-e woodblock print", 
    "2::sumi-e ink painting",
    "2::watercolor landscape",
    "1::photorealistic landscape",
    "1::digital art concept",
    "1::anime landscape style"
]

selected_style = choice(art_styles)
print(f"Selected style: {selected_style}")

# Basic quality settings
quality_terms = [
    "masterpiece",
    "best quality", 
    "highly detailed",
    "fine art",
    "museum quality"
]

base_quality = join(choice(quality_terms, 2))
print(f"Quality settings: {base_quality}")

# === 3. Season and Weather Selection ===
print("\n3. Season and weather settings...")

# Season selection (weighted towards spring)
season_choices = [
    "4::spring with cherry blossoms",
    "2::autumn with red maple leaves", 
    "2::winter with snow-capped peak",
    "1::summer with lush greenery"
]

selected_season = choice(season_choices)
print(f"Selected season: {selected_season}")

# Time of day and lighting
time_lighting = [
    "3::sunrise golden light",
    "3::sunset warm glow",
    "2::early morning mist",
    "2::twilight blue hour",
    "1::midday bright light",
    "1::moonlit night scene"
]

lighting_choice = choice(time_lighting)
print(f"Lighting conditions: {lighting_choice}")

# === 4. Composition and Viewpoint ===
print("\n4. Composition settings...")

# Main composition selection
if '_fuji_compositions' in globals():
    main_composition = choice(_fuji_compositions)
else:
    main_composition = "majestic view from Lake Kawaguchi"

print(f"Main composition: {main_composition}")

# Foreground elements
if '_fuji_foreground' in globals():
    foreground_elements = choice(_fuji_foreground, 2)
else:
    foreground_elements = ["blooming sakura trees", "peaceful lake with boats"]

print(f"Foreground elements: {join(foreground_elements)}")

# === 5. Colors and Mood ===
print("\n5. Color and mood settings...")

# Color palette
if '_fuji_colors' in globals():
    color_palette = choice(_fuji_colors)
else:
    color_palette = "soft pastel colors"

print(f"Color palette: {color_palette}")

# Mood settings
mood_descriptors = [
    "serene and peaceful",
    "majestic and awe-inspiring", 
    "tranquil and meditative",
    "dramatic and powerful",
    "ethereal and mystical"
]

selected_mood = choice(mood_descriptors)
print(f"Mood: {selected_mood}")

# === 6. Technical Details ===
print("\n6. Technical detail settings...")

# Resolution selection
resolutions = [
    "2::1024x768",    # 4:3 landscape
    "3::1280x720",    # 16:9 landscape  
    "2::1080x1080",   # square
    "1::768x1024"     # 3:4 portrait
]

resolution = choice(resolutions)
print(f"Resolution: {resolution}")

# Artistic details
if '_fuji_details' in globals():
    artistic_details = choice(_fuji_details, 3)
else:
    artistic_details = ["intricate brush strokes", "soft atmospheric perspective", "fine art quality"]

print(f"Artistic details: {join(artistic_details)}")

# === 7. Advanced Feature Demonstration ===
print("\n7. Using advanced features...")

# Complex composition (nested wildcards)
if '_fuji_compositions_complex' in globals():
    complex_composition = choice(_fuji_compositions_complex)
    print(f"Complex composition: {complex_composition}")
else:
    complex_composition = f"{selected_style} of Mount Fuji in {selected_season}"

# Conditional logic
include_traditional_elements = choice([True, False])
if include_traditional_elements:
    traditional_elements = [
        "traditional torii gate",
        "Japanese calligraphy", 
        "vintage paper texture",
        "gold leaf accents"
    ]
    selected_traditional = choice(traditional_elements, 2)
    print(f"Adding traditional elements: {join(selected_traditional)}")
else:
    selected_traditional = []
    print("Traditional elements: None")

# Multiple effects (probabilistic inclusion)
atmospheric_effects = [
    maybe("soft lens flare", 0.3),
    maybe("gentle bokeh effect", 0.4), 
    maybe("atmospheric haze", 0.6),
    maybe("volumetric lighting", 0.5),
    maybe("lens distortion", 0.2)
]

active_effects = flatten(atmospheric_effects)
print(f"Atmospheric effects: {join(active_effects) if active_effects else 'None'}")

# === 8. Final Prompt Construction ===
print("\n8. Building final prompt...")

# Positive prompt sections
subject_section = ["Mount Fuji", main_composition]
style_section = [selected_style, base_quality]
scene_section = [selected_season, lighting_choice, color_palette]
foreground_section = [join(foreground_elements)]
mood_section = [selected_mood, join(artistic_details)]
technical_section = [resolution, "professional photography" if "photorealistic" in selected_style else "fine art"]

# Conditional sections
if selected_traditional:
    traditional_section = [join(selected_traditional)]
else:
    traditional_section = []

if active_effects:
    effects_section = [join(active_effects)]
else:
    effects_section = []

# Structured with BREAK notation
positive_prompt_parts = [
    join(subject_section),
    "BREAK",
    join(style_section),
    "BREAK", 
    join(scene_section),
    "BREAK",
    join(foreground_section)
]

# Add conditional sections
if traditional_section:
    positive_prompt_parts.extend(["BREAK", join(traditional_section)])

if effects_section:
    positive_prompt_parts.extend(["BREAK", join(effects_section)])

positive_prompt_parts.extend(["BREAK", join(mood_section), "BREAK", join(technical_section)])

positive_prompt = join(positive_prompt_parts)

# === 9. Negative Prompt Construction ===
print("\n9. Building negative prompt...")

base_negative = [
    "low quality", "blurry", "pixelated", "distorted",
    "modern buildings", "cars", "people", "urban elements",
    "oversaturated", "garish colors", "artificial lighting"
]

style_specific_negative = []
if "traditional" in selected_style.lower():
    style_specific_negative.extend([
        "digital artifacts", "modern art style", "3D rendering"
    ])
elif "photorealistic" in selected_style.lower():
    style_specific_negative.extend([
        "cartoon", "anime", "painting artifacts", "brush strokes"
    ])

negative_prompt = join(flatten([base_negative, style_specific_negative]))

# === 10. Results Display ===
print("\n" + "="*60)
print("Mount Fuji Artwork Generation Prompt")
print("="*60)

print(f"\n【Style】: {selected_style}")
print(f"【Season】: {selected_season}") 
print(f"【Composition】: {main_composition}")
print(f"【Colors】: {color_palette}")
print(f"【Mood】: {selected_mood}")
print(f"【Resolution】: {resolution}")

print(f"\n【Positive Prompt】 ({len(positive_prompt)} characters):")
print("-" * 40)
print(positive_prompt)

print(f"\n【Negative Prompt】 ({len(negative_prompt)} characters):")
print("-" * 40) 
print(negative_prompt)

print(f"\n【Statistics】:")
print(f"- Number of wildcards used: {len([k for k in wildcards.keys() if k.startswith('_fuji')])}")
print(f"- Foreground elements: {len(foreground_elements)}")
print(f"- Artistic details: {len(artistic_details)}")
print(f"- Traditional elements: {'Yes' if selected_traditional else 'None'}")
print(f"- Atmospheric effects: {len(active_effects)}")

print("\n" + "="*60)
print("Prompt generation complete!")
print("="*60)
