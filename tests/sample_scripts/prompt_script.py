# Sample PyPrompt script file
# This file demonstrates how to create prompts using external script files

# Example using utility functions (random module is already available)
styles = ["realistic", "anime", "oil painting", "watercolor"]
subjects = ["beautiful woman", "landscape", "portrait", "still life"]
qualities = ["high quality", "masterpiece", "detailed", "professional"]

# Use choice function to select random elements
selected_style = choice(styles)
selected_subject = choice(subjects)
selected_qualities = choice(qualities, 2)  # Pick 2 qualities

# Use maybe function for conditional elements
extra_detail = maybe("highly detailed", 0.7)  # 70% chance
lighting = maybe("dramatic lighting", 0.5)   # 50% chance

# Compose the prompt
positive_parts = [f"A {selected_style} {selected_subject}"]
positive_parts.extend(selected_qualities)

# Add optional elements if they exist
if extra_detail:
    positive_parts.append(extra_detail)
if lighting:
    positive_parts.append(lighting)

# Join all parts
positive_prompt = join(positive_parts)
negative_prompt = "low quality, blurry, worst quality, deformed"

# Debug output
print(f"Style: {selected_style}")
print(f"Subject: {selected_subject}")
print(f"Qualities: {join(selected_qualities, ' + ')}")
print(f"Extra detail: {extra_detail if extra_detail else 'None'}")
print(f"Lighting: {lighting if lighting else 'None'}")
