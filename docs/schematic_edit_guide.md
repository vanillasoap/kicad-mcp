# Schematic Editing Guide

The KiCad MCP Server provides powerful schematic editing capabilities through integration with the [KiCAD Skip](https://github.com/KiCADNexus/kicad-skip) library. This allows AI assistants to programmatically modify KiCad schematic files directly.

## Overview

The schematic editing feature enables:

- **Component Property Modification**: Change values, part numbers, footprints, and other component properties
- **Component Search**: Find components by reference, value, regex patterns, or position
- **Wire Connections**: Create wire connections between component pins
- **Component Movement**: Reposition components within the schematic
- **Component Cloning**: Duplicate existing components with new references
- **Safe Backup Creation**: Automatic backup creation before modifications

## Available Tools

### `load_schematic`
Load a KiCad schematic file for editing and get basic information about its contents.

**Usage:**
```python
load_schematic(schematic_path="/path/to/my_project.kicad_sch")
```

**Returns:**
- Component count and preview
- Wire count
- Available operations
- Loading status

### `search_components`
Search for components in the schematic using various criteria.

**Usage:**
```python
# Search by reference prefix
search_components(schematic_path="...", search_type="reference", search_value="R*")

# Search by exact reference
search_components(schematic_path="...", search_type="reference", search_value="R1")

# Search by regex pattern
search_components(schematic_path="...", search_type="regex", search_value=r"R\d+")

# Search by value
search_components(schematic_path="...", search_type="value", search_value="10k")
```

### `modify_component_property`
Modify properties of existing components.

**Usage:**
```python
modify_component_property(
    schematic_path="...",
    component_reference="R1",
    property_name="Value",
    new_value="22k",
    create_backup=True
)
```

**Common Properties:**
- `Value`: Component value (e.g., "10k", "100nF")
- `MPN`: Manufacturer part number
- `Footprint`: Physical footprint reference
- `Datasheet`: Link to component datasheet

### `get_component_pin_info`
Discover available pins on a component.

**Usage:**
```python
get_component_pin_info(
    schematic_path="...",
    component_reference="R1"
)
```

**Returns:**
- Pin count and detailed pin information
- Pin numbers and UUIDs
- Helpful for identifying available pins before creating connections

### `add_wire_connection`
Create wire connections between component pins.

**Usage:**
```python
add_wire_connection(
    schematic_path="...",
    from_component="R1",
    from_pin="2",
    to_component="C1",
    to_pin="1",
    create_backup=True
)
```

**Pin Naming Conventions:**
- Resistors/Capacitors: "1", "2"
- LEDs: "A" (anode), "K" (cathode)
- ICs: Numbered pins "1", "2", "3", etc. (check datasheet/symbol)
- **Note**: Use `get_component_pin_info` to discover available pins before creating connections

**Current Implementation:**
- Connects wires to component centers (not exact pin positions)
- Validates pin existence before creating connections
- Provides helpful error messages with available pins if pin not found

### `move_component`
Move components by specified offsets.

**Usage:**
```python
move_component(
    schematic_path="...",
    component_reference="R1",
    x_offset=10.0,  # mm, positive = right
    y_offset=-5.0,  # mm, positive = up
    create_backup=True
)
```

### `clone_component`
Duplicate components with new references.

**Usage:**
```python
clone_component(
    schematic_path="...",
    source_reference="R1",
    new_reference="R2",
    x_offset=15.0,
    y_offset=0.0,
    create_backup=True
)
```

## Prompt Templates

The server includes several prompt templates to guide schematic editing workflows:

### `schematic_component_analysis`
Provides step-by-step guidance for analyzing components in a schematic file.

### `schematic_modification_workflow`
Offers workflow guidance for different types of modifications:
- `component_property`: Property modification workflows
- `add_connection`: Wire connection workflows
- `move_component`: Component movement workflows
- `clone_component`: Component cloning workflows

### `schematic_troubleshooting`
Comprehensive troubleshooting guide for common issues.

## Example Workflows

### Basic Component Analysis
```python
# 1. Load the schematic
result = load_schematic("/path/to/project.kicad_sch")

# 2. Search for all resistors
resistors = search_components(
    schematic_path="/path/to/project.kicad_sch",
    search_type="reference",
    search_value="R*"
)

# 3. Examine results
print(f"Found {resistors['matches_count']} resistors")
for resistor in resistors['matches']:
    print(f"- {resistor['reference']}: {resistor['value']}")
```

### Modify Component Values
```python
# Change resistor value
modify_component_property(
    schematic_path="/path/to/project.kicad_sch",
    component_reference="R1",
    property_name="Value",
    new_value="47k"
)

# Update part numbers for multiple components
components = ["R1", "R2", "R3"]
for comp in components:
    modify_component_property(
        schematic_path="/path/to/project.kicad_sch",
        component_reference=comp,
        property_name="MPN",
        new_value="RC0805FR-0747KL"
    )
```

### Create Circuit Connections
```python
# Step 1: Discover available pins first
pin_info_r1 = get_component_pin_info(
    schematic_path="/path/to/project.kicad_sch",
    component_reference="R1"
)
print(f"R1 has pins: {[pin['number'] for pin in pin_info_r1['pins']]}")

pin_info_c1 = get_component_pin_info(
    schematic_path="/path/to/project.kicad_sch",
    component_reference="C1"
)
print(f"C1 has pins: {[pin['number'] for pin in pin_info_c1['pins']]}")

# Step 2: Connect resistor to capacitor
connection_result = add_wire_connection(
    schematic_path="/path/to/project.kicad_sch",
    from_component="R1",
    from_pin="2",
    to_component="C1",
    to_pin="1"
)

if connection_result.get("status") == "connected":
    print(f"Successfully connected {connection_result['from']} to {connection_result['to']}")
else:
    print(f"Connection failed: {connection_result.get('error')}")
    if 'available_pins' in connection_result:
        print(f"Available pins: {connection_result['available_pins']}")

# Step 3: Connect multiple components in series
connections = [
    ("U1", "1", "R1", "1"),
    ("R1", "2", "C1", "1"),
    ("C1", "2", "GND", "1")  # Note: GND component must exist in schematic
]

for from_comp, from_pin, to_comp, to_pin in connections:
    result = add_wire_connection(
        schematic_path="/path/to/project.kicad_sch",
        from_component=from_comp,
        from_pin=from_pin,
        to_component=to_comp,
        to_pin=to_pin
    )

    if result.get("status") == "connected":
        print(f"✅ Connected {from_comp}.{from_pin} to {to_comp}.{to_pin}")
    else:
        print(f"❌ Failed: {result.get('error')}")
```

### Component Layout Management
```python
# Move component to new position
move_component(
    schematic_path="/path/to/project.kicad_sch",
    component_reference="R1",
    x_offset=20.0,  # Move 20mm right
    y_offset=10.0   # Move 10mm up
)

# Clone component for parallel connection
clone_component(
    schematic_path="/path/to/project.kicad_sch",
    source_reference="C1",
    new_reference="C2",
    x_offset=0.0,
    y_offset=15.0   # Place below original
)
```

## Best Practices

### Safety First
- **Always create backups**: Set `create_backup=True` (default)
- **Test on copies**: Work on project copies during development
- **Incremental changes**: Make small changes and test each step
- **Validate in KiCad**: Open modified files in KiCad to verify changes

### Workflow Efficiency
1. **Load first**: Use `load_schematic` to understand the project structure
2. **Search before modify**: Use `search_components` to find exact references
3. **Batch operations**: Group related modifications together
4. **Document changes**: Keep track of modifications made

### Error Prevention
- **Check component existence**: Search for components before modifying
- **Verify pin names**: Pin naming varies by component and library
- **Use absolute paths**: Avoid relative paths in schematic_path parameters
- **Handle errors gracefully**: Check return status of all operations

## Current Status & Limitations

### ✅ **Fully Working Functions:**

- **`load_schematic`** - Loads and analyzes schematic files ✅
- **`search_components`** - All search types working (reference, value, regex) ✅
- **`get_component_pin_info`** - Enumerates available pins on components ✅
- **`modify_component_property`** - Changes component properties and saves ✅
- **`add_wire_connection`** - Creates wire connections between component pins ✅
- **`clone_component`** - Duplicates components with custom reference names ✅
- **Automatic backup creation** - Creates timestamped backups before edits ✅

### ⚠️ **Partially Working Functions:**

- **`move_component`** - Component movement works, coordinate system needs verification

### 📋 **Known Limitations:**

1. **Pin Positioning**: Wires connect to component centers, not exact pin positions
2. **Coordinate System**: Position units and coordinate transformations need validation
3. **Complex Components**: Multi-unit components may require special handling
4. **Undo Functionality**: No built-in undo - relies on automatic backups

## Troubleshooting

### Common Issues

**"kicad-skip library not installed"**
```bash
pip install kicad-skip
```

**"Component not found"** - FIXED ✅
- The system now provides detailed debugging information
- Shows all available component references when component not found
- Uses fallback search methods (direct access + iteration)

**"'Schematic' object has no attribute 'save'"** - FIXED ✅
- Now uses correct `schematic.overwrite()` API method
- Proper file saving and backup creation implemented

**"Unable to serialize unknown type"** - FIXED ✅
- All KiCAD Skip objects now properly serialized to JSON
- Safe conversion of complex objects to strings

**Property modification issues** - FIXED ✅
- Proper property access using KiCAD Skip API
- Detailed error reporting for debugging

**Component cloning reference names** - FIXED ✅
- Clone components now use the exact reference name specified
- No more auto-generated names like "R1_" or "RCC1_"
- Supports all reference naming patterns (R10, R_CUSTOM, etc.)

### Current Working Workflow

1. **Analysis**: ✅ Use `load_schematic` and `search_components`
2. **Pin Discovery**: ✅ Use `get_component_pin_info` to identify available pins
3. **Property Editing**: ✅ Use `modify_component_property`
4. **Wire Connections**: ✅ Use `add_wire_connection` to connect components
5. **Component Duplication**: ✅ Use `clone_component`
6. **File Management**: ✅ Automatic backups created
7. **Verification**: ✅ Reload schematic to verify changes

### Getting Help

Use the `schematic_troubleshooting` prompt template for comprehensive troubleshooting guidance:

```python
# Access troubleshooting prompt
prompt_result = mcp.get_prompt("schematic_troubleshooting")
```

## Integration Notes

### Dependencies
- **kicad-skip >= 0.2.5**: Core schematic editing library
- **sexpdata >= 0.0.3**: S-expression parsing (kicad-skip dependency)

### File Format Support
- **Input**: `.kicad_sch` KiCad schematic files
- **Backup**: Automatic timestamped backups created
- **Compatibility**: Works with KiCad 6.0+ schematic format

### Performance Considerations
- **File size**: Large schematics may take longer to process
- **Backup creation**: Adds small overhead but essential for safety
- **Memory usage**: Entire schematic loaded into memory during editing

### Platform Support
- **Cross-platform**: Works on macOS, Windows, and Linux
- **KiCad versions**: Compatible with KiCad 6.0+ file formats
- **Python requirement**: Python 3.10+ required

## Advanced Usage

### Custom Validation
```python
# Verify changes before saving
def validate_modification(schematic_path, component_ref):
    # Load and check component exists
    result = search_components(
        schematic_path=schematic_path,
        search_type="reference",
        search_value=component_ref
    )
    return result['matches_count'] > 0

# Use validation in workflow
if validate_modification("/path/to/project.kicad_sch", "R1"):
    modify_component_property(...)
```

### Batch Processing
```python
# Process multiple schematics
import os
from pathlib import Path

def process_project_schematics(project_dir):
    schematic_files = Path(project_dir).glob("*.kicad_sch")

    for sch_file in schematic_files:
        print(f"Processing: {sch_file}")
        result = load_schematic(str(sch_file))

        if result.get('status') == 'loaded':
            # Perform modifications
            pass
```

### Integration with Other Tools
```python
# Combine with project analysis
projects = list_projects()
for project in projects:
    project_files = get_project_structure(project['path'])

    if 'schematic' in project_files['files']:
        sch_path = project_files['files']['schematic']
        result = load_schematic(sch_path)
        # Analyze and modify as needed
```

This comprehensive editing capability enables sophisticated schematic modifications through natural language interaction with AI assistants, making KiCad project manipulation more accessible and efficient.