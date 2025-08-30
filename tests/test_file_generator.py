"""
Tests for PyPromptFileGeneratorNode
"""
import pytest
import os
import tempfile
from unittest.mock import patch


class TestPyPromptFileGeneratorNode:
    """Test class for PyPromptFileGeneratorNode"""
    
    def test_file_generator_node_initialization(self):
        """Test PyPromptFileGeneratorNode initialization"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        node = PyPromptFileGeneratorNode()
        assert node is not None
    
    def test_input_types(self):
        """Test input types configuration"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        input_types = PyPromptFileGeneratorNode.INPUT_TYPES()
        
        assert "required" in input_types
        assert "script_file" in input_types["required"]
        assert "optional" in input_types
        assert "base_path" in input_types["optional"]
    
    def test_execute_with_existing_file(self):
        """Test execution with an existing script file"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('''
# Test script
positive_prompt = "test positive prompt"
negative_prompt = "test negative prompt"
''')
            temp_file = f.name
        
        try:
            node = PyPromptFileGeneratorNode()
            result = node.execute(os.path.basename(temp_file), os.path.dirname(temp_file))
            
            positive, negative = result
            assert positive == "test positive prompt"
            assert negative == "test negative prompt"
        finally:
            os.unlink(temp_file)
    
    def test_execute_with_nonexistent_file(self):
        """Test execution with non-existent file"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        node = PyPromptFileGeneratorNode()
        result = node.execute("nonexistent_file.py", "/nonexistent/path")
        
        positive, negative = result
        assert "Error:" in positive
        assert "file not found" in negative
    
    def test_execute_with_script_using_utils(self):
        """Test execution with script that uses utility functions"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        # Create a script that uses utility functions
        script_content = '''
# Script using utility functions (without import statements)
# random module is already available

items = ["apple", "banana", "cherry"]
selected = choice(items)
count = random_range(1, 5)

positive_prompt = f"Selected: {selected}, Count: {count}"
negative_prompt = "test negative"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            temp_file = f.name
        
        try:
            node = PyPromptFileGeneratorNode()
            result = node.execute(os.path.basename(temp_file), os.path.dirname(temp_file))
            
            positive, negative = result
            assert "Selected:" in positive
            assert "Count:" in positive
            assert negative == "test negative"
        finally:
            os.unlink(temp_file)
    
    def test_execute_with_script_error(self):
        """Test execution with script that contains errors"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        # Create a script with syntax error
        script_content = '''
# Script with error
invalid_syntax = 
positive_prompt = "should not reach here"
negative_prompt = "should not reach here"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            temp_file = f.name
        
        try:
            node = PyPromptFileGeneratorNode()
            result = node.execute(os.path.basename(temp_file), os.path.dirname(temp_file))
            
            positive, negative = result
            assert "Script Error:" in positive
            assert negative == "error"
        finally:
            os.unlink(temp_file)
    
    def test_is_changed_file_modification(self):
        """Test IS_CHANGED method with file modification detection"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write("# Test file")
            temp_file = f.name
        
        try:
            # First call
            result1 = PyPromptFileGeneratorNode.IS_CHANGED(
                os.path.basename(temp_file), 
                os.path.dirname(temp_file)
            )
            
            # Modify file
            import time
            time.sleep(0.1)  # Ensure different modification time
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write("# Modified test file")
            
            # Second call should return different value
            result2 = PyPromptFileGeneratorNode.IS_CHANGED(
                os.path.basename(temp_file), 
                os.path.dirname(temp_file)
            )
            
            assert result1 != result2  # Should be different due to file modification
        finally:
            os.unlink(temp_file)
    
    def test_default_script_file_execution(self):
        """Test execution with default script file if it exists"""
        from src.pyprompt_generator.nodes import PyPromptFileGeneratorNode
        
        # Check if the default script file exists
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        default_script = os.path.join(parent_dir, "scripts", "prompt_script.py")
        
        if os.path.exists(default_script):
            node = PyPromptFileGeneratorNode()
            result = node.execute("tests/sample_scripts/prompt_script.py")
            
            positive, negative = result
            # Should not contain error messages
            assert not positive.startswith("Error:")
            assert not positive.startswith("Script Error:")
            assert negative != "file not found"
            assert negative != "error"
