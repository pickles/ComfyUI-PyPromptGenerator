"""
Tests for flatten function
"""
import pytest
from src.pyprompt_generator.utils import flatten, choice


class TestFlatten:
    """Test class for flatten function"""
    
    def test_flatten_simple_nested_list(self):
        """Test simple nested array"""
        nested = [1, [2, 3], [4, [5, 6]]]
        expected = [1, 2, 3, 4, 5, 6]
        assert flatten(nested) == expected
    
    def test_flatten_two_level_nested(self):
        """Test 2-level nested array"""
        nested = [[1, 2], [3, 4], [5, 6]]
        expected = [1, 2, 3, 4, 5, 6]
        assert flatten(nested) == expected
    
    def test_flatten_with_depth_limit(self):
        """Test with depth limit"""
        nested = [1, [2, [3, [4]]]]
        
        # Depth 1
        result1 = flatten(nested, depth=1)
        expected1 = [1, 2, [3, [4]]]
        assert result1 == expected1
        
        # Depth 2
        result2 = flatten(nested, depth=2)
        expected2 = [1, 2, 3, [4]]
        assert result2 == expected2
    
    def test_flatten_strings(self):
        """Test array containing strings"""
        nested = ["a", ["b", "c"], "d"]
        expected = ["a", "b", "c", "d"]
        assert flatten(nested) == expected
    
    def test_flatten_mixed_types(self):
        """Test mixed types"""
        nested = [1, ["hello", 2.5], [True, [None, "world"]]]
        expected = [1, "hello", 2.5, True, None, "world"]
        assert flatten(nested) == expected
    
    def test_flatten_empty_list(self):
        """Test empty array"""
        assert flatten([]) == []
    
    def test_flatten_single_element(self):
        """Test single element"""
        assert flatten([42]) == [42]
        assert flatten(42) == [42]  # When not an array
    
    def test_flatten_already_flat(self):
        """Test already flat array"""
        flat = [1, 2, 3, 4, 5]
        assert flatten(flat) == flat
    
    def test_flatten_deeply_nested(self):
        """Test deeply nested array"""
        deeply_nested = [1, [2, [3, [4, [5]]]]]
        expected = [1, 2, 3, 4, 5]
        assert flatten(deeply_nested) == expected
    
    def test_flatten_with_tuples(self):
        """Test with tuples"""
        nested = [1, (2, 3), [4, (5, 6)]]
        expected = [1, 2, 3, 4, 5, 6]
        assert flatten(nested) == expected
    
    def test_flatten_empty_sublists(self):
        """Test with empty sublists"""
        nested = [1, [], [2, 3], [], [4]]
        expected = [1, 2, 3, 4]
        assert flatten(nested) == expected
    
    def test_flatten_with_choice_function(self):
        """Test combination with choice function"""
        # Flatten combination of choice function results and lists
        import random
        random.seed(42)  # Fix test results
        
        # Nested array containing choice function results
        nested = [choice(["apple", "banana"]), ["red", "blue"], choice(["small", "large"])]
        result = flatten(nested)
        
        # Result should be a flat array with 4 elements
        assert len(result) == 4  # choice result 1 + red + blue + choice result 1
        assert "red" in result
        assert "blue" in result
        assert result[0] in ["apple", "banana"]
        assert result[3] in ["small", "large"]
    
    def test_flatten_complex_example(self):
        """Test complex usage example"""
        # Real usage example: combination in prompt generation
        style = ["realistic", "anime"]
        colors = [["red", "blue"], ["green", "yellow"]]
        quality = "high quality"
        
        nested = [style, colors, quality]
        result = flatten(nested)
        expected = ["realistic", "anime", "red", "blue", "green", "yellow", "high quality"]
        assert result == expected
