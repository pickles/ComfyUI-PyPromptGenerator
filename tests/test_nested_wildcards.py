"""
Tests for nested wildcard functionality
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.pyprompt_generator.utils import load_wildcards, WildcardManager, _expand_nested_wildcards


@pytest.mark.unit
class TestNestedWildcards:
    """Test nested wildcard expansion functionality"""
    
    def test_basic_nested_wildcard(self):
        """Test basic nested wildcard expansion"""
        # Create a temporary directory for test wildcards
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base wildcard files
            styles_file = Path(temp_dir) / "styles.txt"
            styles_file.write_text("realistic\nanime\npainterly")
            
            colors_file = Path(temp_dir) / "colors.txt"
            colors_file.write_text("red\nblue\ngreen")
            
            # Create a wildcard file with nested references
            combos_file = Path(temp_dir) / "combos.txt"
            combos_file.write_text("{styles} portrait\n{colors} landscape\n{styles} {colors} artwork")
            
            # Load wildcards
            wildcards = load_wildcards(temp_dir)
            
            # Check that all wildcards were loaded
            assert "_styles" in wildcards
            assert "_colors" in wildcards
            assert "_combos" in wildcards
            
            # Check that nested wildcards were expanded
            combos = wildcards["_combos"]
            
            # Each combo should contain one of the possible expansions
            for combo in combos:
                if "portrait" in combo:
                    assert any(style in combo for style in ["realistic", "anime", "painterly"])
                elif "landscape" in combo:
                    assert any(color in combo for color in ["red", "blue", "green"])
                elif "artwork" in combo:
                    # Should contain both style and color
                    has_style = any(style in combo for style in ["realistic", "anime", "painterly"])
                    has_color = any(color in combo for color in ["red", "blue", "green"])
                    assert has_style and has_color
    
    def test_multiple_nested_references(self):
        """Test multiple nested references in one line"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base wildcards
            subjects_file = Path(temp_dir) / "subjects.txt"
            subjects_file.write_text("woman\nman\nchild")
            
            actions_file = Path(temp_dir) / "actions.txt"
            actions_file.write_text("running\nstanding\nsitting")
            
            locations_file = Path(temp_dir) / "locations.txt"
            locations_file.write_text("park\nbeach\nmountain")
            
            # Create wildcard with multiple references
            scenes_file = Path(temp_dir) / "scenes.txt"
            scenes_file.write_text("{subjects} {actions} in {locations}")
            
            wildcards = load_wildcards(temp_dir)
            
            scenes = wildcards["_scenes"]
            
            # Should have one scene that contains all three elements
            assert len(scenes) == 1
            scene = scenes[0]
            
            # Check that it contains elements from all three wildcards
            has_subject = any(subj in scene for subj in ["woman", "man", "child"])
            has_action = any(act in scene for act in ["running", "standing", "sitting"])
            has_location = any(loc in scene for loc in ["park", "beach", "mountain"])
            
            assert has_subject and has_action and has_location
            assert " in " in scene  # Should preserve the structure
    
    def test_nested_wildcard_with_comments(self):
        """Test nested wildcards work with comments and empty lines"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base wildcard with comments
            emotions_file = Path(temp_dir) / "emotions.txt"
            emotions_file.write_text("""# Emotions wildcard
happy
sad

# More emotions
angry
excited
""")
            
            # Create wildcard that references emotions
            expressions_file = Path(temp_dir) / "expressions.txt"
            expressions_file.write_text("""# Expressions using emotions
{emotions} face
{emotions} expression

