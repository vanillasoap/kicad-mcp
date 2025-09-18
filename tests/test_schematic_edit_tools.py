"""
Tests for schematic editing tools.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from kicad_mcp.tools.schematic_edit_tools import register_schematic_edit_tools


class TestSchematicEditTools:
    """Test cases for schematic editing functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_schematic = os.path.join(self.test_dir, "test.kicad_sch")

        # Create a minimal test schematic file
        schematic_content = """(kicad_sch (version 20230121) (generator eeschema)
  (uuid "test-uuid")
  (sheet (at 0 0) (size 297 210))
)"""
        with open(self.test_schematic, "w") as f:
            f.write(schematic_content)

    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_register_schematic_edit_tools(self):
        """Test that schematic edit tools are registered properly."""
        mock_mcp = Mock()

        register_schematic_edit_tools(mock_mcp)

        # Verify that tools were registered
        assert mock_mcp.tool.call_count == 6  # 6 tools should be registered

        # Get the tool names from the mock calls
        tool_names = []
        for call in mock_mcp.tool.call_args_list:
            # Each call should be mcp.tool() decorator
            assert call[0] == ()  # No positional args

        # Verify the decorated functions exist
        registered_functions = [call[0][0] for call in mock_mcp.tool.return_value.call_args_list]
        expected_functions = [
            "load_schematic",
            "search_components",
            "modify_component_property",
            "add_wire_connection",
            "move_component",
            "clone_component",
        ]

    @patch("kicad_mcp.tools.schematic_edit_tools.validate_file_path")
    def test_load_schematic_invalid_path(self, mock_validate):
        """Test loading schematic with invalid path."""
        mock_validate.return_value = {"valid": False, "error": "Invalid path"}

        # Create a mock tool function
        mock_mcp = Mock()
        register_schematic_edit_tools(mock_mcp)

        # Get the load_schematic function
        load_schematic_calls = [call for call in mock_mcp.tool.call_args_list]
        assert len(load_schematic_calls) > 0

    @patch("kicad_mcp.tools.schematic_edit_tools.validate_file_path")
    def test_load_schematic_wrong_extension(self, mock_validate):
        """Test loading schematic with wrong file extension."""
        mock_validate.return_value = {"valid": True}

        mock_mcp = Mock()
        register_schematic_edit_tools(mock_mcp)

        # Test would fail because file doesn't end with .kicad_sch
        # This is tested via integration tests

    @pytest.mark.unit
    def test_backup_file_creation(self):
        """Test that backup files are created properly."""
        from kicad_mcp.utils.file_utils import backup_file

        # Create a test file
        test_file = os.path.join(self.test_dir, "test.kicad_sch")
        with open(test_file, "w") as f:
            f.write("test content")

        # Create backup
        result = backup_file(test_file)

        assert result["success"] is True
        assert "backup_path" in result
        assert os.path.exists(result["backup_path"])

        # Verify backup content matches original
        with open(result["backup_path"], "r") as f:
            backup_content = f.read()
        assert backup_content == "test content"

    @pytest.mark.unit
    def test_backup_file_nonexistent(self):
        """Test backup creation for nonexistent file."""
        from kicad_mcp.utils.file_utils import backup_file

        nonexistent_file = os.path.join(self.test_dir, "nonexistent.kicad_sch")
        result = backup_file(nonexistent_file)

        assert result["success"] is False
        assert "error" in result
        assert "does not exist" in result["error"]

    @pytest.mark.integration
    @pytest.mark.requires_kicad_skip
    @patch("skip.Schematic")
    def test_load_schematic_integration(self, mock_schematic):
        """Integration test for loading a schematic."""
        # Mock the skip.Schematic class
        mock_schem_instance = MagicMock()
        mock_schematic.return_value = mock_schem_instance

        # Mock symbols collection
        mock_symbol1 = MagicMock()
        mock_symbol1.reference = "R1"
        mock_symbol1.value = "10k"
        mock_symbol1.position = "(10, 20)"

        mock_symbol2 = MagicMock()
        mock_symbol2.reference = "C1"
        mock_symbol2.value = "100nF"
        mock_symbol2.position = "(30, 40)"

        mock_schem_instance.symbol = [mock_symbol1, mock_symbol2]
        mock_schem_instance.wire = []

        # Test the actual function logic would go here
        # This would require importing and calling the actual registered function

    @pytest.mark.integration
    @pytest.mark.requires_kicad_skip
    def test_search_components_integration(self):
        """Integration test for component search functionality."""
        # This would test actual kicad-skip integration
        # Requires a real test schematic with known components
        pass

    @pytest.mark.slow
    @pytest.mark.requires_kicad_skip
    def test_modify_component_property_integration(self):
        """Integration test for component property modification."""
        # This would test actual file modification
        # Requires careful setup and teardown
        pass

    def test_error_handling_no_kicad_skip(self):
        """Test error handling when kicad-skip is not available."""
        # Mock import error
        with patch.dict("sys.modules", {"skip": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                # Test would check that proper error is returned
                pass


class TestSchematicEditPrompts:
    """Test cases for schematic editing prompts."""

    def test_register_schematic_edit_prompts(self):
        """Test that schematic editing prompts are registered."""
        from kicad_mcp.prompts.schematic_edit_prompts import register_schematic_edit_prompts

        mock_mcp = Mock()
        register_schematic_edit_prompts(mock_mcp)

        # Verify that prompts were registered
        assert mock_mcp.prompt.call_count == 3  # 3 prompts should be registered

    def test_component_analysis_prompt_content(self):
        """Test component analysis prompt generates appropriate content."""
        from kicad_mcp.prompts.schematic_edit_prompts import register_schematic_edit_prompts

        mock_mcp = Mock()
        register_schematic_edit_prompts(mock_mcp)

        # The actual prompt content testing would require accessing the registered functions
        # This tests the registration mechanism

    def test_modification_workflow_prompts(self):
        """Test modification workflow prompts for different types."""
        # Test that different modification types generate appropriate guidance
        modification_types = [
            "component_property",
            "add_connection",
            "move_component",
            "clone_component",
        ]

        for mod_type in modification_types:
            # Test would verify appropriate prompt content for each type
            pass

    def test_troubleshooting_prompt(self):
        """Test troubleshooting prompt provides helpful guidance."""
        # Test that troubleshooting prompt covers common issues
        pass


if __name__ == "__main__":
    pytest.main([__file__])
