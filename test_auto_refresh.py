import sys
import os
sys.path.insert(0, 'src')

from pyprompt_generator.utils import get_wildcard_vars_with_auto_refresh

print("Testing wildcard auto-refresh functionality...")

# First call
print("\n1. Initial load:")
wildcards = get_wildcard_vars_with_auto_refresh()
print(f"Loaded wildcards: {list(wildcards.keys())}")

# Test creating a new wildcard file
print("\n2. Creating a new wildcard file...")
with open('wildcards/test_new.txt', 'w') as f:
    f.write("item1\nitem2\nitem3\n")

# Second call should detect the new file
print("\n3. Checking for changes:")
wildcards = get_wildcard_vars_with_auto_refresh()
print(f"Loaded wildcards: {list(wildcards.keys())}")

# Clean up
print("\n4. Cleaning up...")
os.remove('wildcards/test_new.txt')

print("\n5. After cleanup:")
wildcards = get_wildcard_vars_with_auto_refresh()
print(f"Loaded wildcards: {list(wildcards.keys())}")
