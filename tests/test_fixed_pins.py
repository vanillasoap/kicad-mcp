#!/usr/bin/env python3
"""
Test script for the fixed pin discovery and wire connection
"""

import skip
import logging

def safe_serialize(obj) -> str:
    """Safely serialize any object to string."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        return "Unknown"

def get_component_pins(component):
    """Get all available pins for a component (FIXED VERSION)."""
    pins_info = []
    try:
        if hasattr(component, 'pin'):
            for pin in component.pin:
                try:
                    # Pin objects are indexable but don't have len(), just access pin[0] directly
                    pin_number = str(pin[0]) if pin[0] is not None else "Unknown"
                    pin_info = {
                        "number": pin_number,
                        "uuid": safe_serialize(getattr(pin, "uuid", None))
                    }
                except (IndexError, TypeError):
                    # If pin[0] fails, try to extract from raw data or skip
                    pin_info = {
                        "number": "Unknown",
                        "uuid": safe_serialize(getattr(pin, "uuid", None))
                    }
                pins_info.append(pin_info)
    except Exception as e:
        logging.warning(f"Could not enumerate pins: {e}")

    return {
        "pin_count": len(pins_info),
        "pins": pins_info
    }

def find_component_by_reference(schem, component_reference: str):
    """Find component by reference with fallback methods."""
    component = getattr(schem.symbol, component_reference, None)

    # Get available references for debugging
    available_refs = [attr for attr in dir(schem.symbol) if not attr.startswith('_')]

    return component, available_refs

def add_wire_connection_fixed(schematic_path, from_component, from_pin, to_component, to_pin):
    """Add a wire connection between two component pins (FIXED VERSION)."""

    try:
        # Load schematic
        print("Loading schematic...")
        schem = skip.Schematic(schematic_path)
        print("Schematic loaded successfully")

        # Find components
        print("Finding components...")
        from_comp, available_refs = find_component_by_reference(schem, from_component)
        to_comp, _ = find_component_by_reference(schem, to_component)
        print(f"Components found: {from_comp is not None}, {to_comp is not None}")

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

        print(f"From component {from_component} pins: {[p['number'] for p in from_pins_info['pins']]}")
        print(f"To component {to_component} pins: {[p['number'] for p in to_pins_info['pins']]}")

        # Find the requested pins (FIXED VERSION)
        print("Searching for specific pins...")
        from_pin_obj = None
        to_pin_obj = None

        # Search for from_pin
        print(f"Searching for pin {from_pin} on {from_component}...")
        for pin in from_comp.pin:
            try:
                pin_number = str(pin[0]) if pin[0] is not None else ""
                if pin_number == from_pin:
                    from_pin_obj = pin
                    print(f"Found pin {from_pin}!")
                    break
            except (IndexError, TypeError) as e:
                print(f"Error accessing pin: {e}")
                continue

        # Search for to_pin
        print(f"Searching for pin {to_pin} on {to_component}...")
        for pin in to_comp.pin:
            try:
                pin_number = str(pin[0]) if pin[0] is not None else ""
                if pin_number == to_pin:
                    to_pin_obj = pin
                    print(f"Found pin {to_pin}!")
                    break
            except (IndexError, TypeError) as e:
                print(f"Error accessing pin: {e}")
                continue

        print(f"Pin search complete. Found pins: {from_pin_obj is not None}, {to_pin_obj is not None}")

        # Check if pins were found
        print("Checking if pins were found...")
        print(f"from_pin_obj type: {type(from_pin_obj)}")
        print(f"to_pin_obj type: {type(to_pin_obj)}")

        if from_pin_obj is None:
            print("from_pin_obj is None, returning error")
            available_pins = [pin["number"] for pin in from_pins_info["pins"]]
            return {
                "error": f"Pin '{from_pin}' not found on component {from_component}",
                "available_pins": available_pins
            }

        if to_pin_obj is None:
            print("to_pin_obj is None, returning error")
            available_pins = [pin["number"] for pin in to_pins_info["pins"]]
            return {
                "error": f"Pin '{to_pin}' not found on component {to_component}",
                "available_pins": available_pins
            }

        print("Both pins found, continuing to wire creation...")

        # Create wire using coordinate-based connection
        print("Getting component positions...")
        from_pos = from_comp.at
        to_pos = to_comp.at
        print(f"Positions: {from_pos} -> {to_pos}")

        try:
            print("Extracting coordinates...")
            from_coords = [float(from_pos[0]), float(from_pos[1])]
            to_coords = [float(to_pos[0]), float(to_pos[1])]
            print(f"Coordinates: {from_coords} -> {to_coords}")
        except Exception as pos_error:
            return {
                "error": f"Could not extract coordinates: {str(pos_error)}",
                "from_position": safe_serialize(from_pos),
                "to_position": safe_serialize(to_pos)
            }

        print("Creating wire...")
        try:
            new_wire = schem.wire.new()
            print("Wire created, setting start position...")
            new_wire.start_at(from_coords)
            print("Start position set, setting end position...")
            new_wire.end_at(to_coords)
            print("Wire configured successfully")
        except Exception as wire_error:
            return {
                "error": f"Wire creation failed: {str(wire_error)}",
                "error_type": type(wire_error).__name__,
                "step": "wire_creation"
            }

        print("Saving schematic...")
        try:
            schem.overwrite()
            print("Save successful!")
        except Exception as save_error:
            return {
                "error": f"Save failed: {str(save_error)}",
                "error_type": type(save_error).__name__,
                "step": "save"
            }

        return {
            "status": "connected",
            "from": f"{from_component}.{from_pin}",
            "to": f"{to_component}.{to_pin}",
            "from_coordinates": from_coords,
            "to_coordinates": to_coords,
            "method": "coordinate_based_wire_fixed"
        }

    except Exception as e:
        return {
            "error": f"Failed to connect pins: {str(e)}",
            "error_type": type(e).__name__
        }

def test_pin_discovery_and_wiring():
    """Test the fixed pin discovery and wiring functionality."""
    print("=== Testing Fixed Pin Discovery ===\n")

    # Load schematic
    schem = skip.Schematic('test_wiring.kicad_sch')

    # Test 1: Resistor pin discovery
    print("Test 1: Resistor Pin Discovery")
    r_scl_comp, _ = find_component_by_reference(schem, 'R_SCL')
    if r_scl_comp:
        r_pins = get_component_pins(r_scl_comp)
        print(f"R_SCL pin count: {r_pins['pin_count']}")
        print(f"R_SCL pins: {[pin['number'] for pin in r_pins['pins']]}")
    else:
        print("R_SCL component not found")

    # Test 2: IC pin discovery
    print("\nTest 2: IC Pin Discovery")
    u1_comp, _ = find_component_by_reference(schem, 'U1')
    if u1_comp:
        u1_pins = get_component_pins(u1_comp)
        print(f"U1 pin count: {u1_pins['pin_count']}")
        print(f"U1 first 5 pins: {[pin['number'] for pin in u1_pins['pins'][:5]]}")
        if u1_pins['pin_count'] > 5:
            print(f"U1 last 5 pins: {[pin['number'] for pin in u1_pins['pins'][-5:]]}")
    else:
        print("U1 component not found")

    # Test 3: Wire connection with resistor
    print("\nTest 3: Wire Connection - Resistor to IC")

    # Create a backup first since we're testing
    import shutil
    shutil.copy2('test_wiring.kicad_sch', 'test_wiring_debug.kicad_sch')

    print("About to call add_wire_connection_fixed...")
    try:
        result1 = add_wire_connection_fixed('test_wiring_debug.kicad_sch', 'R_SCL', '1', 'U1', '2')
        print("Function returned successfully")
        print("Result:", result1)
    except Exception as e:
        print("Exception in add_wire_connection_fixed:", str(e))
        print("Exception type:", type(e).__name__)
        import traceback
        traceback.print_exc()

    # Test 4: Wire connection with invalid pin
    print("\nTest 4: Wire Connection - Invalid Pin")
    result2 = add_wire_connection_fixed('test_wiring.kicad_sch', 'R_SCL', '99', 'U1', '1')
    print("Result:", result2)

    # Summary
    print("\n=== Summary ===")
    success_count = sum(1 for r in [result1, result2] if r.get("status") == "connected")
    print(f"Successful connections: {success_count}/2")

    # Check final schematic state
    final_schem = skip.Schematic('test_wiring.kicad_sch')
    print(f"Total wires in schematic: {len(final_schem.wire)}")

if __name__ == "__main__":
    test_pin_discovery_and_wiring()