"""
Utility functions for ComfyUI Prompt Generator

This module contains utility functions that can be used in prompt generation scripts.
"""

import random
import os
import glob


def choice(items, count=1):
    """
    Extract random items from an array (supports weighted selection)
    
    Args:
        items: Source array for extraction
               For weighted items, use "weight::item" format
               Example: ["1::item1", "2::item2", "item3"] → 1:2:1 ratio
        count: Number of items to extract (default: 1)
            
    Returns:
        For count=1: Single item
        For count>1: List of items (no duplicates)
        
    Examples:
        >>> choice(["apple", "banana", "cherry"])
        'apple'  # Randomly selected
        
        >>> choice(["2::apple", "1::banana", "cherry"], 2)
        ['apple', 'cherry']  # Weighted random selection of 2 items (no duplicates)
        
        >>> choice(["3::common", "1::rare"])
        'common'  # common is selected with 3x probability
    """
    if not items:
        return None if count == 1 else []
    
    # Parse weighted items
    weights = []
    clean_items = []
    
    for item in items:
        if isinstance(item, str) and '::' in item:
            # Weighted item case
            parts = item.split('::', 1)
            try:
                weight = float(parts[0])
                clean_item = parts[1]
            except (ValueError, IndexError):
                # Treat as weight 1 if parsing fails
                weight = 1.0
                clean_item = item
        else:
            # Normal item case, weight is 1
            weight = 1.0
            clean_item = item
        
        weights.append(weight)
        clean_items.append(clean_item)
    
    if count == 1:
        # Single selection with weighted random choice
        selected_item = random.choices(clean_items, weights=weights, k=1)[0]
        return selected_item
    else:
        # Multiple selection case
        available_count = min(count, len(clean_items))
        
        # Weight-based selection (no duplicates)
        selected_indices = set()
        selected_items = []
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            # If all weights are 0, select equally
            return random.sample(clean_items, available_count) if count > 1 else random.choice(clean_items)
        
        normalized_weights = [w / total_weight for w in weights]
        
        for _ in range(available_count):
            # Select from items not yet selected
            available_indices = [i for i in range(len(clean_items)) if i not in selected_indices]
            if not available_indices:
                break
            
            available_weights = [normalized_weights[i] for i in available_indices]
            available_items = [clean_items[i] for i in available_indices]
            
            # Weighted random selection
            selected_index = random.choices(range(len(available_items)), weights=available_weights, k=1)[0]
            actual_index = available_indices[selected_index]
            
            selected_indices.add(actual_index)
            selected_items.append(clean_items[actual_index])
        
        return selected_items


def weighted_choice(items, weights=None):
    """
    Weighted random selection (single item)
    
    Args:
        items: List of choices
        weights: List of weights (equal weights if omitted)
        
    Returns:
        Selected item
        
    Examples:
        >>> weighted_choice(["apple", "banana"], [3, 1])
        'apple'  # apple is selected with 3x probability
    """
    if not items:
        return None
    
    if weights is None:
        weights = [1] * len(items)
    
    return random.choices(items, weights=weights, k=1)[0]


def shuffle_list(items):
    """
    Shuffle a list and return it (original list is not modified)
    
    Args:
        items: List to shuffle
        
    Returns:
        New shuffled list
        
    Examples:
        >>> shuffle_list([1, 2, 3, 4, 5])
        [3, 1, 5, 2, 4]  # Random order
    """
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def random_range(min_val, max_val, step=1):
    """
    Select a random value from the specified range
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        step: Step value (default: 1)
        
    Returns:
        Selected value
        
    Examples:
        >>> random_range(1, 10)
        7  # Random integer between 1 and 10
        
        >>> random_range(0, 1, 0.1)
        0.3  # Value in 0.1 increments between 0 and 1
    """
    if isinstance(step, int):
        return random.randrange(min_val, max_val + 1, step)
    else:
        # For float step
        steps = int((max_val - min_val) / step) + 1
        return min_val + random.randint(0, steps - 1) * step


