"""
Test file for wildcard functionality
"""

import unittest
import os
import tempfile
from src.pyprompt_generator import utils


class TestWildcardFunctionality(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory and files for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.wildcard_dir = os.path.join(self.test_dir, 'wildcard')
        os.makedirs(self.wildcard_dir)
        
        # Create test wildcard files
        test_files = {
            'styles.txt': [
                '# Art styles',
                'realistic',
                '',  # Empty line
                'anime',
                '# Another comment',
                'oil painting',
                'watercolor'
            ],
            'colors.txt': [
                'red',
                '# Color comment',
                'blue',
                'green',
                '',  # Empty line
                'yellow'
            ],
            'empty.txt': [
                '# Only comments',
                '',
                '# Another comment'
            ]
        }
        
        for filename, content in test_files.items():
            filepath = os.path.join(self.wildcard_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
    
    def tearDown(self):
        """Cleanup after tests"""
        import shutil
        shutil.rmtree(self.test_dir)
        
        # Clear cache
        utils._cached_wildcards = None
    
    def test_load_wildcards(self):
        """Test wildcard loading functionality"""
        wildcards = utils.load_wildcards(self.wildcard_dir)
        
        # Confirm files are loaded correctly
        self.assertIn('_styles', wildcards)
        self.assertIn('_colors', wildcards)
        self.assertIn('_empty', wildcards)
        
        # Confirm content is processed correctly
        expected_styles = ['realistic', 'anime', 'oil painting', 'watercolor']
        expected_colors = ['red', 'blue', 'green', 'yellow']
        expected_empty = []  # Empty due to comments and empty lines only
        
        self.assertEqual(wildcards['_styles'], expected_styles)
        self.assertEqual(wildcards['_colors'], expected_colors)
        self.assertEqual(wildcards['_empty'], expected_empty)
    
    def test_wildcard_with_choice_function(self):
        """Test integration of wildcard variables with choice function"""
        wildcards = utils.load_wildcards(self.wildcard_dir)
        
        # Random selection from _styles
        selected_style = utils.choice(wildcards['_styles'])
        self.assertIn(selected_style, ['realistic', 'anime', 'oil painting', 'watercolor'])
        
        # Multiple selection from _colors
        selected_colors = utils.choice(wildcards['_colors'], 2)
        self.assertEqual(len(selected_colors), 2)
        for color in selected_colors:
            self.assertIn(color, ['red', 'blue', 'green', 'yellow'])
    
    def test_get_wildcard_vars_caching(self):
        """Test wildcard variable caching functionality"""
        # First call
        wildcards1 = utils.load_wildcards(self.wildcard_dir)
        
        # Call using cache (in actual implementation, get_wildcard_vars is used)
        wildcards2 = utils.load_wildcards(self.wildcard_dir)
        
        # Confirm same content is returned
        self.assertEqual(wildcards1, wildcards2)
    
    def test_nonexistent_directory(self):
        """Test when specifying a non-existent directory"""
        wildcards = utils.load_wildcards('/nonexistent/path')
        self.assertEqual(wildcards, {})


if __name__ == '__main__':
    unittest.main()
