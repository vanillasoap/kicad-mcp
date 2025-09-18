#!/usr/bin/env python3
"""
Test the current pin discovery functionality
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

def get_component_pins_current(component):
    """Current MCP version of get_component_pins."""
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
    """Find component by reference."""
    component = getattr(schem.symbol, component_reference, None)
    available_refs = [attr for attr in dir(schem.symbol) if not attr.startswith('_')]
    return component, available_refs

def test_current_pin_discovery():
    """Test the current pin discovery with various components."""
    print("=== Testing Current MCP Pin Discovery Function ===\n")

    schem = skip.Schematic('test_wiring.kicad_sch')

    components_to_test = ['R_SCL', 'R_PDN', 'U1']

    for comp_name in components_to_test:
        print(f"Testing {comp_name}:")
        comp, available_refs = find_component_by_reference(schem, comp_name)

        if comp:
            pins_result = get_component_pins_current(comp)
            print(f"  Pin count: {pins_result['pin_count']}")
            print(f"  Pins:")

            for pin in pins_result['pins']:
                uuid_short = pin['uuid'][:30] + '...' if len(pin['uuid']) > 30 else pin['uuid']
                print(f"    Pin '{pin['number']}' (UUID: {uuid_short})")
        else:
            print(f"  Component not found. Available: {available_refs}")
        print()

    # Also test direct pin access to compare
    print("=== Direct Pin Access Comparison ===")
    r_comp, _ = find_component_by_reference(schem, 'R_SCL')
    if r_comp:
        print("R_SCL direct pin access:")
        for i, pin in enumerate(r_comp.pin):
            try:
                direct_number = pin[0]
                print(f"  Direct access pin[{i}][0] = '{direct_number}' (type: {type(direct_number)})")
            except Exception as e:
                print(f"  Direct access pin[{i}] failed: {e}")

if __name__ == "__main__":
    test_current_pin_discovery()