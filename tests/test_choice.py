"""
Unit tests for the choice utility function
"""

import pytest
import random
from collections import Counter
from src.pyprompt_generator.utils import flatten


@pytest.mark.unit
class TestChoiceFunction:
    """Test cases for the choice utility function"""
    
    def test_basic_single_selection(self, choice_function):
        """Test basic single item selection"""
        basic_items = ["apple", "banana", "cherry"]
        
        # Test multiple selections to ensure all items can be selected
        results = set()
        for _ in range(50):
            result = choice_function(basic_items)
            assert result in basic_items, f"Invalid selection: {result}"
            results.add(result)
        
        # All items should be selectable
        assert len(results) >= 2, "Should be able to select different items"
    
    def test_multiple_selection_no_duplicates(self, choice_function):
        """Test multiple selection without duplicates"""
        basic_items = ["apple", "banana", "cherry", "date", "elderberry"]
        
        result = choice_function(basic_items, 3)
        
        assert len(result) == 3, f"Expected 3 items, got {len(result)}"
        assert len(set(result)) == 3, "Duplicates found in multiple selection"
        assert all(item in basic_items for item in result), "Invalid items selected"
    
    @pytest.mark.slow
    def test_weighted_selection_distribution(self, choice_function):
        """Test that weighted selection follows expected distribution"""
        weighted_items = ["3::apple", "1::banana", "1::cherry"]
        results = Counter()
        trials = 1000
        
        for _ in range(trials):
            result = choice_function(weighted_items)
            results[result] += 1
        
        # Apple should be selected roughly 3x more than banana or cherry
        apple_count = results["apple"]
        banana_count = results["banana"]
        cherry_count = results["cherry"]
        
        apple_ratio = apple_count / max(banana_count, 1)
        assert apple_ratio > 2.0, f"Apple should be selected more frequently (ratio: {apple_ratio})"
        
        # Check that all items were selected
        assert apple_count > 0, "Apple should be selected"
        assert banana_count > 0, "Banana should be selected"
        assert cherry_count > 0, "Cherry should be selected"
    
    def test_mixed_weighted_and_unweighted(self, choice_function):
        """Test mixed weighted and unweighted items"""
        mixed_items = ["2::apple", "banana", "3::cherry", "orange"]
        # Expected weights: apple=2, banana=1, cherry=3, orange=1
        
        results = Counter()
        trials = 700
        
        for _ in range(trials):
            result = choice_function(mixed_items)
            results[result] += 1
        
        # Cherry should be most frequent (weight 3)
        # Apple should be second (weight 2)
        # Banana and orange should be least frequent (weight 1 each)
        cherry_count = results["cherry"]
        apple_count = results["apple"]
        banana_count = results["banana"]
        orange_count = results["orange"]
        
        assert cherry_count > apple_count, "Cherry should be selected more than apple"
        assert apple_count > banana_count, "Apple should be selected more than banana"
        assert apple_count > orange_count, "Apple should be selected more than orange"
    
    def test_multiple_weighted_selection(self, choice_function):
        """Test multiple selection with weights (no duplicates)"""
        weighted_items = ["4::alpha", "2::beta", "1::gamma", "1::delta"]
        
        result = choice_function(weighted_items, 3)
        
        assert len(result) == 3, f"Expected 3 items, got {len(result)}"
        assert len(set(result)) == 3, "Duplicates found in multiple weighted selection"
        
        valid_items = ["alpha", "beta", "gamma", "delta"]
        assert all(item in valid_items for item in result), "Invalid items selected"
    
    def test_empty_list(self, choice_function):
        """Test behavior with empty list"""
        result = choice_function([])
        assert result is None, f"Expected None for empty list, got {result}"
    
    def test_empty_list_multiple_selection(self, choice_function):
        """Test multiple selection from empty list"""
        result = choice_function([], 3)
        assert result == [], f"Expected empty list, got {result}"
    
    def test_single_item_list(self, choice_function):
        """Test selection from single item list"""
        result = choice_function(["only"])
        assert result == "only", f"Expected 'only', got {result}"
    
    def test_request_more_items_than_available(self, choice_function):
        """Test requesting more items than available"""
        result = choice_function(["a", "b"], 5)
        
        assert len(result) == 2, f"Expected 2 items (max available), got {len(result)}"
        assert set(result) == {"a", "b"}, "Incorrect items returned"
    
    def test_invalid_weight_format(self, choice_function):
        """Test handling of invalid weight format"""
        items_with_invalid_weight = ["invalid::weight::item", "normal"]
        
        # Should not raise an exception
        result = choice_function(items_with_invalid_weight)
        assert result in ["invalid::weight::item", "normal"], "Invalid weight format not handled"
    
    def test_zero_weight(self, choice_function):
        """Test handling of zero weight"""
        items_with_zero_weight = ["0::never_selected", "1::always_selected"]
        
        results = set()
        for _ in range(50):
            result = choice_function(items_with_zero_weight)
            results.add(result)
        
        # Zero weight item should never be selected
        assert "never_selected" not in results, "Zero weight item was selected"
        assert "always_selected" in results, "Non-zero weight item should be selected"
    
    def test_float_weights(self, choice_function):
        """Test handling of float weights"""
        items_with_float_weights = ["0.5::low", "1.5::high"]
        
        results = Counter()
        trials = 600
        
        for _ in range(trials):
            result = choice_function(items_with_float_weights)
            results[result] += 1
        
        # High should be selected roughly 3x more than low (1.5 vs 0.5)
        high_count = results["high"]
        low_count = results["low"]
        ratio = high_count / max(low_count, 1)
        
        assert ratio > 2.0, f"High weight item should be selected more frequently (ratio: {ratio})"
    
    @pytest.mark.parametrize("count", [1, 2, 3, 5])
    def test_different_count_values(self, choice_function, count):
        """Test different count values"""
        items = ["a", "b", "c", "d", "e", "f"]
        
        result = choice_function(items, count)
        
        expected_count = min(count, len(items))
        if count == 1:
            assert isinstance(result, str), "Single selection should return string"
            assert result in items, "Single selection should be valid item"
        else:
            assert isinstance(result, list), "Multiple selection should return list"
            assert len(result) == expected_count, f"Expected {expected_count} items, got {len(result)}"
            assert len(set(result)) == expected_count, "No duplicates should be present"
            assert all(item in items for item in result), "All items should be valid"
    
    def test_non_string_items(self, choice_function):
        """Test handling of non-string items"""
        numeric_items = [1, 2, 3, 4, 5]
        
        result = choice_function(numeric_items)
        assert result in numeric_items, "Should handle non-string items"
        
        mixed_items = [1, "2::string", 3.14]
        result = choice_function(mixed_items)
        # Should work without errors
        assert result is not None, "Should handle mixed type items"


