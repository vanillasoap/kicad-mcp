#!/usr/bin/env python3
"""
Test script for wire connection functionality
"""

import skip
import tempfile
import shutil
import os

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def find_component_by_reference(schem, component_reference: str):
    """Find component by reference with fallback methods."""
    component = getattr(schem.symbol, component_reference, None)

    # Get available references for debugging
    available_refs = [attr for attr in dir(schem.symbol) if not attr.startswith('_')]

    return component, available_refs

def get_component_pins(component):
    """Extract pin information from component."""
    pins_info = []
    for pin in component.pin:
        pin_info = {
            "number": str(pin[0]) if len(pin) > 0 else "Unknown",
            "uuid": safe_serialize(getattr(pin, "uuid", None))
        }
        pins_info.append(pin_info)
    return {"pin_count": len(pins_info), "pins": pins_info}

def add_wire_connection(schematic_path, from_component, from_pin, to_component, to_pin, create_backup=True):
    """Add a wire connection between two component pins."""

    try:
        # Create backup if needed
        backup_path = None
        if create_backup:
            backup_path = f"{schematic_path}.backup"
            shutil.copy2(schematic_path, backup_path)

        # Load schematic
        schem = skip.Schematic(schematic_path)

        # Find components
        from_comp, available_refs = find_component_by_reference(schem, from_component)
        to_comp, _ = find_component_by_reference(schem, to_component)

        if not from_comp:
            return {
                "error": f"Source component {from_component} not found",
                "available_references": available_refs
            }
        if not to_comp:
            return {
                "error": f"Target component {to_component} not found",
                "available_references": available_refs
            }

        # Get pin information
        from_pins_info = get_component_pins(from_comp)
        to_pins_info = get_component_pins(to_comp)

        # Verify pins exist
        from_pin_found = any(pin["number"] == from_pin for pin in from_pins_info["pins"])
        to_pin_found = any(pin["number"] == to_pin for pin in to_pins_info["pins"])

        if not from_pin_found:
            available_pins = [pin["number"] for pin in from_pins_info["pins"]]
            return {
                "error": f"Pin '{from_pin}' not found on component {from_component}",
                "available_pins": available_pins,
                "component": from_component,
                "lib_id": safe_serialize(getattr(from_comp, "lib_id", None))
            }

        if not to_pin_found:
            available_pins = [pin["number"] for pin in to_pins_info["pins"]]
            return {
                "error": f"Pin '{to_pin}' not found on component {to_component}",
                "available_pins": available_pins,
                "component": to_component,
                "lib_id": safe_serialize(getattr(to_comp, "lib_id", None))
            }

        # Get component positions
        from_pos = from_comp.at
        to_pos = to_comp.at

        # Check positions without triggering boolean evaluation
        try:
            from_coords = [float(from_pos[0]), float(from_pos[1])]
            to_coords = [float(to_pos[0]), float(to_pos[1])]
        except Exception as pos_error:
            return {
                "error": f"Could not extract coordinates: {str(pos_error)}",
                "from_position": safe_serialize(from_pos),
                "to_position": safe_serialize(to_pos)
            }

        # Create wire using coordinate-based connection
        new_wire = schem.wire.new()
        new_wire.start_at(from_coords)
        new_wire.end_at(to_coords)

        # Save schematic
        schem.overwrite()

        return {
            "status": "connected",
            "from": f"{from_component}.{from_pin}",
            "to": f"{to_component}.{to_pin}",
            "from_coordinates": from_coords,
            "to_coordinates": to_coords,
            "backup_created": backup_path is not None,
            "backup_path": backup_path,
            "method": "coordinate_based_wire",
            "note": "Connected to component centers. Pin-specific offsets not yet implemented."
        }

    except Exception as e:
        return {
            "error": f"Failed to connect pins: {str(e)}",
            "error_type": type(e).__name__
        }

def test_wire_connections():
    """Test various wire connection scenarios."""
    print("=== Wire Connection Tests ===\n")

    # Test 1: R_SCL to U1
    print("Test 1: Connect R_SCL pin 1 to U1 pin 1")
    result1 = add_wire_connection(
        'test_wiring.kicad_sch',
        'R_SCL', '1',
        'U1', '1',
        create_backup=False  # We already have a wire from previous test
    )
    print("Result:", result1)
    print()

    # Test 2: R_PDN to U1
    print("Test 2: Connect R_PDN pin 2 to U1 pin 2")
    result2 = add_wire_connection(
        'test_wiring.kicad_sch',
        'R_PDN', '2',
        'U1', '2',
        create_backup=False
    )
    print("Result:", result2)
    print()

    # Test 3: Invalid pin test
    print("Test 3: Try to connect to invalid pin")
    result3 = add_wire_connection(
        'test_wiring.kicad_sch',
        'R_SCL', '99',
        'U1', '1',
        create_backup=False
    )
    print("Result:", result3)
    print()

    return [result1, result2, result3]

if __name__ == "__main__":
    results = test_wire_connections()

    # Summary
    success_count = sum(1 for r in results if r.get("status") == "connected")
    print(f"\\n=== Summary ===")
    print(f"Successful connections: {success_count}/{len(results)}")

    # Verify final state
    try:
        schem = skip.Schematic('test_wiring.kicad_sch')
        print(f"Total wires in schematic: {len(schem.wire)}")
    except Exception as e:
        print(f"Error reading final state: {e}")