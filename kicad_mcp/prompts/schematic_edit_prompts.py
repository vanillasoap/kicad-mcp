"""
Prompt templates for schematic editing workflows.
"""

from mcp.server.fastmcp import FastMCP


def register_schematic_edit_prompts(mcp: FastMCP) -> None:
    """Register schematic editing prompt templates with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.prompt()
    def schematic_component_analysis(schematic_path: str) -> str:
        """Analyze and report on components in a schematic file.

        This prompt helps you analyze the components in a KiCad schematic file.
        It will load the schematic, search for components, and provide insights
        about the circuit design.

        Args:
            schematic_path: Path to the .kicad_sch schematic file
        """
        return f"""You are helping analyze a KiCad schematic file. Please follow these steps:

1. First, load the schematic file: {schematic_path}
   Use the `load_schematic` tool to get basic information about the schematic.

2. Search for different types of components:
   - Search for all resistors: use `search_components` with search_type="reference" and search_value="R*"
   - Search for all capacitors: use `search_components` with search_type="reference" and search_value="C*"
   - Search for all integrated circuits: use `search_components` with search_type="reference" and search_value="U*"
   - Search for power components: use `search_components` with search_type="reference" and search_value="VCC" or "GND"

3. Analyze the results and provide insights about:
   - Total component count and types
   - Circuit complexity (based on component diversity)
   - Potential circuit patterns or functions
   - Any obvious design issues or recommendations

4. Summarize your findings in a clear, structured report.

Focus on providing actionable insights that would help someone understand or improve the schematic design."""

    @mcp.prompt()
    def schematic_modification_workflow(schematic_path: str, modification_type: str) -> str:
        """Guide through common schematic modification workflows.

        This prompt provides step-by-step guidance for modifying KiCad schematics
        safely and effectively.

        Args:
            schematic_path: Path to the .kicad_sch schematic file
            modification_type: Type of modification (component_property, add_connection, move_component, clone_component)
        """
        base_guidance = f"""You are helping modify a KiCad schematic file: {schematic_path}

IMPORTANT SAFETY NOTES:
- Always create backups before making changes (set create_backup=True)
- Test changes incrementally
- Validate the schematic in KiCad after modifications

"""

        if modification_type == "component_property":
            return (
                base_guidance
                + """COMPONENT PROPERTY MODIFICATION WORKFLOW:

1. First, load the schematic to understand its structure:
   Use `load_schematic` tool to get an overview of components.

2. Find the specific component to modify:
   Use `search_components` to locate the component by reference, value, or pattern.

3. Modify the component property:
   Use `modify_component_property` with the correct:
   - component_reference (e.g., "R1", "C5")
   - property_name (e.g., "Value", "MPN", "Footprint")
   - new_value
   - create_backup=True

4. Verify the change was successful by searching for the component again.

Common properties you can modify:
- Value: Component value (e.g., "10k", "100nF")
- MPN: Manufacturer part number
- Footprint: Physical footprint reference
- Datasheet: Link to component datasheet

Proceed with your specific modification needs."""
            )

        elif modification_type == "add_connection":
            return (
                base_guidance
                + """WIRE CONNECTION WORKFLOW:

1. Load the schematic and identify components:
   Use `load_schematic` and `search_components` to find the components you want to connect.

2. Identify the pin numbers/names on each component:
   Review the component information to understand available pins.

3. Create the wire connection:
   Use `add_wire_connection` with:
   - from_component: Reference of source component (e.g., "R1")
   - from_pin: Pin identifier (e.g., "1", "A", "VCC")
   - to_component: Reference of target component (e.g., "C1")
   - to_pin: Pin identifier (e.g., "2", "K", "GND")
   - create_backup=True

4. Verify the connection in KiCad after the modification.

NOTE: Pin names/numbers vary by component type and library. Common pins:
- Resistors/Capacitors: "1", "2"
- LEDs: "A" (anode), "K" (cathode)
- ICs: Check datasheet or symbol for pin numbers