def random_boolean(probability=0.5):
    """
    Return True with the specified probability
    
    Args:
        probability: Probability of returning True (0.0-1.0)
        
    Returns:
        Boolean value
        
    Examples:
        >>> random_boolean(0.8)
        True  # True with 80% probability
        
        >>> random_boolean(0.2)
        False  # True with 20% probability, False with 80% probability
    """
    return random.random() < probability


def join(items, separator=", "):
    """
    Join array elements with specified separator into a string
    If "BREAK" string is included, insert newline characters before and after it
    
    Args:
        items: List of elements to join
        separator: Separator character (default: ", ")
        
    Returns:
        Joined string
        
    Examples:
        >>> join(["apple", "banana", "cherry"])
        'apple, banana, cherry'
        
        >>> join(["red", "blue", "green"], " | ")
        'red | blue | green'
        
        >>> join([1, 2, 3], "-")
        '1-2-3'
        
        >>> join(["a", "b", "BREAK", "c"])
        'a, b\nBREAK\nc'
        
        >>> join(["start", "BREAK", "middle", "BREAK", "end"])
        'start\nBREAK\nmiddle\nBREAK\nend'
    """
    if not items:
        return ""
    
    # すべての要素を文字列に変換
    str_items = [str(item) for item in items]
    
    # If BREAK is not included, use normal join
    if "BREAK" not in str_items:
        return separator.join(str_items)
    
    # Special handling for BREAK: build step by step
    result_parts = []
    
    for i, item in enumerate(str_items):
        if item == "BREAK":
            # Add newline before BREAK (if not the first element)
            if i > 0:
                result_parts.append("\n")
            result_parts.append("BREAK")
            # Add newline after BREAK (if not the last element)
            if i < len(str_items) - 1:
                result_parts.append("\n")
        else:
            # Normal element
            # Check if separator is needed
            if i > 0:
                # If previous element was BREAK, newline already added, no separator needed
                if str_items[i-1] != "BREAK":
                    result_parts.append(separator)
            result_parts.append(item)
    
    return "".join(result_parts)


def load_wildcards(wildcard_dir=None):
    """
    Load text files from wildcard folder and make them available as variables
    
    Args:
        wildcard_dir: Path to wildcard folder (auto-detected if omitted)
        
    Returns:
        dict: Dictionary with filename as key (no extension, with underscore prefix)
        
    Examples:
        wildcards = load_wildcards()
        print(wildcards['_styles'])  # Contents of styles.txt stored as array
        print(wildcards['_colors'])  # Contents of colors.txt stored as array
        
    Notes:
        - Empty lines are ignored
        - Lines starting with # (comment lines) are ignored
        - Filenames are prefixed with underscore (_)
        - Extensions (.txt) are removed
        - Nested wildcards supported: {wildcard_name} will be replaced with random selection
    """
    if wildcard_dir is None:
        # Find wildcard folder based on current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        wildcard_dir = os.path.join(current_dir, 'wildcard')
    
    wildcards = {}
    
    if not os.path.exists(wildcard_dir):
        print(f"Warning: Wildcard directory not found: {wildcard_dir}")
        return wildcards
    
    # Get all .txt files in wildcard folder
    txt_files = glob.glob(os.path.join(wildcard_dir, "*.txt"))
    
    # First pass: Load all files without processing nested wildcards
    for file_path in txt_files:
        try:
            # Remove extension from filename and add underscore prefix
            filename = os.path.basename(file_path)
            var_name = "_" + os.path.splitext(filename)[0]
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Process: remove empty lines and lines starting with #
            processed_lines = []
            for line in lines:
                line = line.strip()  # Remove leading/trailing whitespace
                if line and not line.startswith('#'):  # Not empty and doesn't start with #
                    processed_lines.append(line)
            
            wildcards[var_name] = processed_lines
            print(f"Loaded wildcard: {var_name} ({len(processed_lines)} items from {filename})")
            
        except Exception as e:
            print(f"Error loading wildcard file {file_path}: {e}")
    
    # Second pass: Process nested wildcards
    _expand_nested_wildcards(wildcards)
    
    return wildcards


