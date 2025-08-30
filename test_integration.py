"""Integration test for nested wildcard functionality"""
from src.pyprompt_generator.utils import load_wildcards, choice
import os

def test_nested_wildcards():
    # Load wildcards from the wildcards directory
    wildcards_dir = os.path.join(os.getcwd(), 'wildcards')
    wildcards = load_wildcards(wildcards_dir)
    
    print("=== Loaded Wildcards ===")
    for key in sorted(wildcards.keys()):
        print(f"{key}: {len(wildcards[key])} items")
    
    print("\n=== Testing Nested Wildcard Expansion ===")
    if '_compositions' in wildcards:
        print("Compositions (with nested expansions):")
        for i, comp in enumerate(wildcards['_compositions'][:5]):
            print(f"{i+1}. {comp}")
        
        print("\n=== Random Selections ===")
        for i in range(3):
            print(f"Random {i+1}: {choice(wildcards['_compositions'])}")
    else:
        print("No compositions found")
    
    # Show individual wildcard files
    print("\n=== Individual Wildcard Files ===")
    for wildcard_name in ['_styles', '_colors', '_subjects']:
        if wildcard_name in wildcards:
            print(f"{wildcard_name}: {wildcards[wildcard_name][:3]}")

if __name__ == "__main__":
    test_nested_wildcards()