Proceed with creating your specific connection."""
            )

        elif modification_type == "move_component":
            return (
                base_guidance
                + """COMPONENT MOVEMENT WORKFLOW:

1. Load the schematic and locate the component:
   Use `load_schematic` and `search_components` to find the component to move.

2. Plan the movement:
   - Consider the current position and desired new position
   - Ensure the new position won't cause overlaps
   - Think about wire routing implications

3. Move the component:
   Use `move_component` with:
   - component_reference: Component to move (e.g., "R1")
   - x_offset: Horizontal movement in mm (positive = right, negative = left)
   - y_offset: Vertical movement in mm (positive = up, negative = down)
   - create_backup=True

4. Check the result and adjust wire connections if needed.

Typical movement distances:
- Small adjustments: 2-5mm
- Component spacing: 10-20mm
- Major repositioning: 25-50mm

Proceed with moving your component."""
            )

        elif modification_type == "clone_component":
            return (
                base_guidance
                + """COMPONENT CLONING WORKFLOW:

1. Load the schematic and identify the component to clone:
   Use `load_schematic` and `search_components` to find the source component.

2. Plan the clone:
   - Choose a unique reference for the new component
   - Determine appropriate positioning offset
   - Consider circuit implications of the duplicate

3. Clone the component:
   Use `clone_component` with:
   - source_reference: Component to clone (e.g., "R1")
   - new_reference: New component reference (e.g., "R2")
   - x_offset: Horizontal offset in mm (default: 10.0)
   - y_offset: Vertical offset in mm (default: 0.0)
   - create_backup=True

4. After cloning, you may want to:
   - Modify properties of the new component if needed
   - Add wire connections to integrate it into the circuit
   - Update the reference designator sequence

Proceed with cloning your component."""
            )

        else:
            return (
                base_guidance
                + """Please specify a valid modification_type:
- component_property: Modify component properties like value, footprint, etc.
- add_connection: Create wire connections between components
- move_component: Reposition components in the schematic
- clone_component: Duplicate existing components

Choose one of these types and I'll provide specific guidance."""
            )

    @mcp.prompt()
    def schematic_troubleshooting() -> str:
        """Help troubleshoot common schematic editing issues."""
        return """SCHEMATIC EDITING TROUBLESHOOTING GUIDE:

COMMON ISSUES AND SOLUTIONS:

1. "kicad-skip library not installed" Error:
   - Install with: pip install kicad-skip
   - Ensure you're in the correct virtual environment
   - Verify installation with: python -c "import skip; print('OK')"

2. "Component not found" Error:
   - Use `search_components` to find the correct component reference
   - Check for typos in component references (case-sensitive)
   - Verify the component exists in the loaded schematic

3. "Property not found" Error:
   - Not all components have all properties
   - Use `search_components` to examine existing component properties
   - Common properties: Value, MPN, Footprint, Datasheet

4. "Failed to connect pins" Error:
   - Verify both components exist using `search_components`
   - Check pin names/numbers match the component symbol
   - Some components may have different pin naming conventions

5. File Access Issues:
   - Ensure the schematic file path is correct and accessible
   - Check file permissions (read/write access required)
   - Close KiCad if it has the file open (may cause conflicts)

6. Backup Creation Failed:
   - Verify write permissions in the schematic directory
   - Check available disk space
   - Ensure the backup directory path is valid

BEST PRACTICES:

- Always create backups before modifications (create_backup=True)
- Start with simple modifications to test the workflow
- Use `load_schematic` first to understand the schematic structure
- Search for components before trying to modify them
- Open modified schematics in KiCad to verify changes
- Keep original files safe and test on copies when learning

DEBUGGING STEPS:

1. Load the schematic with `load_schematic` to verify it's readable
2. Use `search_components` to explore available components
3. Start with simple property modifications before complex operations
4. Check error messages carefully - they often indicate the specific issue

If you encounter specific errors, provide the exact error message and the operation you were attempting for more targeted help."""