def _expand_nested_wildcards(wildcards):
    """
    Expand nested wildcard references in wildcard entries
    
    Args:
        wildcards: Dictionary of wildcard variables to process in-place
        
    Notes:
        - Processes {wildcard_name} patterns
        - Handles multiple references per line
        - Prevents infinite recursion
    """
    import re
    
    # Pattern to match {wildcard_name}
    pattern = re.compile(r'\{([^}]+)\}')
    
    for var_name, entries in wildcards.items():
        expanded_entries = []
        
        for entry in entries:
            # Find all wildcard references in this entry
            matches = pattern.findall(entry)
            
            if matches:
                # Process each wildcard reference
                expanded_entry = entry
                for match in matches:
                    wildcard_ref = f"_{match}"  # Add underscore prefix
                    
                    if wildcard_ref in wildcards and wildcard_ref != var_name:  # Prevent self-reference
                        # Replace with random selection from referenced wildcard
                        try:
                            replacement = choice(wildcards[wildcard_ref])
                            expanded_entry = expanded_entry.replace(f"{{{match}}}", replacement)
                        except Exception as e:
                            print(f"Warning: Could not expand wildcard {{{match}}} in {var_name}: {e}")
                            # Leave the reference as-is if expansion fails
                    else:
                        if wildcard_ref == var_name:
                            print(f"Warning: Self-reference detected in {var_name}: {{{match}}}")
                        else:
                            print(f"Warning: Referenced wildcard not found: {{{match}}} in {var_name}")
                
                expanded_entries.append(expanded_entry)
            else:
                # No wildcard references, keep as-is
                expanded_entries.append(entry)
        
        # Update the entries with expanded versions
        wildcards[var_name] = expanded_entries


class WildcardManager:
    """
    ワイルドカードファイルの管理クラス
    指定されたパスからワイルドカードを読み込み、キャッシュ機能を提供
    """
    
    def __init__(self, wildcard_dir=None):
        """
        Constructor for WildcardManager
        
        Args:
            wildcard_dir: Path to wildcard folder (auto-detected if omitted)
        """
        if wildcard_dir is None:
            # Find wildcard folder based on current script directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Default to 'wildcard' to keep consistent with load_wildcards()
            wildcard_dir = os.path.join(current_dir, 'wildcard')
        
        self.wildcard_dir = wildcard_dir
        self._cached_wildcards = None
    
    def load_wildcards(self):
        """
        Load text files from wildcard folder
        
        Returns:
            dict: Dictionary with filename as key (no extension, with underscore prefix)
        """
        wildcards = {}
        
        if not os.path.exists(self.wildcard_dir):
            print(f"Warning: Wildcard directory not found: {self.wildcard_dir}")
            return wildcards
        
        # Get all .txt files in wildcard folder
        txt_files = glob.glob(os.path.join(self.wildcard_dir, "*.txt"))
        
        # First pass: Load all files without processing nested wildcards
        for file_path in txt_files:
            try:
                # Remove extension from filename and add underscore prefix
                filename = os.path.basename(file_path)
                var_name = "_" + os.path.splitext(filename)[0]
                
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Process: remove empty lines and lines starting with #
                processed_lines = []
                for line in lines:
                    line = line.strip()  # Remove leading/trailing whitespace
                    if line and not line.startswith('#'):  # Not empty and doesn't start with #
                        processed_lines.append(line)
                
                wildcards[var_name] = processed_lines
                print(f"[WildcardManager] Loaded: {var_name} ({len(processed_lines)} items from {filename})")
                
            except Exception as e:
                print(f"[WildcardManager] Error loading file {file_path}: {e}")
        
        # Second pass: Process nested wildcards
        _expand_nested_wildcards(wildcards)
        
        return wildcards
        
        return wildcards
    
    def get_wildcard_vars(self):
        """
        Get dictionary of variables loaded from wildcard files
        Cached on first load, then accessible at high speed
        
        Returns:
            dict: Dictionary of wildcard variables
        """
        if self._cached_wildcards is None:
            self._cached_wildcards = self.load_wildcards()
        return self._cached_wildcards
    
    def refresh_wildcards(self):
        """
        Clear wildcard cache and reload
        Use when adding new wildcard files
        
        Returns:
            dict: Updated wildcard variables dictionary
        """
        self._cached_wildcards = None
        return self.get_wildcard_vars()
    
    def update_globals(self, target_globals=None):
        """
        Add wildcard variables to global variables
        
        Args:
            target_globals: Target global dictionary (caller's globals() if omitted)
        
        Returns:
            dict: Dictionary of added wildcard variables
        """
        if target_globals is None:
            import inspect
            frame = inspect.currentframe().f_back
            target_globals = frame.f_globals
        
        wildcard_vars = self.get_wildcard_vars()
        target_globals.update(wildcard_vars)
        return wildcard_vars


