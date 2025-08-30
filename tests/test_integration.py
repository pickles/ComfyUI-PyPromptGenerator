"""
Integration tests for the PyPromptGeneratorNode
"""

import pytest
import json
from unittest.mock import patch


@pytest.mark.integration
class TestPyPromptGeneratorNode:
    """Integration tests for the complete node functionality"""
    
    def test_simple_script_execution(self, prompt_generator_node, sample_scripts):
        """Test basic script execution and output"""
        script = sample_scripts["simple"]
        
        result = prompt_generator_node.execute(
            script=script
        )
        
        assert isinstance(result, tuple), "Execute should return tuple"
        assert len(result) == 2, "Result should contain 2 items (positive, negative)"
        
        positive, negative = result
        assert positive == "beautiful landscape", "Incorrect positive prompt"
        assert negative == "ugly, blurry", "Incorrect negative prompt"
    
    def test_choice_function_integration(self, prompt_generator_node, sample_scripts):
        """Test that choice function works within node execution"""
        script = sample_scripts["with_choice"]
        
        # Run multiple times to test randomness
        results = set()
        for _ in range(20):
            result = prompt_generator_node.execute(
                script=script
            )
            
            assert isinstance(result, tuple), "Execute should return tuple"
            assert len(result) == 2, "Result should contain 2 items"
            
            positive, negative = result
            # Collect positive prompts to verify randomness
            results.add(positive)
        
        # Should have some variation in results
        assert len(results) > 1, "Choice function should produce different results"
        
        # All results should be from expected choices
        expected_positives = ["sunny day", "cloudy sky", "starry night"]
        for positive in results:
            assert positive in expected_positives, f"Unexpected positive result: {positive}"
    
    def test_weighted_choice_integration(self, prompt_generator_node):
        """Test weighted choice function within node execution"""
        script = """
# Test weighted choice
options = ["3::common", "1::rare", "1::very_rare"]
positive_prompt = choice(options)
negative_prompt = "low quality"
"""
        
        # Run many times to test weight distribution
        results = {"common": 0, "rare": 0, "very_rare": 0}
        trials = 100
        
        for _ in range(trials):
            result = prompt_generator_node.execute(
                script=script
            )
            
            positive, negative = result
            if positive in results:
                results[positive] += 1
        
        # Common should be selected most frequently
        assert results["common"] > results["rare"], "Common should be selected more than rare"
        assert results["common"] > results["very_rare"], "Common should be selected more than very_rare"
        
        # All options should be selected at least once
        assert results["common"] > 0, "Common should be selected"
        assert results["rare"] > 0, "Rare should be selected"
        assert results["very_rare"] > 0, "Very rare should be selected"
    
    def test_multiple_choice_integration(self, prompt_generator_node):
        """Test multiple choice selection within node execution"""
        script = """
# Test multiple choice
tags = ["fantasy", "portrait", "landscape", "anime", "photorealistic"]
selected = choice(tags, 3)
positive_prompt = ", ".join(selected)
negative_prompt = "low quality"
"""
        
        result = prompt_generator_node.execute(
            script=script
        )
        
        positive, negative = result
        positive_tags = positive.split(", ")
        assert len(positive_tags) == 3, f"Expected 3 tags, got {len(positive_tags)}"
        assert len(set(positive_tags)) == 3, "No duplicate tags should be present"
        
        expected_tags = ["fantasy", "portrait", "landscape", "anime", "photorealistic"]
        assert all(tag in expected_tags for tag in positive_tags), "All tags should be valid"
    
    def test_script_with_error(self, prompt_generator_node):
        """Test error handling in script execution"""
        script_with_error = """
# This script has an error
positive_prompt = undefined_variable  # This will cause a NameError
negative_prompt = "error test"
"""
        
        result = prompt_generator_node.execute(
            script=script_with_error
        )
        
        assert isinstance(result, tuple), "Execute should return tuple even on error"
        assert len(result) == 2, "Result should contain 2 items"
        
        positive, negative = result
        # Should return error information
        assert "Script Error:" in positive, "Should return error message in positive"
        assert negative == "error", "Should return 'error' in negative on script error"
    
    def test_console_logging(self, prompt_generator_node, sample_scripts):
        """Test that logs are always output to console"""
        script = sample_scripts["simple"]
        
        # Execute script - logs should always be printed to console
        result = prompt_generator_node.execute(
            script=script
        )
        
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should contain 2 items"
        
        # Note: This test verifies the function executes without error
        # Console output verification would require capturing stdout in a real test scenario
    
    def test_always_refresh_functionality(self, prompt_generator_node, sample_scripts):
        """Test that the node always refreshes (IS_CHANGED always returns different values)"""
        script = sample_scripts["simple"]
        
        # Test IS_CHANGED method - should always return different values
        import time
        changed_id_1 = prompt_generator_node.IS_CHANGED(script=script)
        time.sleep(0.001)  # Small delay to ensure different timestamp
        changed_id_2 = prompt_generator_node.IS_CHANGED(script=script)
        
        # Should always produce different change IDs since we always refresh
        different_ids_found = changed_id_1 != changed_id_2
        if not different_ids_found:
            # Try a few more times with longer delay
            for _ in range(3):
                time.sleep(0.01)
                new_id = prompt_generator_node.IS_CHANGED(script=script)
                if new_id != changed_id_1:
                    different_ids_found = True
                    break
        
        assert different_ids_found, "Always refresh should produce different change IDs"
    
    def test_complex_script_execution(self, prompt_generator_node):
        """Test execution of a complex script with multiple operations"""
        complex_script = """
# Complex prompt generation
base_styles = ["2::photorealistic", "1::anime", "1::oil painting"]
subjects = ["portrait", "landscape", "still life"]
modifiers = ["highly detailed", "masterpiece", "trending on artstation"]

style = choice(base_styles)
subject = choice(subjects)
selected_modifiers = choice(modifiers, 2)

positive_prompt = f"{style} {subject}, " + ", ".join(selected_modifiers)

# Generate negative with some logic
negative_base = ["low quality", "blurry", "amateur"]
if "photorealistic" in style:
    negative_base.append("cartoon")
elif "anime" in style:
    negative_base.append("realistic")

negative_prompt = ", ".join(choice(negative_base, min(3, len(negative_base))))
"""
        
        result = prompt_generator_node.execute(
            script=complex_script
        )
        
        assert isinstance(result, tuple), "Execute should return tuple"
        assert len(result) == 2, "Result should contain 2 items"
        
        positive, negative = result
        
        # Verify positive prompt structure
        assert any(style in positive for style in ["photorealistic", "anime", "oil painting"]), \
            "Positive should contain a style"
        assert any(subject in positive for subject in ["portrait", "landscape", "still life"]), \
            "Positive should contain a subject"
        
        # Verify negative prompt
        assert len(negative) > 0, "Negative should not be empty"
        assert any(neg in negative for neg in ["low quality", "blurry", "amateur"]), \
            "Negative should contain base negative terms"
    
    def test_join_function_integration(self, prompt_generator_node):
        """Test join function within node execution"""
        script = """
# Test join function
tags = ["fantasy", "portrait", "detailed"]
styles = ["realistic", "anime"]

# Basic join with default separator
joined_tags = join(tags)  # Should be "fantasy, portrait, detailed"

# Join with custom separator
joined_styles = join(styles, " | ")  # Should be "realistic | anime"

# Join with numbers and mixed types
numbers = [1, 2, 3]
joined_numbers = join(numbers, "-")  # Should be "1-2-3"

# Test BREAK functionality
break_test = ["a", "b", "BREAK", "c", "d"]
joined_break = join(break_test)  # Should be "a, b\\nBREAK\\nc, d"

positive_prompt = f"Tags: {joined_tags}, Styles: {joined_styles}, Numbers: {joined_numbers}"
negative_prompt = "low quality"
"""
        
        result = prompt_generator_node.execute(script=script)
        
        assert isinstance(result, tuple), "Execute should return tuple"
        assert len(result) == 2, "Result should contain 2 items"
        
        positive, negative = result
        
        # Verify join function results
        assert "fantasy, portrait, detailed" in positive, "Should contain joined tags with default separator"
        assert "realistic | anime" in positive, "Should contain joined styles with custom separator"
        assert "1-2-3" in positive, "Should contain joined numbers with dash separator"
    
    def test_node_input_types(self, prompt_generator_node):
        """Test node input type definitions"""
        input_types = prompt_generator_node.INPUT_TYPES()
        
        assert "required" in input_types, "Should have required inputs"
        required = input_types["required"]
        
        assert "script" in required, "Should have script input"
        
        # Check script input type
        script_input = required["script"]
        assert script_input[0] == "STRING", "Script should be STRING type"
        assert script_input[1]["multiline"] is True, "Script should be multiline"
    
    def test_node_return_types(self, prompt_generator_node):
        """Test node return type definitions"""
        return_types = prompt_generator_node.RETURN_TYPES
        expected_types = ("STRING", "STRING")  # positive, negative
        assert return_types == expected_types, f"Expected {expected_types}, got {return_types}"
        
        return_names = prompt_generator_node.RETURN_NAMES
        expected_names = ("positive_prompt", "negative_prompt")
        assert return_names == expected_names, f"Expected {expected_names}, got {return_names}"
    
    def test_node_metadata(self, prompt_generator_node):
        """Test node metadata and configuration"""
        assert hasattr(prompt_generator_node, "FUNCTION"), "Should have FUNCTION attribute"
        assert prompt_generator_node.FUNCTION == "execute", "Function should be 'execute'"
        
        assert hasattr(prompt_generator_node, "CATEGORY"), "Should have CATEGORY attribute"
        assert prompt_generator_node.CATEGORY == "utils", "Category should be 'utils'"
    
    @pytest.mark.slow
    def test_performance_with_large_script(self, prompt_generator_node):
        """Test performance with a larger script"""
        large_script = """
# Large script with many operations
choices = []
for i in range(100):
    choices.append(f"option_{i}")

# Generate multiple prompts
prompts = []
for i in range(10):
    selected = choice(choices, 5)
    prompts.append(", ".join(selected))

positive_prompt = " | ".join(prompts[:5])
negative_prompt = " | ".join(prompts[5:])
"""
        
        import time
        start_time = time.time()
        
        result = prompt_generator_node.execute(
            script=large_script
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert isinstance(result, tuple), "Should execute successfully"
        assert execution_time < 5.0, f"Execution too slow: {execution_time:.2f}s"
        
        positive, negative = result
        assert len(positive) > 0, "Should generate positive prompt"
        assert len(negative) > 0, "Should generate negative prompt"
