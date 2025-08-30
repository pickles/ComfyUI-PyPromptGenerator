#!/usr/bin/env python3
"""
Wrapper script to run sample scripts with proper utility functions defined.
This allows running sample scripts locally without import statements.

Usage:
    python run_sample.py sample1
    python run_sample.py simple_example
    python run_sample.py sample2
"""

import sys
import os
import random
import argparse
from pathlib import Path

# Add the src directory to Python path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Import all utility functions from pyprompt_generator
from pyprompt_generator.utils import (
    choice, maybe, flatten, join, weighted_choice,
    get_wildcard_vars_with_auto_refresh, random_boolean, shuffle_list, random_range
)

# Define missing utility functions
def multiple(items, count=None):
    """Select multiple items from an array"""
    if count is None:
        count = random_range(2, min(5, len(items))) if len(items) > 1 else 1
    return choice(items, count)

def weighted(items_with_weights):
    """Weighted choice using items with weights in format ['weight::item', ...]"""
    return choice(items_with_weights)

# Make utilities available globally for sample1.py
globals().update({
    'choice': choice,
    'multiple': multiple,
    'maybe': maybe,
    'weighted': weighted,
    'flatten': flatten,
    'join': join,
    'get_wildcard_vars_with_auto_refresh': get_wildcard_vars_with_auto_refresh,
    'weighted_choice': weighted_choice,
    'random_boolean': random_boolean,
    'shuffle_list': shuffle_list,
    'random_range': random_range
})

def main():
    """Execute specified sample script with utilities available."""
    parser = argparse.ArgumentParser(
        description="Run sample scripts with PyPromptGenerator utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_sample.py sample1
    python run_sample.py simple_example
    python run_sample.py --list
        """
    )
    parser.add_argument('sample_name', nargs='?', 
                       help='Name of the sample script to run (without .py extension)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available sample scripts')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    sample_scripts_dir = script_dir / "sample_scripts"
    
    # List available samples if requested
    if args.list:
        print("Available sample scripts:")
        if sample_scripts_dir.exists():
            for script_file in sample_scripts_dir.glob("*.py"):
                sample_name = script_file.stem
                print(f"  - {sample_name}")
        else:
            print("  No sample_scripts directory found")
        return 0
    
    # Check if sample name is provided
    if not args.sample_name:
        print("Error: Please specify a sample script name")
        print("Use --list to see available samples")
        parser.print_help()
        return 1
    
    sample_name = args.sample_name
    sample_file = sample_scripts_dir / f"{sample_name}.py"
    
    # Check if sample file exists
    if not sample_file.exists():
        print(f"Error: Sample script not found: {sample_file}")
        print("Use --list to see available samples")
        return 1
    
    print(f"=== Running {sample_name} with PyPromptGenerator Utilities ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"Sample script: {sample_file}")
    print()
    
    # Change to script directory to ensure relative paths work
    original_cwd = os.getcwd()
    os.chdir(script_dir)
    
    try:
        # Read and execute the sample script
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample_code = f.read()
            
        # Execute the code with our globals (including utility functions)
        exec(sample_code, globals())
        
        return 0
        
    except Exception as e:
        print(f"Error executing {sample_name}: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    sys.exit(main())