# Hold wildcard as global variable (for backward compatibility)
_cached_wildcards = None

def get_wildcard_vars():
    """
    Get dictionary of variables loaded from wildcard files
    Cached on first load, then accessible at high speed
    
    Returns:
        dict: Dictionary of wildcard variables
    """
    global _cached_wildcards
    if _cached_wildcards is None:
        _cached_wildcards = load_wildcards()
    return _cached_wildcards


def refresh_wildcards():
    """
    Clear wildcard cache and reload
    Use when adding new wildcard files
    
    Returns:
        dict: Updated wildcard variables dictionary
    """
    global _cached_wildcards
    _cached_wildcards = None
    return get_wildcard_vars()


def flatten(nested_list, depth=None):
    """
    Flatten nested arrays into a one-dimensional array
    Empty strings are ignored
    
    Args:
        nested_list: Nested array to flatten
        depth: Flattening depth (complete flattening if omitted)
               1 for 1 level only, 2 for up to 2 levels
        
    Returns:
        list: Flattened one-dimensional array (empty strings excluded)
        
    Examples:
        >>> flatten([1, [2, 3], [4, [5, 6]]])
        [1, 2, 3, 4, 5, 6]
        
        >>> flatten([[1, 2], [3, 4], [5, 6]])
        [1, 2, 3, 4, 5, 6]
        
        >>> flatten([1, [2, [3, [4]]]], depth=1)
        [1, 2, [3, [4]]]
        
        >>> flatten([1, [2, [3, [4]]]], depth=2)
        [1, 2, 3, [4]]
        
        >>> flatten(["a", ["b", "c"], "d"])
        ['a', 'b', 'c', 'd']
        
        >>> flatten(["hello", "", ["world", ""], "!"])
        ['hello', 'world', '!']  # Empty strings are excluded
        
        >>> flatten([choice(["apple", "banana"]), ["red", "blue"]])
        # choice results and array elements are flattened
    """
    def _flatten_recursive(lst, current_depth):
        """Internal function for recursive flattening"""
        if not isinstance(lst, (list, tuple)):
            # Check and exclude empty strings
            if lst == "":
                return []
            return [lst]
        
        result = []
        for item in lst:
            if isinstance(item, (list, tuple)) and (depth is None or current_depth < depth):
                # For nested arrays/tuples, recursively flatten
                result.extend(_flatten_recursive(item, current_depth + 1))
            else:
                # Normal element or depth limit reached
                # Add only if not empty string
                if item != "":
                    result.append(item)
        return result
    
    if not isinstance(nested_list, (list, tuple)):
        # If not an array
        if nested_list == "":
            return []  # Return empty array for empty string
        return [nested_list]
    
    return _flatten_recursive(nested_list, 0)


def maybe(value, probability=0.5):
    """
    Utility function that randomly returns argument or empty string
    
    Args:
        value: Value that may be returned (string, array, other)
        probability: Probability of returning original value (0.0-1.0, default: 0.5)
    
    Returns:
        Argument value or empty string ("")
        
    Examples:
        >>> maybe("test")
        "test"  # or ""
        
        >>> maybe(["apple", "banana"])
        ["apple", "banana"]  # or ""
        
        >>> maybe("test", 0.8)  # Return "test" with 80% probability
        "test"  # or ""
        
        >>> ["a", maybe("test")]
        ["a", "test"]  # or ["a", ""]
    """
    if random.random() < probability:
        return value
    else:
        return ""
