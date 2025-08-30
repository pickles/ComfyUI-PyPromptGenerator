"""
Unit tests for utility functions
"""

import pytest
import random
from collections import Counter
from src.pyprompt_generator.utils import (
    weighted_choice, shuffle_list, random_range, random_boolean, 
    join, maybe, flatten
)


@pytest.mark.unit
class TestUtilityFunctions:
    """Test cases for utility functions in utils.py"""
    
    def test_weighted_choice_basic(self):
        """Test basic weighted_choice functionality"""
        items = ["apple", "banana", "cherry"]
        weights = [3, 1, 1]
        
        # Test multiple selections to check distribution
        results = Counter()
        trials = 1000
        
        for _ in range(trials):
            result = weighted_choice(items, weights)
            results[result] += 1
        
        # Apple should be selected roughly 3x more than banana or cherry
        apple_ratio = results["apple"] / max(results["banana"], 1)
        assert apple_ratio > 2.0, f"Apple should be selected more frequently (ratio: {apple_ratio})"
    
    def test_weighted_choice_no_weights(self):
        """Test weighted_choice without specifying weights"""
        items = ["a", "b", "c"]
        result = weighted_choice(items)
        
        assert result in items, "Should return one of the items"
    
    def test_weighted_choice_empty_list(self):
        """Test weighted_choice with empty list"""
        result = weighted_choice([])
        assert result is None, "Should return None for empty list"
    
    def test_shuffle_list(self):
        """Test shuffle_list functionality"""
        original = [1, 2, 3, 4, 5]
        shuffled = shuffle_list(original)
        
        # Original should be unchanged
        assert original == [1, 2, 3, 4, 5], "Original list should not be modified"
        
        # Shuffled should contain same elements
        assert sorted(shuffled) == sorted(original), "Shuffled list should contain same elements"
        
        # Should eventually produce different order (test multiple times)
        different_order_found = False
        for _ in range(10):
            test_shuffle = shuffle_list(original)
            if test_shuffle != original:
                different_order_found = True
                break
        
        assert different_order_found, "Shuffle should produce different order"
    
    def test_shuffle_list_empty(self):
        """Test shuffle_list with empty list"""
        result = shuffle_list([])
        assert result == [], "Should return empty list for empty input"
    
    def test_random_range_integers(self):
        """Test random_range with integers"""
        # Test multiple calls to ensure range is respected
        for _ in range(100):
            result = random_range(1, 10)
            assert 1 <= result <= 10, f"Result {result} should be between 1 and 10"
            assert isinstance(result, int), "Result should be integer"
    
    def test_random_range_with_step(self):
        """Test random_range with step parameter"""
        # Test with step of 2
        for _ in range(50):
            result = random_range(0, 10, 2)
            assert result in [0, 2, 4, 6, 8, 10], f"Result {result} should be even number"
    
    def test_random_range_floats(self):
        """Test random_range with float step"""
        # Test with float step
        for _ in range(50):
            result = random_range(0, 1, 0.1)
            assert 0 <= result <= 1, f"Result {result} should be between 0 and 1"
            # Check if result is approximately a multiple of 0.1
            assert abs(result - round(result, 1)) < 0.001, f"Result {result} should be multiple of 0.1"
    
    def test_random_boolean_default(self):
        """Test random_boolean with default probability"""
        # Test multiple calls to check distribution
        true_count = 0
        trials = 1000
        
        for _ in range(trials):
            if random_boolean():
                true_count += 1
        
        # Should be roughly 50% (allow for some variance)
        ratio = true_count / trials
        assert 0.4 < ratio < 0.6, f"Default probability should be around 0.5, got {ratio}"
    
    def test_random_boolean_custom_probability(self):
        """Test random_boolean with custom probabilities"""
        # Test with 80% probability
        true_count = 0
        trials = 1000
        
        for _ in range(trials):
            if random_boolean(0.8):
                true_count += 1
        
        # Should be roughly 80% (allow for some variance)
        ratio = true_count / trials
        assert 0.7 < ratio < 0.9, f"80% probability should be around 0.8, got {ratio}"
        
        # Test with 20% probability
        true_count = 0
        for _ in range(trials):
            if random_boolean(0.2):
                true_count += 1
        
        ratio = true_count / trials
        assert 0.1 < ratio < 0.3, f"20% probability should be around 0.2, got {ratio}"
    
    def test_random_boolean_edge_cases(self):
        """Test random_boolean with edge case probabilities"""
        # Test with 0% probability
        for _ in range(100):
            assert random_boolean(0.0) == False, "0% probability should always return False"
        
        # Test with 100% probability
        for _ in range(100):
            assert random_boolean(1.0) == True, "100% probability should always return True"
    
    def test_join_basic(self):
        """Test basic join functionality"""
        # Test with strings
        result = join(["apple", "banana", "cherry"])
        assert result == "apple, banana, cherry", f"Expected 'apple, banana, cherry', got '{result}'"
        
        # Test with custom separator
        result = join(["red", "blue", "green"], " | ")
        assert result == "red | blue | green", f"Expected 'red | blue | green', got '{result}'"
        
        # Test with numbers
        result = join([1, 2, 3], "-")
        assert result == "1-2-3", f"Expected '1-2-3', got '{result}'"
    
    def test_join_edge_cases(self):
        """Test join with edge cases"""
        # Test with empty list
        result = join([])
        assert result == "", f"Expected empty string for empty list, got '{result}'"
        
        # Test with single item
        result = join(["single"])
        assert result == "single", f"Expected 'single', got '{result}'"
        
        # Test with mixed types
        result = join([1, "two", 3.0, True], " ")
        assert result == "1 two 3.0 True", f"Expected '1 two 3.0 True', got '{result}'"
        
        # Test with empty strings in list
        result = join(["", "middle", ""], "-")
        assert result == "-middle-", f"Expected '-middle-', got '{result}'"
    
    def test_join_break_functionality(self):
        """Test join with BREAK special handling"""
        # Test with single BREAK
        result = join(["a", "b", "BREAK", "c"])
        expected = "a, b\nBREAK\nc"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with BREAK at the beginning
        result = join(["BREAK", "a", "b"])
        expected = "BREAK\na, b"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with BREAK at the end
        result = join(["a", "b", "BREAK"])
        expected = "a, b\nBREAK"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with multiple BREAKs
        result = join(["start", "BREAK", "middle", "BREAK", "end"])
        expected = "start\nBREAK\nmiddle\nBREAK\nend"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with only BREAK
        result = join(["BREAK"])
        expected = "BREAK"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with custom separator and BREAK
        result = join(["a", "b", "BREAK", "c", "d"], " | ")
        expected = "a | b\nBREAK\nc | d"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        
        # Test with consecutive BREAKs
        result = join(["a", "BREAK", "BREAK", "b"])
        expected = "a\nBREAK\n\nBREAK\nb"
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    def test_all_utils_available_in_script(self):
        """Test that all utility functions are available in script execution"""
        from src.pyprompt_generator.nodes import PyPromptGeneratorNode
        
        script = """
# Test all utility functions
items = ["a", "b", "c"]

# Test choice function
selected = choice(items)
result1 = selected in items

# Test weighted_choice
weighted = weighted_choice(["x", "y"], [1, 2])
result2 = weighted in ["x", "y"]

# Test shuffle_list
shuffled = shuffle_list([1, 2, 3])
result3 = len(shuffled) == 3

# Test random_range
num = random_range(1, 5)
result4 = 1 <= num <= 5

# Test random_boolean
bool_val = random_boolean(0.5)
result5 = isinstance(bool_val, bool)

# Test join function
joined = join(["hello", "world"])
result6 = joined == "hello, world"

# Test join with custom separator
joined_custom = join([1, 2, 3], "-")
result7 = joined_custom == "1-2-3"

# Test flatten function
nested = [1, [2, "", 3], "", [4, [5, ""]]]
flattened = flatten(nested)
result8 = flattened == [1, 2, 3, 4, 5]

# Test maybe function
maybe_result = maybe("test", 1.0)  # 100% probability
result9 = maybe_result == "test"

maybe_empty = maybe("test", 0.0)   # 0% probability
result10 = maybe_empty == ""

# All tests should pass
all_passed = result1 and result2 and result3 and result4 and result5 and result6 and result7 and result8 and result9 and result10
positive_prompt = f"All utils work: {all_passed}"
negative_prompt = "test negative"
"""
        
        node = PyPromptGeneratorNode()
        result = node.execute(script)
        
        positive, negative = result
        assert "True" in positive, f"All utility functions should work in script: {positive}"
    
    def test_maybe_function(self):
        """Test maybe function for random empty string return"""
        # Test with 100% probability (should always return the value)
        for _ in range(10):
            result = maybe("test", 1.0)
            assert result == "test", f"Expected 'test' with 100% probability, got '{result}'"
        
        # Test with 0% probability (should always return empty string)
        for _ in range(10):
            result = maybe("test", 0.0)
            assert result == "", f"Expected '' with 0% probability, got '{result}'"
        
        # Test with list input
        test_list = ["apple", "banana"]
        result_100 = maybe(test_list, 1.0)
        assert result_100 == test_list, f"Expected {test_list} with 100% probability, got {result_100}"
        
        result_0 = maybe(test_list, 0.0)
        assert result_0 == "", f"Expected '' with 0% probability, got '{result_0}'"
        
        # Test with default probability (50%)
        results = set()
        for _ in range(100):
            result = maybe("test")
            results.add(result)
        
        # Should get both "test" and "" over many trials
        assert "test" in results, "Should sometimes return the original value"
        assert "" in results, "Should sometimes return empty string"
        
        # Test with different probability values
        high_prob_count = 0
        low_prob_count = 0
        trials = 200
        
        for _ in range(trials):
            if maybe("test", 0.8) == "test":
                high_prob_count += 1
            if maybe("test", 0.2) == "test":
                low_prob_count += 1
        
        # 80% should give more results than 20%
        assert high_prob_count > low_prob_count, "Higher probability should yield more positive results"
        
        # Check rough ranges (allowing for randomness)
        high_ratio = high_prob_count / trials
        low_ratio = low_prob_count / trials
        
        assert 0.6 < high_ratio < 1.0, f"80% probability should be around 0.8, got {high_ratio}"
        assert 0.0 < low_ratio < 0.4, f"20% probability should be around 0.2, got {low_ratio}"
    
    def test_maybe_edge_cases(self):
        """Test maybe function edge cases"""
        # Test with None
        result = maybe(None, 1.0)
        assert result is None, f"Expected None, got {result}"
        
        result = maybe(None, 0.0)
        assert result == "", f"Expected '', got {result}"
        
        # Test with empty string input
        result = maybe("", 1.0)
        assert result == "", f"Expected '', got {result}"
        
        # Test with numeric input
        result = maybe(42, 1.0)
        assert result == 42, f"Expected 42, got {result}"
        
        result = maybe(42, 0.0)
        assert result == "", f"Expected '', got {result}"
        
        # Test with boolean input
        result = maybe(True, 1.0)
        assert result is True, f"Expected True, got {result}"
        
        result = maybe(False, 0.0)
        assert result == "", f"Expected '', got {result}"
    
    def test_flatten_empty_string_filtering(self):
        """Test flatten function filters out empty strings"""
        # Test basic empty string filtering
        result = flatten(["a", "", "b", "c"])
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result}"
        
        # Test nested empty string filtering
        result = flatten(["a", ["", "b"], "c", ""])
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result}"
        
        # Test deep nested empty string filtering
        result = flatten([1, [2, "", [3, "", 4]], "", 5])
        assert result == [1, 2, 3, 4, 5], f"Expected [1, 2, 3, 4, 5], got {result}"
        
        # Test with only empty strings
        result = flatten(["", "", ["", ""]])
        assert result == [], f"Expected [], got {result}"
        
        # Test mixed with None values (should keep None)
        result = flatten(["a", "", None, "b"])
        assert result == ["a", None, "b"], f"Expected ['a', None, 'b'], got {result}"
        
        # Test empty strings at various positions
        result = flatten(["", "start", ["middle", ""], "end", ""])
        assert result == ["start", "middle", "end"], f"Expected ['start', 'middle', 'end'], got {result}"
    
    def test_flatten_with_tuples_and_empty_strings(self):
        """Test flatten with tuples containing empty strings"""
        # Test tuple with empty strings
        result = flatten([("a", "", "b"), "c"])
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result}"
        
        # Test nested tuples with empty strings
        result = flatten([1, (2, ("", 3)), ""])
        assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"
    
    def test_flatten_depth_limit_with_empty_strings(self):
        """Test flatten with depth limit and empty strings"""
        # Test depth 1 with empty strings
        nested = ["a", "", ["b", "", ["c", ""]]]
        result = flatten(nested, depth=1)
        assert result == ["a", "b", ["c", ""]], f"Expected ['a', 'b', ['c', '']], got {result}"
        
        # Test depth 2 with empty strings
        result = flatten(nested, depth=2)
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result}"
