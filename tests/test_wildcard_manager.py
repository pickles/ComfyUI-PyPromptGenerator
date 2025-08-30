"""
WildcardManager class tests
"""
import pytest
import os
import tempfile
from src.pyprompt_generator.utils import WildcardManager


class TestWildcardManager:
    """Test class for WildcardManager class"""
    
    def test_wildcard_manager_initialization(self):
        """Test WildcardManager initialization"""
        # Initialize with default path
        wm = WildcardManager()
        assert wm.wildcard_dir.endswith('wildcard')
        assert wm._cached_wildcards is None
        
        # Initialize with custom path
        custom_path = "/custom/path"
        wm_custom = WildcardManager(custom_path)
        assert wm_custom.wildcard_dir == custom_path
    
    def test_wildcard_manager_with_existing_files(self):
        """Test with existing wildcard files"""
        # Use current directory's wildcard folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        wildcard_dir = os.path.join(os.path.dirname(current_dir), 'wildcard')
        
        if os.path.exists(wildcard_dir):
            wm = WildcardManager(wildcard_dir)
            
            # Get wildcard variables
            wildcard_vars = wm.get_wildcard_vars()
            
            # Basic validation
            assert isinstance(wildcard_vars, dict)
            
            # Cache test
            cached_vars = wm.get_wildcard_vars()
            assert wildcard_vars is cached_vars  # Confirm it's the same object
            
            # Refresh test
            refreshed_vars = wm.refresh_wildcards()
            assert isinstance(refreshed_vars, dict)
    
    def test_wildcard_manager_with_temp_files(self):
        """Test with temporary files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test_styles.txt")
            with open(test_file1, 'w', encoding='utf-8') as f:
                f.write("# Style list\nrealistic\nanime\n\n# Empty lines and comment test\noil painting\n")
            
            test_file2 = os.path.join(temp_dir, "test_colors.txt")
            with open(test_file2, 'w', encoding='utf-8') as f:
                f.write("red\nblue\ngreen\n")
            
            # Test with WildcardManager
            wm = WildcardManager(temp_dir)
            wildcard_vars = wm.get_wildcard_vars()
            
            # Confirm expected variables exist
            assert '_test_styles' in wildcard_vars
            assert '_test_colors' in wildcard_vars
            
            # Confirm content
            assert wildcard_vars['_test_styles'] == ['realistic', 'anime', 'oil painting']
            assert wildcard_vars['_test_colors'] == ['red', 'blue', 'green']
    
    def test_wildcard_manager_nonexistent_directory(self):
        """Test with non-existent directory"""
        nonexistent_path = "/path/that/does/not/exist"
        wm = WildcardManager(nonexistent_path)
        
        wildcard_vars = wm.get_wildcard_vars()
        
        # Confirm empty dictionary is returned
        assert isinstance(wildcard_vars, dict)
        assert len(wildcard_vars) == 0
    
    def test_wildcard_manager_cache_behavior(self):
        """Test cache behavior"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initial file
            test_file = os.path.join(temp_dir, "cache_test.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("initial\nvalue\n")
            
            wm = WildcardManager(temp_dir)
            
            # Initial load
            vars1 = wm.get_wildcard_vars()
            assert vars1['_cache_test'] == ['initial', 'value']
            
            # Modify file
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("updated\nvalue\nnew_item\n")
            
            # No change due to caching
            vars2 = wm.get_wildcard_vars()
            assert vars2['_cache_test'] == ['initial', 'value']
            
            # Updated after refresh
            vars3 = wm.refresh_wildcards()
            assert vars3['_cache_test'] == ['updated', 'value', 'new_item']
    
    def test_wildcard_manager_path_consistency(self):
        """Test path consistency"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "path_test.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("test_item\n")
            
            # Multiple instances with same path
            wm1 = WildcardManager(temp_dir)
            wm2 = WildcardManager(temp_dir)
            
            vars1 = wm1.get_wildcard_vars()
            vars2 = wm2.get_wildcard_vars()
            
            # Same content but different instances
            assert vars1 == vars2
            assert vars1 is not vars2  # Different instances