# Empty line above should be ignored
""")
            
            wildcards = load_wildcards(temp_dir)
            
            # Check emotions loaded correctly (comments and empty lines ignored)
            emotions = wildcards["_emotions"]
            assert "happy" in emotions
            assert "sad" in emotions
            assert "angry" in emotions
            assert "excited" in emotions
            assert len(emotions) == 4  # No comments or empty lines
            
            # Check expressions expanded correctly
            expressions = wildcards["_expressions"]
            assert len(expressions) == 2
            
            for expr in expressions:
                if "face" in expr:
                    assert any(emotion in expr for emotion in emotions)
                elif "expression" in expr:
                    assert any(emotion in expr for emotion in emotions)
    
    def test_invalid_nested_reference(self):
        """Test handling of invalid nested wildcard references"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create wildcard with invalid reference
            invalid_file = Path(temp_dir) / "invalid.txt"
            invalid_file.write_text("valid text\n{nonexistent} reference\n{also_missing}")
            
            wildcards = load_wildcards(temp_dir)
            
            invalid_entries = wildcards["_invalid"]
            
            # Should have 3 entries
            assert len(invalid_entries) == 3
            
            # First entry should be unchanged
            assert "valid text" in invalid_entries
            
            # Invalid references should be left as-is
            invalid_refs = [entry for entry in invalid_entries if "{" in entry]
            assert len(invalid_refs) == 2
            assert any("{nonexistent}" in entry for entry in invalid_refs)
            assert any("{also_missing}" in entry for entry in invalid_refs)
    
    def test_self_reference_prevention(self):
        """Test that self-references are detected and prevented"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create wildcard that tries to reference itself
            recursive_file = Path(temp_dir) / "recursive.txt"
            recursive_file.write_text("normal entry\n{recursive} self-reference\nvalid entry")
            
            wildcards = load_wildcards(temp_dir)
            
            recursive_entries = wildcards["_recursive"]
            
            # Should have 3 entries
            assert len(recursive_entries) == 3
            
            # Self-reference should be left unchanged
            self_ref_entries = [entry for entry in recursive_entries if "{recursive}" in entry]
            assert len(self_ref_entries) == 1
            assert "{recursive} self-reference" in self_ref_entries
    
    def test_nested_wildcard_with_weights(self):
        """Test nested wildcards work with weighted entries"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create weighted wildcard
            rarity_file = Path(temp_dir) / "rarity.txt"
            rarity_file.write_text("10::common\n1::rare\n5::uncommon")
            
            # Create wildcard that references weighted entries
            items_file = Path(temp_dir) / "items.txt"
            items_file.write_text("{rarity} sword\n{rarity} shield")
            
            wildcards = load_wildcards(temp_dir)
            
            # Check rarity loaded with weights
            rarity = wildcards["_rarity"]
            assert "10::common" in rarity
            assert "1::rare" in rarity
            assert "5::uncommon" in rarity
            
            # Check items expanded (should expand the weighted choice)
            items = wildcards["_items"]
            assert len(items) == 2
            
            # Items should contain the choice results (weights will be processed by choice function)
            sword_item = next(item for item in items if "sword" in item)
            shield_item = next(item for item in items if "shield" in item)
            
            # Should contain one of the rarity types (without weight prefix after expansion)
            rarity_types = ["common", "rare", "uncommon"]
            assert any(rarity_type in sword_item for rarity_type in rarity_types)
            assert any(rarity_type in shield_item for rarity_type in rarity_types)
    
    def test_nested_wildcard_manager(self):
        """Test that WildcardManager also supports nested wildcards"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            base_file = Path(temp_dir) / "base.txt"
            base_file.write_text("alpha\nbeta\ngamma")
            
            nested_file = Path(temp_dir) / "nested.txt"
            nested_file.write_text("{base} version\nstandalone")
            
            # Use WildcardManager
            manager = WildcardManager(temp_dir)
            wildcards = manager.get_wildcard_vars()
            
            # Check expansion worked
            assert "_base" in wildcards
            assert "_nested" in wildcards
            
            nested_entries = wildcards["_nested"]
            assert len(nested_entries) == 2
            
            # One entry should be expanded, one should be standalone
            expanded_entry = next(entry for entry in nested_entries if "version" in entry)
            standalone_entry = next(entry for entry in nested_entries if entry == "standalone")
            
            assert any(base in expanded_entry for base in ["alpha", "beta", "gamma"])
            assert standalone_entry == "standalone"
    
    def test_expand_nested_wildcards_function(self):
        """Test the _expand_nested_wildcards function directly"""
        # Create test wildcard dictionary
        test_wildcards = {
            "_colors": ["red", "blue", "green"],
            "_shapes": ["circle", "square", "triangle"],
            "_combos": ["{colors} {shapes}", "plain shape", "{colors} item"]
        }
        
        # Expand nested wildcards
        _expand_nested_wildcards(test_wildcards)
        
        # Check expansion
        combos = test_wildcards["_combos"]
        assert len(combos) == 3
        
        # First combo should have both color and shape
        color_shape_combo = combos[0]
        has_color = any(color in color_shape_combo for color in ["red", "blue", "green"])
        has_shape = any(shape in color_shape_combo for shape in ["circle", "square", "triangle"])
        assert has_color and has_shape
        
        # Second combo should be unchanged
        assert "plain shape" in combos
        
        # Third combo should have color but no shape
        color_item_combo = next(combo for combo in combos if "item" in combo)
        has_color_in_item = any(color in color_item_combo for color in ["red", "blue", "green"])
        assert has_color_in_item
    
    def test_complex_nested_scenario(self):
        """Test a complex scenario with multiple levels and cross-references"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a complex hierarchy
            base_file = Path(temp_dir) / "adjectives.txt"
            base_file.write_text("beautiful\nmajestic\nmysterious")
            
            subjects_file = Path(temp_dir) / "subjects.txt"
            subjects_file.write_text("dragon\ncastle\nforest")
            
            styles_file = Path(temp_dir) / "styles.txt"
            styles_file.write_text("fantasy\nrealistic\nabstract")
            
            # Intermediate level
            descriptions_file = Path(temp_dir) / "descriptions.txt"
            descriptions_file.write_text("{adjectives} {subjects}\n{styles} artwork")
            
            # Top level
            prompts_file = Path(temp_dir) / "prompts.txt"
            prompts_file.write_text("{descriptions}, masterpiece\n{styles} {adjectives} scene")
            
            wildcards = load_wildcards(temp_dir)
            
            # Check all levels loaded
            assert "_adjectives" in wildcards
            assert "_subjects" in wildcards
            assert "_styles" in wildcards
            assert "_descriptions" in wildcards
            assert "_prompts" in wildcards
            
            # Check expansions at each level
            descriptions = wildcards["_descriptions"]
            assert len(descriptions) == 2
            
            prompts = wildcards["_prompts"]
            assert len(prompts) == 2
            
            # Each prompt should contain elements from the hierarchy
            for prompt in prompts:
                if "masterpiece" in prompt:
                    # Should contain description elements
                    has_adj_or_style = any(word in prompt for word in 
                                         ["beautiful", "majestic", "mysterious", "fantasy", "realistic", "abstract"])
                    assert has_adj_or_style
                elif "scene" in prompt:
                    # Should contain style and adjective
                    has_style = any(style in prompt for style in ["fantasy", "realistic", "abstract"])
                    has_adj = any(adj in prompt for adj in ["beautiful", "majestic", "mysterious"])
                    assert has_style and has_adj