@pytest.mark.unit
class TestFlattenFunction:
    """Test cases for the flatten utility function"""
    
    def test_basic_flatten(self):
        """Test basic flatten functionality"""
        
        # Test simple nested list
        result = flatten([1, [2, 3], 4])
        assert result == [1, 2, 3, 4], f"Expected [1, 2, 3, 4], got {result}"
        
        # Test deeply nested list
        result = flatten([1, [2, [3, [4]]]])
        assert result == [1, 2, 3, 4], f"Expected [1, 2, 3, 4], got {result}"
        
        # Test with strings
        result = flatten(["a", ["b", "c"], "d"])
        assert result == ["a", "b", "c", "d"], f"Expected ['a', 'b', 'c', 'd'], got {result}"
    
    def test_flatten_with_depth(self):
        """Test flatten with depth parameter"""
        
        nested = [1, [2, [3, [4]]]]
        
        # Depth 1
        result = flatten(nested, depth=1)
        assert result == [1, 2, [3, [4]]], f"Expected [1, 2, [3, [4]]], got {result}"
        
        # Depth 2
        result = flatten(nested, depth=2)
        assert result == [1, 2, 3, [4]], f"Expected [1, 2, 3, [4]], got {result}"
    
    def test_flatten_empty_string_filtering(self):
        """Test flatten function filters out empty strings"""
        
        # Test basic empty string filtering
        result = flatten(["hello", "", "world"])
        assert result == ["hello", "world"], f"Expected ['hello', 'world'], got {result}"
        
        # Test nested empty string filtering
        result = flatten(["a", ["", "b", ""], "c"])
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result}"
        
        # Test deep nested empty string filtering
        result = flatten([["", ["hello", ""]], ["", "world", ""]])
        assert result == ["hello", "world"], f"Expected ['hello', 'world'], got {result}"
        
        # Test with only empty strings
        result = flatten(["", ["", ""], ""])
        assert result == [], f"Expected [], got {result}"
        
        # Test with single empty string
        result = flatten("")
        assert result == [], f"Expected [], got {result}"
        
        # Test mixed content with empty strings
        result = flatten([1, "", ["", 2, ""], 3, [""]])
        assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"
        
        # Test empty strings preserved at specific depth
        result = flatten(["a", ["", ["b", ""]], ""], depth=1)
        assert result == ["a", ["b", ""]], f"Expected ['a', ['b', '']], got {result}"
    
    def test_flatten_edge_cases(self):
        """Test flatten edge cases"""
        
        # Test empty list
        result = flatten([])
        assert result == [], f"Expected [], got {result}"
        
        # Test non-list input
        result = flatten("single")
        assert result == ["single"], f"Expected ['single'], got {result}"
        
        # Test with tuples
        result = flatten([1, (2, 3), 4])
        assert result == [1, 2, 3, 4], f"Expected [1, 2, 3, 4], got {result}"
        
        # Test mixed list and tuple nesting
        result = flatten([(1, [2, (3, 4)]), 5])
        assert result == [1, 2, 3, 4, 5], f"Expected [1, 2, 3, 4, 5], got {result}"
